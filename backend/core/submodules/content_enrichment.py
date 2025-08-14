import logging
import re
from typing import List, Optional, Dict, Any, Set, Tuple
from dataclasses import dataclass

from backend.models.models import EnhancedModule, Submodule, LearningPathState
from backend.services.image_service import search_wikimedia_images
from backend.services.services import get_llm_for_evaluation
from backend.core.graph_nodes.helpers import run_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger("content_enrichment.images")

# --- Data structures for retry logic ---

@dataclass
class AttemptState:
    """State tracking for multi-attempt image search process."""
    attempt_number: int
    used_urls: Set[str]
    all_candidates_history: List[Dict[str, Any]]
    query_history: List[List[str]]
    previous_rejection_reasons: List[str]

# --- Module-level prompt templates (verbatim) ---
PROMPT_WIKIMEDIA_QUERIES = """
You generate concise Wikimedia Commons image search terms that maximize success probability.
Produce 3 lines, each ONE query. 2–4 words, no quotes, no punctuation.

**EVIDENCE-BASED SUCCESS STRATEGIES:**

**LANGUAGE OPTIMIZATION (Critical for success):**
- SCIENTIFIC/MATHEMATICAL topics: ALWAYS use English (Wikimedia Commons is primarily English)
  - Mathematics: "Stokes theorem", "differential topology", "vector calculus"
  - Science: "quantum mechanics", "DNA structure", "photosynthesis"
  - NOT: "Teoremas de Stokes", "topología diferencial" (these fail)
- BIOGRAPHICAL content: Use full English names
  - "Theodor Adorno portrait", "Jacques Derrida biography", "Einstein relativity"
  - NOT: "Adorno filósofo", "Derrida pensador"
- OTHER topics: Use {query_language} if culturally specific, otherwise prefer English

**PROVEN SUCCESSFUL PATTERNS:**
1. **Scientific Models/Theories**: "[Scientist Name] [concept]" or "[concept] diagram"
   - SUCCESS: "Baddeley Hitch model" → Found perfect diagram
   - SUCCESS: "Stokes theorem illustration" → Found mathematical content
2. **Biographical**: "[Full Name] portrait" or "[Full Name] biography"
   - SUCCESS: "Theodor Adorno portrait" → Found biographical photo
   - SUCCESS: "Jacques Derrida portrait" → Found biographical content
3. **Technical Diagrams**: "[concept] diagram", "[model] illustration", "[theory] visualization"

**CONTENT-TYPE DETECTION & STRATEGY:**
- If topic contains: mathematics, theorem, equation, formula, calculus, topology, geometry → Use English scientific terms
- If topic contains: model, theory, concept, diagram, process → Target diagrams + key figures
- If topic contains: person names, philosophers, scientists, authors → Biographical approach
- If topic contains: historical events, periods, movements → Geographic + temporal approach

**OPTIMIZATION RULES:**
- Prefer concrete, visual subjects (people, places, institutions, diagrams, objects)
- Scientific terms: Use universally recognized English terminology
- Avoid abstract phrases or overly specific technical jargon
- Target content likely to exist on Wikimedia Commons
- Balance between: 1) Key figures/biography, 2) Conceptual diagrams, 3) Related institutions

Context:
- Course topic: {user_topic}
- Module: {module_title}
- Submodule: {submodule_title}
- Section: {section_heading}
- Image topic hint: {context_hint}
"""

PROMPT_IMAGE_RANKING = """
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

PROMPT_IMAGE_SELECTION_WITH_CAPTION = """
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

PROMPT_IMAGE_SELECTION_WITH_ALTERNATIVES = """
You evaluate Wikimedia images for a submodule and either select one OR suggest alternative search queries with HIGH SUCCESS PROBABILITY.

**ATTEMPT STRATEGY**: This is attempt {attempt_number} of {max_attempts}. {attempt_context}

Output strict JSON in ONE of these formats:
1. If you find a relevant image: {{"index": <number>, "caption": "<short caption>"}}
2. If NO images are relevant AND we haven't reached max attempts: {{"alternative_queries": ["query1", "query2", "query3"], "reason": "<brief explanation why current images aren't suitable>"}}
3. If NO images are relevant AND we've reached max attempts: {{}}

**CRITICAL LANGUAGE CONSISTENCY RULE:**
- MAINTAIN THE SAME LANGUAGE STRATEGY across all attempts for this topic
- For SCIENTIFIC/MATHEMATICAL topics: ALWAYS use English terms in alternative queries
  - Mathematics: "Stokes theorem", "differential topology", "manifold geometry"
  - Science: "quantum mechanics", "DNA structure", "working memory model"
  - Computer Science: "NP complete", "algorithm complexity", "Cook Levin theorem"
- For BIOGRAPHICAL topics: ALWAYS use English names: "Vladimir Propp portrait", "Einstein biography"
- For OTHER topics: Use English for better Wikimedia results unless culturally specific

**EVIDENCE-BASED QUERY PATTERNS (Use these proven successful patterns):**
1. **Simple Biographical**: "[Full Name] portrait" or "[Full Name] biography"
   - PROVEN SUCCESS: "Vladimir Propp portrait", "Theodor Adorno portrait"
   - AVOID: Complex queries like "Vladimir Propp functions" (these fail)
2. **Scientific Diagrams**: "[concept] diagram" or "[theory] illustration"
   - PROVEN SUCCESS: "Baddeley Hitch model", "Stokes theorem illustration"
3. **Technical Terms**: Use universally recognized English scientific terminology
   - PROVEN SUCCESS: "NP complete diagram", "differential topology"

**FLEXIBLE IMAGE SELECTION RULES:**
- PRIORITIZE CONTENT RELEVANCE over format preferences
- For conceptual topics: Diagrams, illustrations, and visualizations are EXCELLENT choices
- For biographical topics: Photos of people are ideal
- For scientific topics: ANY related diagram, even if abstract, is valuable
- FINAL ATTEMPT RULE: If this is attempt 3/3, be EXTREMELY lenient - select anything with ANY connection to topic

**CURRENT ATTEMPT GUIDANCE:**
{attempt_specific_guidance}

**REJECTION LEARNING - AVOID FAILED PATTERNS:**
Previous unsuccessful queries: {previous_queries}
{rejection_history}

**ALTERNATIVE QUERY GENERATION (when current images insufficient):**
- **PRIORITY 1**: Simple biographical queries: "[Key Figure] portrait", "[Scientist] biography"
- **PRIORITY 2**: Basic concept diagrams: "[theory] diagram", "[model] illustration"
- **PRIORITY 3**: Institution + topic: "[University] [subject]", "[Place] [concept]"
- **LANGUAGE RULE**: Keep same language strategy as initial queries (usually English for academic topics)
- **SIMPLICITY RULE**: Prefer simple 2-3 word queries over complex phrases

**Caption guidelines (if selecting):**
- Language: {caption_lang}  
- 1 sentence, 12–28 words. Describe what the image shows and why it is relevant to the section.
- Do not invent facts beyond title/obvious content. Be neutral and concise.

**Context:**
- Module: {module_title}
- Submodule: {submodule_title}
- Section: {section_heading}

**Candidates (JSON):**
{candidates_json}
"""

PROMPT_PLAN_IMAGE_ANCHORS = """
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

# --- Text parsing helpers ---

def _split_into_sections(markdown_text: str) -> List[str]:
    """Split markdown into alternating content and heading tokens.

    Splits on H2/H3 markdown headings or standalone bold-line headings (**...**),
    preserving separators so that insertion points can be located precisely.
    """
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
    """Extract clean heading text from a heading token.

    Supports '##' or '###' markdown headings and standalone bold headings (**Heading**).
    If no known pattern matches, returns the token as-is (stripped).
    """
    token = heading_token.strip()
    if token.startswith("##"):
        return re.sub(r'^#+\s*', '', token)
    # Handle standalone bold heading lines: **Heading**
    m = re.match(r'^\*\*([^\n*]+)\*\*$', token)
    if m:
        return m.group(1).strip()
    return token


def _collect_heading_texts(markdown_text: str) -> List[str]:
    """Collect H2/H3 and bold-line headings as plain texts in encountered order."""
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


# --- Language heuristics ---

def _determine_query_language(state: LearningPathState, text_pool: List[str]) -> str:
    """Heuristically choose a language code based on country keywords in provided texts.

    Returns 'en' if no match is found.
    """
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


# --- Wikimedia integration and LLM helpers ---

async def _generate_wikimedia_queries(
    state: LearningPathState,
    module: EnhancedModule,
    submodule: Submodule,
    section_heading: Optional[str],
    context_hint: Optional[str] = None,
) -> List[str]:
    """Use LLM to produce up to 3 short, image-friendly queries (2–4 words)."""
    try:
        language_for_queries = _determine_query_language(
            state,
            [state.get("user_topic", ""), module.title, submodule.title, section_heading or ""]
        )

        prompt = ChatPromptTemplate.from_template(PROMPT_WIKIMEDIA_QUERIES)
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


async def _generate_alternative_queries(
    state: LearningPathState,
    module: EnhancedModule,
    submodule: Submodule,
    section_heading: Optional[str],
    context_hint: Optional[str],
    suggested_queries: List[str],
    attempt_state: AttemptState,
) -> List[str]:
    """Generate alternative queries combining LLM suggestions with enhanced fallback logic.
    
    Returns a list of new queries to try, avoiding previous queries and duplicates.
    """
    language_for_queries = _determine_query_language(
        state,
        [state.get("user_topic", ""), module.title, submodule.title, section_heading or ""]
    )
    
    # Start with LLM suggested queries - enhanced cleaning and validation
    alternative_queries = []
    if suggested_queries:
        for q in suggested_queries:
            if isinstance(q, str) and q.strip():
                # Enhanced cleaning - extract words and validate for visual potential
                words = re.findall(r"[\w\-]+", q.strip())
                if words:
                    cleaned = " ".join(words[:4])  # Limit to 4 words
                    
                    # Enhanced validation - prioritize queries with high visual potential
                    visual_score = 0
                    cleaned_lower = cleaned.lower()
                    
                    # Boost score for visual content indicators
                    visual_indicators = ["portrait", "photo", "image", "building", "statue", "monument", "university", "museum", "palace", "church", "square", "street", "city", "country"]
                    biographical_indicators = ["biography", "life", "born", "death", "president", "minister", "scientist", "artist", "writer", "inventor"]
                    geographic_indicators = ["america", "europe", "germany", "france", "london", "paris", "new york", "washington", "moscow", "beijing"]
                    
                    for indicator in visual_indicators:
                        if indicator in cleaned_lower:
                            visual_score += 3
                    for indicator in biographical_indicators:
                        if indicator in cleaned_lower:
                            visual_score += 2
                    for indicator in geographic_indicators:
                        if indicator in cleaned_lower:
                            visual_score += 2
                    
                    # Penalize abstract terms that are less likely to have images
                    abstract_penalties = ["theory", "concept", "idea", "principle", "methodology", "framework", "paradigm", "philosophy", "ideology"]
                    for penalty in abstract_penalties:
                        if penalty in cleaned_lower:
                            visual_score -= 1
                    
                    # Only include queries with positive visual potential or if we have few alternatives
                    if visual_score > 0 or len(alternative_queries) < 1:
                        if cleaned and cleaned not in [existing.lower() for existing in alternative_queries]:
                            alternative_queries.append(cleaned)
    
    # Get all previously used queries (flattened)
    used_queries_lower = set()
    for queries in attempt_state.query_history:
        for q in queries:
            used_queries_lower.add(q.lower())
    
    # Filter out previously used queries
    alternative_queries = [q for q in alternative_queries if q.lower() not in used_queries_lower]
    
    # If we don't have enough alternatives, generate additional fallback queries
    if len(alternative_queries) < 2:
        fallback_queries = await _generate_fallback_alternative_queries(
            state, module, submodule, section_heading, context_hint, attempt_state, language_for_queries
        )
        
        for q in fallback_queries:
            if q.lower() not in used_queries_lower and q not in alternative_queries:
                alternative_queries.append(q)
                if len(alternative_queries) >= 3:
                    break
    
    # Final deduplication and validation
    final_queries = []
    for q in alternative_queries:
        if q and len(q) >= 2 and q not in final_queries:
            final_queries.append(q)
        if len(final_queries) >= 3:
            break
    
    logger.debug(f"Generated {len(final_queries)} alternative queries for attempt {attempt_state.attempt_number}")
    return final_queries


async def _generate_fallback_alternative_queries(
    state: LearningPathState,
    module: EnhancedModule,
    submodule: Submodule,
    section_heading: Optional[str],
    context_hint: Optional[str],
    attempt_state: AttemptState,
    language_for_queries: str,
) -> List[str]:
    """Generate fallback alternative queries using enhanced success-oriented strategies."""
    
    fallback_queries = []
    
    # Enhanced Strategy 1: Visual-first approach - Target people, places, institutions
    topic_words = re.findall(r"[\w\-]+", state.get("user_topic", ""))
    module_words = re.findall(r"[\w\-]+", module.title)
    submodule_words = re.findall(r"[\w\-]+", submodule.title)
    
    # Progressive specificity based on attempt number
    if attempt_state.attempt_number == 1:
        # Attempt 1: Broad but concrete - focus on main concepts with visual potential
        if module_words and submodule_words:
            # Combine for concrete visual concepts
            visual_query = " ".join((module_words[:2] + submodule_words[:2]))
            if visual_query:
                fallback_queries.append(visual_query)
    
    elif attempt_state.attempt_number == 2:
        # Attempt 2: Add specificity - geographic, institutional, biographical angles
        
        # Geographic strategy: Look for country/region references
        geographic_terms = []
        all_words = topic_words + module_words + submodule_words
        for word in all_words:
            if word.lower() in ["america", "europe", "asia", "africa", "germany", "france", "britain", "russia", "china", "japan", "spain", "italy", "united", "states", "kingdom"]:
                geographic_terms.append(word)
        
        if geographic_terms:
            geo_query = " ".join(geographic_terms[:2] + submodule_words[:2])
            if geo_query:
                fallback_queries.append(geo_query)
        
        # Institutional strategy: Add university, government, organization terms
        if any(word.lower() in ["science", "research", "study", "theory", "development"] for word in all_words):
            institutional_query = " ".join(submodule_words[:2] + ["university", "research"])
            fallback_queries.append(institutional_query)
    
    else:
        # Attempt 3: Maximum specificity - historical periods, famous figures
        
        # Historical period strategy
        historical_periods = ["1900s", "1920s", "1930s", "1940s", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s"]
        period_query = " ".join(submodule_words[:2] + ["20th", "century"])
        fallback_queries.append(period_query)
        
        # Famous figures strategy - add common surname patterns
        if submodule_words:
            biographical_query = " ".join(submodule_words[:2] + ["biography", "portrait"])
            fallback_queries.append(biographical_query)
    
    # Enhanced Strategy 2: Context-aware section targeting
    if section_heading:
        section_words = re.findall(r"[\w\-]+", section_heading)
        
        # Focus on concrete elements from section heading
        concrete_section_words = [w for w in section_words if len(w) > 3 and w.lower() not in 
                                {"theory", "concept", "analysis", "overview", "introduction", "conclusion", "summary"}]
        
        if concrete_section_words:
            specific_query = " ".join(concrete_section_words[:3])
            if specific_query:
                fallback_queries.append(specific_query)
    
    # Enhanced Strategy 3: Visual manifestation pivoting
    abstract_to_concrete_mapping = {
        "theory": ["scientist", "laboratory", "university"],
        "concept": ["diagram", "illustration", "museum"],
        "analysis": ["document", "research", "institution"],
        "development": ["building", "construction", "progress"],
        "movement": ["people", "demonstration", "gathering"],
        "revolution": ["conflict", "leaders", "historical"],
        "culture": ["art", "architecture", "tradition"],
        "economy": ["market", "business", "industry"],
        "politics": ["government", "parliament", "leaders"],
        "philosophy": ["philosopher", "university", "manuscript"]
    }
    
    # Apply concrete mapping based on detected abstract terms
    all_text = f"{module.title} {submodule.title} {section_heading or ''} {context_hint or ''}".lower()
    for abstract_term, concrete_alternatives in abstract_to_concrete_mapping.items():
        if abstract_term in all_text:
            concrete_query = " ".join(submodule_words[:2] + [concrete_alternatives[0]])
            fallback_queries.append(concrete_query)
            break
    
    # Enhanced Strategy 4: High-probability Wikimedia content targeting
    if context_hint:
        hint_words = re.findall(r"[\w\-]+", context_hint)
        # Enhance hint with biographical/geographic elements likely to have photos
        if hint_words:
            enhanced_hint = " ".join(hint_words[:2] + ["biography"])
            fallback_queries.append(enhanced_hint)
    
    # Remove duplicates and ensure quality
    unique_queries = []
    for query in fallback_queries:
        if query and len(query) > 4 and query not in unique_queries:
            unique_queries.append(query)
    
    logger.debug(f"Generated {len(unique_queries)} enhanced fallback queries for attempt {attempt_state.attempt_number}")
    return unique_queries[:5]  # Limit fallback queries


async def _rank_images_with_llm(
    state: LearningPathState,
    module: EnhancedModule,
    submodule: Submodule,
    section_heading: Optional[str],
    candidates: List[Dict[str, Any]],
    max_select: int = 1,
) -> List[int]:
    """Ask LLM to select up to max_select relevant image indices from candidates, or none.

    Note: Currently unused by the enrichment flow, retained for potential future use.
    """
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

        from json import dumps
        prompt = ChatPromptTemplate.from_template(PROMPT_IMAGE_RANKING)
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
    """Create the markdown block for an image with optional caption and attribution in Spanish."""
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
        prompt = ChatPromptTemplate.from_template(PROMPT_IMAGE_SELECTION_WITH_CAPTION)
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


async def _select_image_with_alternatives_llm(
    state: LearningPathState,
    module: EnhancedModule,
    submodule: Submodule,
    section_heading: Optional[str],
    candidates: List[Dict[str, Any]],
    attempt_state: AttemptState,
    max_attempts: int = 3,
) -> Dict[str, Any]:
    """Enhanced LLM selection that provides alternative queries when no images are relevant.

    Returns a dict with one of:
    - {"success": True, "index": int, "caption": str} - successful selection
    - {"success": False, "alternative_queries": List[str], "reason": str} - needs retry with new queries
    - {"success": False} - no more options (terminal)
    """
    if not candidates:
        return {"success": False}
    
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

        # Build context for the prompt
        previous_queries_str = ", ".join([f'"{q}"' for queries in attempt_state.query_history for q in queries])
        
        attempt_context = ""
        if attempt_state.attempt_number == 1:
            attempt_context = "This is the first attempt."
        elif attempt_state.attempt_number < max_attempts:
            attempt_context = f"Previous attempts found images but they weren't relevant."
        else:
            attempt_context = "This is the final attempt - if no images are relevant, return empty JSON {{}}."

        # Generate attempt-specific guidance for enhanced success probability
        attempt_specific_guidance = ""
        if attempt_state.attempt_number == 1:
            attempt_specific_guidance = """ATTEMPT 1 STRATEGY - Balanced Approach:
- For conceptual topics: Look for BOTH diagrams/illustrations AND biographical content
- For models/theories: Scientific diagrams, flowcharts, or concept visualizations are IDEAL
- For historical topics: Photos of people, events, or documents work well
- For geographic topics: Maps, location photos, or institutional buildings
- Examples: "memory model" → Select memory model diagram OR Baddeley portrait"""
        elif attempt_state.attempt_number == 2:
            attempt_specific_guidance = """ATTEMPT 2 STRATEGY - Expanded Targeting:
- Add geographic, temporal, or institutional context for broader options
- For abstract concepts: Target key figures, universities, historical periods
- For technical topics: Look for technical illustrations, inventor photos, or application examples
- Include specific names, places, or documented visual elements
- Examples: "economic theory" → "Keynes portrait" OR "Cambridge University economics" """
        elif attempt_state.attempt_number >= 3:
            attempt_specific_guidance = """ATTEMPT 3 STRATEGY - MAXIMUM FLEXIBILITY (Final Attempt):
- **CRITICAL**: This is the last chance - be EXTREMELY lenient and select ANY reasonably related content
- **SELECTION PRIORITY** (any of these should trigger selection):
  1. ANY diagram/illustration related to the topic concept
  2. ANY photograph of people mentioned in the topic
  3. ANY technical drawing, mathematical illustration, or scientific visualization
  4. ANY geographical location, institution, or building related to the topic
  5. ANY historical document, artifact, or period image connected to the topic
- **EVIDENCE-BASED SUCCESS PATTERNS**:
  - Mathematical topics: Select ANY mathematical diagrams, even if abstract
  - Scientific topics: Select ANY related scientific illustrations or Nobel Prize winners
  - Theoretical topics: Select ANY related theorist's photograph or conceptual diagram
  - Economic topics: Select ANY economist's photo or economic graph/chart
- **FINAL ATTEMPT RULE**: If there's ANY visual connection to the topic, SELECT IT
- **STUDENT ENGAGEMENT**: Something relevant is infinitely better than nothing
- Examples: "Stokes theorem" + any mathematical diagram → SELECT; "Keynes theory" + any economist photo → SELECT"""

        rejection_history = ""
        if attempt_state.previous_rejection_reasons:
            rejection_history = f"Previous rejection reasons: {'; '.join(attempt_state.previous_rejection_reasons)}"

        from json import dumps
        prompt = ChatPromptTemplate.from_template(PROMPT_IMAGE_SELECTION_WITH_ALTERNATIVES)
        llm_getter = lambda: get_llm_for_evaluation(state.get("google_key_provider"), user=state.get("user"))
        
        raw = await run_chain(
            prompt,
            llm_getter,
            StrOutputParser(),
            {
                "attempt_number": attempt_state.attempt_number,
                "max_attempts": max_attempts,
                "attempt_context": attempt_context,
                "attempt_specific_guidance": attempt_specific_guidance,
                "previous_queries": previous_queries_str,
                "rejection_history": rejection_history,
                "caption_lang": state.get("language", "es"),
                "module_title": module.title,
                "submodule_title": submodule.title,
                "section_heading": section_heading or "",
                "candidates_json": dumps(compact, ensure_ascii=False),
            },
            max_retries=1,
            initial_retry_delay=0.5,
        )

        # Parse the enhanced JSON response
        import json
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {"success": False}
        
        data = json.loads(raw[start:end+1])
        if not isinstance(data, dict):
            return {"success": False}

        # Check for successful selection
        if "index" in data:
            idx = int(data.get("index"))
            caption = str(data.get("caption", "")).strip()
            if 0 <= idx < len(compact):
                return {"success": True, "index": idx, "caption": caption}
            else:
                return {"success": False}

        # Check for alternative queries
        if "alternative_queries" in data and attempt_state.attempt_number < max_attempts:
            alternative_queries = data.get("alternative_queries", [])
            reason = data.get("reason", "Images not relevant")
            if isinstance(alternative_queries, list) and alternative_queries:
                # Clean and validate queries
                cleaned_queries = []
                for q in alternative_queries:
                    if isinstance(q, str) and q.strip():
                        cleaned_queries.append(q.strip()[:50])  # Limit query length
                if cleaned_queries:
                    return {
                        "success": False,
                        "alternative_queries": cleaned_queries[:3],  # Limit to 3 queries
                        "reason": reason[:200]  # Limit reason length
                    }

        # Empty response or no valid alternatives
        return {"success": False}

    except Exception as e:
        logger.debug(f"Enhanced LLM selection failed: {e}")
        return {"success": False}


async def _find_relevant_image_with_retry(
    state: LearningPathState,
    module: EnhancedModule,
    submodule: Submodule,
    section_heading: Optional[str],
    exclude_urls: Optional[Set[str]] = None,
    topic_hint: Optional[str] = None,
    max_attempts: int = 3,
) -> Optional[Dict[str, Any]]:
    """Main retry orchestrator for finding relevant images with progressive query refinement."""
    
    # Get configuration for max attempts
    configured_max_attempts = state.get("max_image_search_attempts", max_attempts)
    max_attempts = min(max(configured_max_attempts, 1), 5)  # Clamp between 1 and 5
    
    # Initialize attempt state
    attempt_state = AttemptState(
        attempt_number=1,
        used_urls=exclude_urls.copy() if exclude_urls else set(),
        all_candidates_history=[],
        query_history=[],
        previous_rejection_reasons=[]
    )
    
    language = state.get("language", "en")
    
    for attempt in range(1, max_attempts + 1):
        attempt_state.attempt_number = attempt
        
        logger.debug(f"Image search attempt {attempt}/{max_attempts} for {submodule.title}")
        
        try:
            # Generate queries for this attempt
            if attempt == 1:
                # First attempt: use original query generation
                queries = await _generate_wikimedia_queries(
                    state, module, submodule, section_heading, context_hint=topic_hint
                )
            else:
                # Subsequent attempts: use alternative queries if available
                # (alternative queries will be set by previous attempt)
                if not hasattr(attempt_state, 'next_queries') or not attempt_state.next_queries:
                    logger.debug(f"No alternative queries available for attempt {attempt}, stopping")
                    break
                queries = attempt_state.next_queries
                delattr(attempt_state, 'next_queries')  # Clean up
            
            if not queries:
                logger.debug(f"No queries generated for attempt {attempt}, stopping")
                break
            
            # Add current queries to history
            attempt_state.query_history.append(queries)
            
            # Search for candidates
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
            
            # Exclude URLs already used
            all_candidates = [c for c in all_candidates if c.get("url") not in attempt_state.used_urls]
            
            if not all_candidates:
                logger.debug(f"No candidates found for attempt {attempt}")
                if attempt < max_attempts:
                    # Try to generate fallback queries for next attempt
                    fallback_queries = await _generate_fallback_alternative_queries(
                        state, module, submodule, section_heading, topic_hint, attempt_state, 
                        _determine_query_language(state, [state.get("user_topic", ""), module.title, submodule.title, section_heading or ""])
                    )
                    if fallback_queries:
                        attempt_state.next_queries = fallback_queries
                        continue
                break
            
            # Add candidates to history
            attempt_state.all_candidates_history.extend(all_candidates)
            
            # Try enhanced selection with alternative query generation
            selection_result = await _select_image_with_alternatives_llm(
                state, module, submodule, section_heading, all_candidates, attempt_state, max_attempts
            )
            
            if selection_result.get("success"):
                # Success! Return the selected image
                idx = selection_result["index"]
                chosen = all_candidates[idx]
                chosen["caption"] = selection_result.get("caption")
                
                logger.debug(f"Image found on attempt {attempt}/{max_attempts}")
                return chosen
            
            elif "alternative_queries" in selection_result and attempt < max_attempts:
                # LLM provided alternative queries for next attempt
                alternative_queries = selection_result["alternative_queries"]
                reason = selection_result.get("reason", "Images not relevant")
                
                # Store rejection reason
                attempt_state.previous_rejection_reasons.append(reason)
                
                # Generate enhanced alternative queries
                enhanced_alternatives = await _generate_alternative_queries(
                    state, module, submodule, section_heading, topic_hint,
                    alternative_queries, attempt_state
                )
                
                if enhanced_alternatives:
                    attempt_state.next_queries = enhanced_alternatives
                    logger.debug(f"Attempt {attempt} failed, trying {len(enhanced_alternatives)} alternative queries")
                    continue
                else:
                    logger.debug(f"No valid alternative queries for attempt {attempt}")
                    break
            else:
                # No alternatives or max attempts reached
                logger.debug(f"No alternatives available or max attempts reached at attempt {attempt}")
                break
                
        except Exception as e:
            logger.debug(f"Error in attempt {attempt}: {e}")
            if attempt >= max_attempts:
                break
            # Try to continue with next attempt if we have more tries
            continue
    
    logger.debug(f"Image search failed after {max_attempts} attempts for {submodule.title}")
    return None


async def _find_relevant_image_for_anchor(
    state: LearningPathState,
    module: EnhancedModule,
    submodule: Submodule,
    section_heading: Optional[str],
    exclude_urls: Optional[Set[str]] = None,
    topic_hint: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Generate queries, search Wikimedia, and select the best candidate with a caption.
    
    This function now uses the enhanced retry mechanism if enabled, otherwise falls back
    to the original single-attempt behavior for backward compatibility.
    """
    # Check if enhanced retry is enabled (default: True)
    use_retry = state.get("enhanced_image_search_enabled", True)
    
    if use_retry:
        return await _find_relevant_image_with_retry(
            state, module, submodule, section_heading, exclude_urls, topic_hint
        )
    else:
        # Original single-attempt logic for backward compatibility
        queries = await _generate_wikimedia_queries(state, module, submodule, section_heading, context_hint=topic_hint)
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
        # Use original selection method for backward compatibility
        selection = await _select_image_and_caption_with_llm(state, module, submodule, section_heading, all_candidates)
        if selection is None:
            return None
        idx = selection["index"]
        chosen = all_candidates[idx]
        chosen["caption"] = selection.get("caption")
        return chosen


# --- Anchor planning via LLM ---

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
        prompt = ChatPromptTemplate.from_template(PROMPT_PLAN_IMAGE_ANCHORS)
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


# --- Public API ---

async def enrich_content_with_images(
    state: LearningPathState,
    module: EnhancedModule,
    submodule: Submodule,
    content_markdown: str,
) -> str:
    """Enrich markdown content with contextual images from Wikimedia Commons.

    Behavior-preserving refactor: identical logic, prompts, and outputs; improved organization and typing only.
    """
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
