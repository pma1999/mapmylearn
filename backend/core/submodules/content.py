import logging
from typing import List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from backend.models.models import (
    LearningPathState,
    EnhancedModule,
    Submodule,
    SearchQuery,
    SearchServiceResult,
)
from backend.services.services import get_llm_with_search, get_llm_for_evaluation
from backend.core.graph_nodes.helpers import run_chain, escape_curly_braces, MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT
from backend.core.submodules.context_builders import (
    build_learning_path_context,
    build_module_context,
    build_adjacent_context,
    build_enhanced_search_context,
)


async def develop_submodule_specific_content(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    sub_queries: List[SearchQuery],
    sub_search_results: List[SearchServiceResult],
) -> str:
    """
    Develops comprehensive, detailed content for a submodule using enhanced prompting.
    """
    logger = logging.getLogger("learning_path.content_developer")
    logger.info(f"Developing enhanced content for submodule: {submodule.title}")

    from backend.utils.language_utils import get_full_language_name

    output_language_code = state.get("language", "en")
    output_language = get_full_language_name(output_language_code)
    style = state.get("explanation_style", "standard")

    style_descriptions = {
        "standard": """
**Style Instructions**: Provide balanced, comprehensive explanations suitable for focused learning. Use clear terminology and provide extensive detail with good depth. Structure content logically with smooth transitions between concepts. Aim for 1800-2200 words of substantial educational content.
""",
        "simple": """
**Style Instructions**: Explain concepts as if teaching someone intelligent but new to the topic. Prioritize absolute clarity and understanding. Use accessible vocabulary while maintaining accuracy. Include plenty of analogies and step-by-step breakdowns. Build concepts very gradually. Aim for 1600-2000 words with extensive explanations and examples.
""",
        "technical": """
**Style Instructions**: Provide precise, detailed technical exposition. Use correct technical terminology and formal language. Include specific mechanisms, implementation details, and underlying principles. Assume solid foundational knowledge but explain advanced concepts thoroughly. Aim for 2000-2500 words with comprehensive technical depth.
""",
        "example": """
**Style Instructions**: Illustrate every key concept with concrete, practical examples. Include relevant code snippets, case studies, or real-world scenarios throughout. Each major point should be demonstrated with at least one detailed example. Focus heavily on application and implementation. Aim for 1800-2300 words with extensive practical examples.
""",
        "conceptual": """
**Style Instructions**: Emphasize core principles, the 'why' behind concepts, and relationships between ideas. Focus on building mental models and deep understanding. Explore implications and connections extensively. Prioritize conceptual frameworks over implementation details. Aim for 1700-2100 words with thorough conceptual exploration.
""",
        "grumpy_genius": """
**Style Instructions**: Adopt the persona of a brilliant expert who finds explaining this topic mildly tedious but does so with comedic reluctance and sharp insights. Use phrases like "Look, this is actually straightforward once you stop overthinking it..." or "*Sigh*... Fine, let me explain why everyone gets this wrong...". Maintain accuracy while adding personality and humor. Aim for 1800-2200 words with engaging, personality-driven explanations.
""",
    }

    style_instructions = style_descriptions.get(style, style_descriptions["standard"])

    learning_path_context = build_learning_path_context(state, module_id)
    module_context = build_module_context(module, sub_id)
    adjacent_context = build_adjacent_context(module, sub_id)

    search_results_context = build_enhanced_search_context(sub_search_results)

    from backend.prompts.learning_path_prompts import (
        ENHANCED_SUBMODULE_CONTENT_DEVELOPMENT_PROMPT,
    )
    prompt = ChatPromptTemplate.from_template(
        ENHANCED_SUBMODULE_CONTENT_DEVELOPMENT_PROMPT
    )

    try:
        llm_getter = lambda: get_llm_with_search(
            key_provider=state.get("google_key_provider"), user=state.get("user")
        )

        developed_content = await run_chain(
            prompt,
            llm_getter,
            StrOutputParser(),
            {
                "user_topic": escape_curly_braces(state["user_topic"]),
                "module_title": escape_curly_braces(module.title),
                "module_order": module_id + 1,
                "module_count": len(state.get("enhanced_modules", [])),
                "submodule_title": escape_curly_braces(submodule.title),
                "submodule_order": sub_id + 1,
                "submodule_count": len(module.submodules),
                "submodule_description": escape_curly_braces(submodule.description),
                "core_concept": escape_curly_braces(submodule.core_concept),
                "learning_objective": escape_curly_braces(submodule.learning_objective),
                "key_components": escape_curly_braces(
                    ", ".join(submodule.key_components)
                ),
                "depth_level": escape_curly_braces(submodule.depth_level),
                "learning_path_context": learning_path_context,
                "module_context": module_context,
                "adjacent_context": adjacent_context,
                "style_instructions": style_instructions,
                "language": output_language,
                "search_results_context": search_results_context,
            },
            max_retries=5,
            initial_retry_delay=1.0,
        )

        content_length = len(developed_content)
        logger.info(
            f"Generated enhanced content for {submodule.title}: {content_length} characters"
        )

        if content_length < 3000:
            logger.warning(
                f"Generated content may be shorter than expected: {content_length} chars"
            )

        return developed_content

    except Exception as e:
        logger.exception(f"Error in enhanced content development: {str(e)}")
        raise


async def develop_enhanced_content(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    current_content: str,
    refinement_search_results: List[SearchServiceResult],
) -> str:
    """
    Enhances existing content with new information from refinement searches.
    This performs ENHANCEMENT rather than complete regeneration.
    """
    logger = logging.getLogger("learning_path.content_enhancer")
    logger.info(
        f"Enhancing content for submodule {module_id+1}.{sub_id+1}: {submodule.title}"
    )

    from backend.utils.language_utils import get_full_language_name

    google_key_provider = state.get("google_key_provider")
    output_language_code = state.get("language", "en")
    output_language = get_full_language_name(output_language_code)
    explanation_style = state.get("explanation_style", "standard")

    refinement_context = ""
    for result in refinement_search_results:
        if result.search_provider_error:
            continue

        for item in result.results:
            refinement_context += f"Title: {item.title}\n"
            refinement_context += f"Content: {item.content[:500]}...\n"
            refinement_context += f"URL: {item.url}\n\n"

    if not refinement_context.strip():
        logger.warning(
            f"No useful refinement information found for submodule {module_id+1}.{sub_id+1}, returning original content"
        )
        return current_content

    enhancement_prompt = """# EDUCATIONAL CONTENT ENHANCEMENT SPECIALIST

Your task is to ENHANCE existing educational content by incorporating new information from refinement research.

## ENHANCEMENT CONTEXT
- Subject Topic: {user_topic}
- Module: {module_title}
- Submodule: {submodule_title}
- Target Style: {explanation_style}
- Language: {output_language}

## CURRENT CONTENT (TO BE ENHANCED)
{current_content}

## REFINEMENT INFORMATION (FOR ENHANCEMENT)
{refinement_context}

## ENHANCEMENT INSTRUCTIONS

### 1. PRESERVE STRUCTURE AND CORE CONTENT
- Keep the existing content structure and organization
- Preserve all correct information already present
- Maintain the original educational flow and progression

### 2. STRATEGIC ENHANCEMENT APPROACH
- **ENHANCE** rather than rewrite completely
- Add new information that fills gaps or improves explanations
- Integrate better examples, analogies, or practical applications
- Improve clarity where needed without losing technical accuracy

### 3. ENHANCEMENT PRIORITIES
- Add missing key concepts or details
- Improve explanations that were unclear or incomplete
- Insert better examples or real-world applications
- Enhance technical accuracy with updated information
- Add practical insights or methodologies

### 4. INTEGRATION GUIDELINES
- Seamlessly weave new information into existing content
- Ensure enhanced content flows naturally
- Maintain consistent tone and style throughout
- Preserve the educational objectives and learning outcomes

### 5. QUALITY ENHANCEMENT
- Improve content depth without overwhelming the reader
- Add clarifying details where concepts were too brief
- Include practical examples that illustrate key points
- Enhance pedagogical effectiveness for better learning

## CONTENT STYLE REQUIREMENTS
{style_description}

## OUTPUT REQUIREMENTS
Provide the ENHANCED content that:
- Incorporates the most valuable refinement information
- Maintains the original structure while improving quality
- Addresses content gaps identified in evaluation
- Remains focused on the submodule learning objectives
- Is more comprehensive, clear, and educationally effective than the original

## IMPORTANT: OUTPUT ONLY THE ENHANCED CONTENT
Do not include meta-commentary, explanations of changes, or section headers describing the enhancement process.
"""

    style_descriptions = {
        "standard": "",
        "simple": "Use simple vocabulary and sentence structure. Incorporate basic analogies if helpful. Prioritize clarity over technical precision.",
        "technical": "Use correct technical terms and formal language. Include specific details, mechanisms, and underlying principles.",
        "example": "Illustrate every key concept with concrete, practical examples. Include relevant code snippets or pseudocode where applicable.",
        "conceptual": "Emphasize core principles, relationships between ideas, and mental models. Focus on the 'why' behind concepts.",
        "grumpy_genius": "Adopt a comedic reluctant expert persona while providing clear explanations. Use phrases showing mild intellectual impatience but always follow with correct information.",
    }

    style_description = style_descriptions.get(explanation_style, "")

    prompt = ChatPromptTemplate.from_template(enhancement_prompt)

    try:
        llm = get_llm_for_evaluation(
            key_provider=google_key_provider, user=state.get("user")
        )

        enhanced_content_response = await llm.ainvoke(
            prompt.format(
                user_topic=escape_curly_braces(state["user_topic"]),
                module_title=escape_curly_braces(module.title),
                submodule_title=escape_curly_braces(submodule.title),
                explanation_style=explanation_style,
                output_language=output_language,
                current_content=escape_curly_braces(current_content),
                refinement_context=escape_curly_braces(refinement_context),
                style_description=style_description,
            )
        )

        enhanced_content = enhanced_content_response.content.strip()

        if len(enhanced_content) < len(current_content) * 0.8:
            logger.warning(
                f"Enhanced content seems too short for submodule {module_id+1}.{sub_id+1}, using original content"
            )
            return current_content

        logger.info(
            f"Content successfully enhanced for submodule {module_id+1}.{sub_id+1} (original: {len(current_content)} chars, enhanced: {len(enhanced_content)} chars)"
        )
        return enhanced_content

    except Exception as e:
        logger.exception(
            f"Error enhancing content for submodule {module_id+1}.{sub_id+1}: {str(e)}"
        )
        logger.info("Returning original content due to enhancement error")
        return current_content
