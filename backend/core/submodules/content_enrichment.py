import logging
import re
from typing import List, Optional, Dict, Any, Set, Tuple

from backend.models.models import EnhancedModule, Submodule, LearningPathState
from backend.services.image_service import search_wikimedia_images
from backend.services.services import get_llm_for_evaluation
from backend.core.graph_nodes.helpers import run_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger("content_enrichment.images")


def _split_into_sections(markdown_text: str) -> List[str]:
    # Split on H2/H3 markdown headings or standalone bold-line headings (**...**)
    parts = re.split(r"(\n##[^\n]*\n|\n###[^\n]*\n|\n\*\*[^\n]+\*\*\n)", markdown_text)
    combined: List[str] = []
    i = 0
    while i < len(parts):
        segment = parts[i]
        if (i + 1 < len(parts)) and (parts[i + 1].startswith("\n##") or parts[i + 1].startswith("\n###")):
            combined.append(segment)
            combined.append(parts[i + 1])
            i += 2
        else:
            combined.append(segment)
            i += 1
    return combined


def _extract_heading_text(heading_token: str) -> str:
    token = heading_token.strip()
    if token.startswith("##"):
        return re.sub(r'^#+\s*', '', token)
    # Handle standalone bold heading lines: **Heading**
    m = re.match(r'^\*\*([^\n*]+)\*\*$', token)
    if m:
        return m.group(1).strip()
    return token


def _determine_query_language(state: LearningPathState, text_pool: List[str]) -> str:
    joined = " ".join([t for t in text_pool if t])
    lower = joined.lower()
    country_to_lang = {
        "españa": "es", "méxico": "es", "mexico": "es", "argentina": "es", "colombia": "es",
        "chile": "es", "perú": "es", "peru": "es", "uruguay": "es", "ecuador": "es",
        "france": "fr", "paris": "fr", "québec": "fr", "quebec": "fr",
        "germany": "de", "deutschland": "de", "berlin": "de",
        "italy": "it", "italia": "it", "roma": "it",
        "portugal": "pt", "brasil": "pt", "brazil": "pt",
    }
    for key, lang in country_to_lang.items():
        if key in lower:
            return lang
    return "en"


async def _generate_wikimedia_queries(
    state: LearningPathState,
    module: EnhancedModule,
    submodule: Submodule,
    section_heading: Optional[str],
    context_hint: Optional[str] = None,
) -> List[str]:
    """Use LLM to produce 3 short, image-friendly queries (2–4 words)."""
    try:
        language_for_queries = _determine_query_language(
            state,
            [state.get("user_topic", ""), module.title, submodule.title, section_heading or ""]
        )

        prompt_text = """
You generate concise Wikimedia Commons image search terms.
Produce 3 lines, each ONE query. 2–4 words, no quotes, no punctuation.
Guidelines:
- Prefer concrete, visual subjects (people, places, institutions, events, objects, scenes)
- Avoid abstract phrases like "economic policy changes" or generic words like "context"
- Avoid years unless iconic (e.g., "Reagan 1981 inauguration")
- Use {query_language} unless the concept is an English-only term
- Keep it broad enough to likely have photos on Wikimedia
Context:
- Course topic: {user_topic}
- Module: {module_title}
- Submodule: {submodule_title}
- Section: {section_heading}
 - Image topic hint: {context_hint}
"""
        prompt = ChatPromptTemplate.from_template(prompt_text)
        llm_getter = lambda: get_llm_for_evaluation(state.get("google_key_provider"), user=state.get("user"))
        output = await run_chain(
            prompt,
            llm_getter,
            StrOutputParser(),
            {
                "query_language": language_for_queries,
                "user_topic": state.get("user_topic", ""),
                "module_title": module.title,
                "submodule_title": submodule.title,
                "section_heading": section_heading or "",
                "context_hint": context_hint or "",
            },
            max_retries=2,
            initial_retry_delay=0.5,
        )
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        cleaned: List[str] = []
        for line in lines:
            words = re.findall(r"[\w\-]+", line)
            if not words:
                continue
            trimmed = " ".join(words[:4])
            # Filter out too-abstract tokens
            if trimmed.lower() in {"context", "history", "economy"}:
                continue
            if trimmed.lower() not in [c.lower() for c in cleaned]:
                cleaned.append(trimmed)
            if len(cleaned) >= 3:
                break
        if not cleaned:
            # Fallback: extract concrete tokens from titles
            def pick_terms(text: str) -> Optional[str]:
                tokens = re.findall(r"[A-Za-zÀ-ÿ0-9\-]+", text or "")
                if not tokens:
                    return None
                return " ".join(tokens[:3])
            for t in [section_heading, submodule.title, module.title]:
                term = pick_terms(t or "")
                if term and term.lower() not in [c.lower() for c in cleaned]:
                    cleaned.append(term)
                if len(cleaned) >= 2:
                    break
        return cleaned[:3]
    except Exception as e:
        logger.debug(f"LLM query generation failed, using simple fallback: {e}")
        base: List[str] = []
        for text in [submodule.title, section_heading or "", module.title]:
            if text:
                words = re.findall(r"[\w\-]+", text)
                if words:
                    base.append(" ".join(words[:3]))
        return [q for q in base if q][:2]


async def _rank_images_with_llm(
    state: LearningPathState,
    module: EnhancedModule,
    submodule: Submodule,
    section_heading: Optional[str],
    candidates: List[Dict[str, Any]],
    max_select: int = 1,
) -> List[int]:
    """Ask LLM to select up to max_select relevant image indices from candidates, or none."""
    if not candidates:
        return []
    try:
        # Prepare compact list to fit prompt budget
        compact = []
        for idx, c in enumerate(candidates[:10]):
            compact.append({
                "idx": idx,
                "title": c.get("title", "")[:120],
                "url": c.get("url", ""),
                "page": c.get("file_page_url", ""),
                "w": c.get("width", 0),
                "h": c.get("height", 0),
                "mime": c.get("mime", ""),
            })

        prompt_text = """
You are selecting relevant Wikimedia images for a submodule.
Return a JSON array of selected indices from the candidate list (e.g., [0] or [] or [1,2]), maximum {max_sel}.
Selection rules:
- Only select if clearly relevant to the submodule topic/section; otherwise return []
- Prefer photos illustrating concrete entities/events/institutions related to the topic
- Avoid generic cityscapes, random buildings, unrelated portraits
- Prefer landscape orientation and width>=600 when possible
Context:
- Module: {module_title}
- Submodule: {submodule_title}
- Section: {section_heading}
Candidates (JSON):
{candidates_json}
"""
        from json import dumps
        prompt = ChatPromptTemplate.from_template(prompt_text)
        llm_getter = lambda: get_llm_for_evaluation(state.get("google_key_provider"), user=state.get("user"))
        output = await run_chain(
            prompt,
            llm_getter,
            StrOutputParser(),
            {
                "max_sel": max_select,
                "module_title": module.title,
                "submodule_title": submodule.title,
                "section_heading": section_heading or "",
                "candidates_json": dumps(compact, ensure_ascii=False),
            },
            max_retries=1,
            initial_retry_delay=0.5,
        )
        # Parse array of ints
        nums = re.findall(r"\d+", output)
        indices = [int(n) for n in nums][:max_select]
        # Keep only valid
        return [i for i in indices if 0 <= i < len(compact)]
    except Exception as e:
        logger.debug(f"LLM image ranking failed: {e}")
        return []


def _insert_image_markdown(image_url: str, file_page_url: str, alt_text: str, caption: Optional[str] = None) -> str:
    attribution = f"Fuente: [Wikimedia Commons]({file_page_url})"
    if caption and caption.strip():
        # Use italic caption line for readability
        return f"\n\n![{alt_text}]({image_url})\n_{caption.strip()}_\n{attribution}\n\n"
    return f"\n\n![{alt_text}]({image_url})\n{attribution}\n\n"


async def _select_image_and_caption_with_llm(
    state: LearningPathState,
    module: EnhancedModule,
    submodule: Submodule,
    section_heading: Optional[str],
    candidates: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Ask LLM to pick the best image and draft a short caption explaining relevance.

    Returns a dict: {"index": int, "caption": str} or None.
    """
    if not candidates:
        return None
    try:
        compact = []
        for idx, c in enumerate(candidates[:10]):
            compact.append({
                "idx": idx,
                "title": c.get("title", "")[:160],
                "page": c.get("file_page_url", ""),
                "url": c.get("url", ""),
                "w": c.get("width", 0),
                "h": c.get("height", 0),
                "mime": c.get("mime", ""),
            })
        from json import dumps
        prompt_text = """
You select ONE Wikimedia image and write a helpful caption.
Output strict JSON: {{"index": <number>, "caption": "<short caption>"}}
Selection rules:
- Only pick if clearly relevant to the submodule topic/section; else return an empty JSON object
- Prefer photos that concretely illustrate the topic; favor width>=600 and landscape when possible
Caption guidelines:
- Language: {caption_lang}
- 1 sentence, 12–28 words. Describe what the image shows and why it is relevant to the section.
- Do not invent facts beyond title/obvious content. Be neutral and concise.
Context:
- Module: {module_title}
- Submodule: {submodule_title}
- Section: {section_heading}
Candidates (JSON):
{candidates_json}
"""
        prompt = ChatPromptTemplate.from_template(prompt_text)
        llm_getter = lambda: get_llm_for_evaluation(state.get("google_key_provider"), user=state.get("user"))
        raw = await run_chain(
            prompt,
            llm_getter,
            StrOutputParser(),
            {
                "caption_lang": state.get("language", "es"),
                "module_title": module.title,
                "submodule_title": submodule.title,
                "section_heading": section_heading or "",
                "candidates_json": dumps(compact, ensure_ascii=False),
            },
            max_retries=1,
            initial_retry_delay=0.5,
        )
        # Extract minimal JSON
        import json
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        data = json.loads(raw[start:end+1])
        if not isinstance(data, dict):
            return None
        if "index" not in data:
            return None
        idx = int(data.get("index"))
        caption = str(data.get("caption", "")).strip()
        if idx < 0 or idx >= len(compact):
            return None
        return {"index": idx, "caption": caption}
    except Exception as _e:
        return None


async def _find_relevant_image_for_anchor(
    state: LearningPathState,
    module: EnhancedModule,
    submodule: Submodule,
    section_heading: Optional[str],
    exclude_urls: Optional[Set[str]] = None,
    topic_hint: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    # Generate multiple short queries
    queries = await _generate_wikimedia_queries(state, module, submodule, section_heading, context_hint=topic_hint)
    # Fetch candidates per query and aggregate
    language = state.get("language", "en")
    all_candidates: List[Dict[str, Any]] = []
    seen_urls = set()
    for q in queries:
        results = await search_wikimedia_images(q, count=5, language=language, timeout_seconds=3.0)
        for r in results:
            url = r.get("url")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            all_candidates.append(r)
    # Exclude URLs already used if provided
    if exclude_urls:
        all_candidates = [c for c in all_candidates if c.get("url") not in exclude_urls]

    if not all_candidates:
        return None
    # Ask LLM to pick best and produce a caption
    selection = await _select_image_and_caption_with_llm(state, module, submodule, section_heading, all_candidates)
    if selection is None:
        return None
    idx = selection["index"]
    chosen = all_candidates[idx]
    chosen["caption"] = selection.get("caption")
    return chosen


def _collect_heading_texts(markdown_text: str) -> List[str]:
    headings_h = re.findall(r"^##\s+([^\n]+)$|^###\s+([^\n]+)$", markdown_text, flags=re.MULTILINE)
    bold_headings = re.findall(r"^\*\*([^\n*]+)\*\*$", markdown_text, flags=re.MULTILINE)
    result: List[str] = []
    for h2, h3 in headings_h:
        if h2:
            result.append(h2.strip())
        elif h3:
            result.append(h3.strip())
    for b in bold_headings:
        text = b.strip()
        if text and text not in result:
            result.append(text)
    return result


async def _plan_image_anchors(
    state: LearningPathState,
    module: EnhancedModule,
    submodule: Submodule,
    content_markdown: str,
    max_images: int,
) -> List[Dict[str, str]]:
    """Ask LLM to propose up to max_images anchors with hints.
    Returns list of dicts with keys: type (intro|heading), heading (optional), hint (short query hint).
    """
    try:
        headings = _collect_heading_texts(content_markdown)
        prompt_text = """
Plan up to {max_images} image insertion anchors for the submodule below.
Rules:
- Only choose anchors that clearly benefit from a contextual, illustrative image.
- Prefer placing after H2/H3 headings; optionally include a single 'intro' image near the start.
- Ensure each selected anchor is unique and relevant; choose fewer than {max_images} if needed.
- For each anchor, provide a short 2–4 word topic hint suitable for finding a Wikimedia photo.
Output strict JSON array, items like:
  {{"type":"heading", "heading":"<exact heading text>", "hint":"<2-4 words>"}}
  or {{"type":"intro", "hint":"<2-4 words>"}}
Context:
- Module: {module_title}
- Submodule: {submodule_title}
- Headings: {headings}
 - Full content:
 {content_full}
"""
        prompt = ChatPromptTemplate.from_template(prompt_text)
        llm_getter = lambda: get_llm_for_evaluation(state.get("google_key_provider"), user=state.get("user"))
        raw = await run_chain(
            prompt,
            llm_getter,
            StrOutputParser(),
            {
                "max_images": max_images,
                "module_title": module.title,
                "submodule_title": submodule.title,
                "headings": ", ".join(headings) if headings else "(none)",
                "content_full": content_markdown,
            },
            max_retries=2,
            initial_retry_delay=0.5,
        )
        # Attempt to extract JSON array
        import json
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1 and end > start:
            raw_json = raw[start:end+1]
            data = json.loads(raw_json)
            anchors: List[Dict[str, str]] = []
            seen: Set[Tuple[str, str]] = set()
            for item in data:
                if not isinstance(item, dict):
                    continue
                a_type = str(item.get("type", "")).strip().lower()
                if a_type not in {"intro", "heading"}:
                    continue
                hint = str(item.get("hint", "")).strip()
                if not hint:
                    continue
                heading_text = ""
                if a_type == "heading":
                    heading_text = str(item.get("heading", "")).strip()
                    if not heading_text:
                        continue
                key = (a_type, heading_text.lower())
                if key in seen:
                    continue
                seen.add(key)
                anchors.append({"type": a_type, "heading": heading_text, "hint": hint})
                if len(anchors) >= max_images:
                    break
            return anchors
        return []
    except Exception as _e:
        return []


async def enrich_content_with_images(
    state: LearningPathState,
    module: EnhancedModule,
    submodule: Submodule,
    content_markdown: str,
) -> str:
    try:
        if not content_markdown or not content_markdown.strip():
            return content_markdown
        if not state.get("images_enrichment_enabled", True):
            return content_markdown
        max_images = int(state.get("images_per_submodule", 5) or 0)
        if max_images <= 0:
            return content_markdown

        sections = _split_into_sections(content_markdown)
        used_urls: Set[str] = set()
        # Plan anchors with LLM
        anchors = await _plan_image_anchors(state, module, submodule, content_markdown, max_images)

        # Fallback: if no anchors proposed, keep previous heuristic (single or per-heading)
        if not anchors:
            anchors = []
            if len(sections) <= 1:
                anchors.append({"type": "intro", "heading": "", "hint": submodule.title})
            else:
                # Propose anchors for first few headings without LLM
                for i in range(1, len(sections), 2):
                    heading_text = _extract_heading_text(sections[i])
                    anchors.append({"type": "heading", "heading": heading_text, "hint": heading_text})
                    if len(anchors) >= max_images:
                        break

        # If no headings and single section
        if len(sections) <= 1:
            # For single-section content, insert at most one image after the first paragraph
            out = content_markdown
            chosen_anchor = None
            # Prefer an intro-type anchor; fall back to first available
            for a in anchors:
                if a.get("type") == "intro":
                    chosen_anchor = a
                    break
            if not chosen_anchor and anchors:
                chosen_anchor = anchors[0]
            if chosen_anchor:
                hint = chosen_anchor.get("hint") or submodule.title
                img = await _find_relevant_image_for_anchor(state, module, submodule, None, exclude_urls=used_urls, topic_hint=hint)
                if img and img["url"] not in used_urls:
                    used_urls.add(img["url"])
                    insertion = _insert_image_markdown(img["url"], img["file_page_url"], submodule.title, caption=img.get("caption"))
                    # Insert after first paragraph boundary if present
                    parts = re.split(r"(\n\n)", out, maxsplit=1)
                    if len(parts) == 3:
                        out = parts[0] + parts[1] + insertion + parts[2]
                    else:
                        out = out + insertion
            return out

        images_inserted = 0
        out_parts: List[str] = []
        # Index anchors by heading for quick lookup
        anchors_by_heading: Dict[str, Dict[str, str]] = {
            (a.get("heading") or "").strip(): a for a in anchors if a.get("type") == "heading" and a.get("heading")
        }
        intro_anchors = [a for a in anchors if a.get("type") == "intro"]
        # Optionally handle one intro image before first heading
        preface_inserted = False
        i = 0
        while i < len(sections) and images_inserted < max_images:
            part = sections[i]
            out_parts.append(part)
            # After initial content before first heading, consider intro image
            if i == 0 and intro_anchors and not preface_inserted:
                hint = intro_anchors[0].get("hint") or submodule.title
                img = await _find_relevant_image_for_anchor(state, module, submodule, None, exclude_urls=used_urls, topic_hint=hint)
                if img and img.get("url") not in used_urls and images_inserted < max_images:
                    out_parts.append(_insert_image_markdown(img["url"], img["file_page_url"], submodule.title, caption=img.get("caption")))
                    used_urls.add(img["url"])
                    images_inserted += 1
                    preface_inserted = True
            if i + 1 < len(sections):
                heading = sections[i + 1]
                out_parts.append(heading)
                heading_text = _extract_heading_text(heading)
                # If an anchor was planned for this heading, use its hint; otherwise skip
                planned = anchors_by_heading.get(heading_text)
                if planned and images_inserted < max_images:
                    img = await _find_relevant_image_for_anchor(
                        state,
                        module,
                        submodule,
                        heading_text,
                        exclude_urls=used_urls,
                        topic_hint=(planned.get("hint") or heading_text),
                    )
                else:
                    img = None
                if img and img.get("url") not in used_urls and images_inserted < max_images:
                    alt_text = f"{submodule.title} – {heading_text}" if heading_text else submodule.title
                    out_parts.append(_insert_image_markdown(img["url"], img["file_page_url"], alt_text, caption=img.get("caption")))
                    used_urls.add(img["url"])
                    images_inserted += 1
                i += 2
            else:
                i += 1
        while i < len(sections):
            out_parts.append(sections[i])
            i += 1
        return "".join(out_parts)

    except Exception as e:
        logger.debug(f"Image enrichment failed, skipping: {e}")
        return content_markdown
