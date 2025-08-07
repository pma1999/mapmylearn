import logging
from typing import List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from backend.models.models import (
    LearningPathState,
    EnhancedModule,
    Submodule,
    QuizQuestion,
    QuizQuestionList,
)
from backend.parsers.parsers import quiz_questions_parser
from backend.services.services import get_llm
from backend.core.graph_nodes.helpers import escape_curly_braces, run_chain, MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT
from backend.core.submodules.utils import extract_json_from_markdown
from backend.prompts.learning_path_prompts import SUBMODULE_QUIZ_GENERATION_PROMPT


async def generate_submodule_quiz(
    state: LearningPathState,
    module_id: int,
    sub_id: int,
    module: EnhancedModule,
    submodule: Submodule,
    submodule_content: str,
) -> List[QuizQuestion]:
    logger = logging.getLogger("learning_path.quiz_generator")
    logger.info(
        f"Generating quiz questions for submodule {sub_id+1} of module {module_id+1}: {submodule.title}"
    )

    progress_callback = state.get("progress_callback")

    if state.get("quiz_generation_enabled") is False:
        logger.info(
            f"Quiz generation is disabled, skipping for submodule {module_id}.{sub_id}"
        )
        return []

    try:
        import time

        start_time = time.time()

        if progress_callback:
            await progress_callback(
                f"Generating quiz questions for {module.title} > {submodule.title}",
                phase="quiz_generation",
                phase_progress=0.1,
                overall_progress=0.8,
                action="processing",
            )

        from backend.utils.language_utils import get_full_language_name

        output_language_code = state.get("language", "en")
        output_language = get_full_language_name(output_language_code)

        escaped_content = escape_curly_braces(submodule_content)
        user_topic = escape_curly_braces(state["user_topic"])
        module_title = escape_curly_braces(module.title)
        submodule_title = escape_curly_braces(submodule.title)
        submodule_description = escape_curly_braces(submodule.description)

        modified_quiz_prompt = (
            SUBMODULE_QUIZ_GENERATION_PROMPT
            + """
## IMPORTANT FORMAT INSTRUCTIONS
- Return ONLY the raw JSON output without any markdown formatting
- DO NOT wrap your response in ```json or ``` markdown code blocks
- Provide a clean, valid JSON object that can be directly parsed
"""
        )

        prompt = ChatPromptTemplate.from_template(modified_quiz_prompt)

        llm = await get_llm(
            key_provider=state.get("google_key_provider"), user=state.get("user")
        )

        try:
            result = await run_chain(
                prompt,
                lambda: get_llm(
                    key_provider=state.get("google_key_provider"), user=state.get("user")
                ),
                quiz_questions_parser,
                {
                    "user_topic": user_topic,
                    "module_title": module_title,
                    "submodule_title": submodule_title,
                    "submodule_description": submodule_description,
                    "submodule_content": escaped_content[
                        :MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT
                    ],
                    "language": output_language,
                    "format_instructions": quiz_questions_parser.get_format_instructions(),
                },
            )

            quiz_questions = result.questions

        except Exception as parsing_error:
            logger.warning(
                f"Standard parsing failed, attempting to extract JSON from response: {str(parsing_error)}"
            )

            raw_response = await run_chain(
                prompt,
                lambda: get_llm(
                    key_provider=state.get("google_key_provider"), user=state.get("user")
                ),
                StrOutputParser(),
                {
                    "user_topic": user_topic,
                    "module_title": module_title,
                    "submodule_title": submodule_title,
                    "submodule_description": submodule_description,
                    "submodule_content": escaped_content[
                        :MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT
                    ],
                    "language": output_language,
                    "format_instructions": quiz_questions_parser.get_format_instructions(),
                },
                max_retries=3,
                initial_retry_delay=1.0,
            )

            json_data = extract_json_from_markdown(raw_response)

            if json_data and "questions" in json_data:
                result = QuizQuestionList(**json_data)
                quiz_questions = result.questions
                logger.info(
                    "Successfully extracted quiz questions from markdown-formatted response"
                )
            else:
                logger.error(
                    f"Failed to extract valid JSON from LLM response: {raw_response[:500]}..."
                )
                if progress_callback:
                    await progress_callback(
                        f"Could not generate quiz questions for {module.title} > {submodule.title} due to formatting issues",
                        phase="quiz_generation",
                        phase_progress=0.5,
                        overall_progress=0.8,
                        action="error",
                    )
                return []

        if not quiz_questions:
            logger.warning(
                f"No quiz questions generated for submodule {module_id}.{sub_id}"
            )
            return []

        if len(quiz_questions) > 10:
            logger.info(
                f"Trimming excess quiz questions from {len(quiz_questions)} to 10"
            )
            quiz_questions = quiz_questions[:10]

        generation_time = time.time() - start_time
        logger.info(
            f"Generated {len(quiz_questions)} quiz questions for submodule {module_id}.{sub_id} in {generation_time:.2f}s"
        )

        if progress_callback:
            await progress_callback(
                f"Generated {len(quiz_questions)} quiz questions for {module.title} > {submodule.title}",
                phase="quiz_generation",
                phase_progress=1.0,
                overall_progress=0.85,
                preview_data={"quiz_count": len(quiz_questions)},
                action="completed",
            )

        return quiz_questions

    except Exception as e:
        error_msg = (
            f"Error generating quiz questions for submodule {module_id}.{sub_id}: {str(e)}"
        )
        logger.exception(error_msg)

        if state.get("quiz_generation_errors") is None:
            state["quiz_generation_errors"] = {}

        error_key = f"{module_id}:{sub_id}"
        state["quiz_generation_errors"][error_key] = str(e)

        if progress_callback:
            await progress_callback(
                f"Error generating quiz questions: {str(e)}",
                phase="quiz_generation",
                phase_progress=0.5,
                overall_progress=0.8,
                action="error",
            )

        return []
