import logging
import re
from typing import List, Optional, Dict, Any, Set

from backend.models.models import EnhancedModule, Submodule, LearningPathState
from backend.services.image_service import search_wikimedia_images
from backend.services.services import get_llm_for_evaluation
from backend.core.graph_nodes.helpers import run_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger("content_enrichment.images")


def _split_into_sections(markdown_text: str) -> List[str]:
    parts = re.split(r"(\n##[^\n]*\n|\n###[^\n]*\n)", markdown_text)
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
    return re.sub(r'^#+\s*', '', heading_token.strip())


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


def _insert_image_markdown(image_url: str, file_page_url: str, alt_text: str) -> str:
    attribution = f"Fuente: [Wikimedia Commons]({file_page_url})"
    return f"\n\n![{alt_text}]({image_url})\n{attribution}\n\n"


async def _find_relevant_image_for_anchor(
    state: LearningPathState,
    module: EnhancedModule,
    submodule: Submodule,
    section_heading: Optional[str],
    exclude_urls: Optional[Set[str]] = None,
) -> Optional[Dict[str, Any]]:
    # Generate multiple short queries
    queries = await _generate_wikimedia_queries(state, module, submodule, section_heading)
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
    # Ask LLM to pick the best (or none)
    sel = await _rank_images_with_llm(state, module, submodule, section_heading, all_candidates, max_select=1)
    if not sel:
        return None
    return all_candidates[sel[0]]


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
        max_images = int(state.get("images_per_submodule", 2) or 0)
        if max_images <= 0:
            return content_markdown

        sections = _split_into_sections(content_markdown)
        used_urls: Set[str] = set()
        if len(sections) <= 1:
            img = await _find_relevant_image_for_anchor(state, module, submodule, None, exclude_urls=used_urls)
            if img:
                if img["url"] not in used_urls:
                    used_urls.add(img["url"])
                    insertion = _insert_image_markdown(img["url"], img["file_page_url"], submodule.title)
                    return re.sub(r"\n\n", f"\n\n{insertion}", content_markdown, count=1)
            return content_markdown

        images_inserted = 0
        out_parts: List[str] = []
        i = 0
        while i < len(sections) and images_inserted < max_images:
            part = sections[i]
            out_parts.append(part)
            if i + 1 < len(sections):
                heading = sections[i + 1]
                out_parts.append(heading)
                heading_text = _extract_heading_text(heading)
                img = await _find_relevant_image_for_anchor(state, module, submodule, heading_text, exclude_urls=used_urls)
                if img and img.get("url") not in used_urls:
                    alt_text = f"{submodule.title} – {heading_text}" if heading_text else submodule.title
                    out_parts.append(_insert_image_markdown(img["url"], img["file_page_url"], alt_text))
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
