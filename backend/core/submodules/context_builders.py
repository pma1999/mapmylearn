from typing import List
import logging
from backend.models.models import LearningPathState, EnhancedModule, SearchServiceResult
from backend.core.graph_nodes.helpers import escape_curly_braces, MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT


def build_learning_path_context(state: LearningPathState, current_module_id: int) -> str:
    try:
        modules = state.get("enhanced_modules", [])
        if not modules:
            return "No course structure available."

        context_parts = ["# COMPLETE COURSE STRUCTURE\n"]

        for i, mod in enumerate(modules):
            is_current = i == current_module_id
            status_indicator = " **\u2190 CURRENT MODULE**" if is_current else ""

            mod_title = escape_curly_braces(getattr(mod, 'title', f'Module {i+1}'))
            mod_desc = escape_curly_braces(getattr(mod, 'description', 'No description'))

            context_parts.append(f"## Module {i+1}: {mod_title}{status_indicator}")
            context_parts.append(f"**Description**: {mod_desc}")

            if hasattr(mod, 'submodules') and mod.submodules:
                context_parts.append("**Submodules**:")
                for j, sub in enumerate(mod.submodules):
                    sub_title = escape_curly_braces(getattr(sub, 'title', f'Submodule {j+1}'))
                    context_parts.append(f"  {j+1}. {sub_title}")

            context_parts.append("")

        return "\n".join(context_parts)

    except Exception as e:
        logging.error(f"Error building learning path context: {str(e)}")
        return f"Error building course context: {str(e)}"


def build_module_context(module: EnhancedModule, current_sub_id: int) -> str:
    try:
        module_title = escape_curly_braces(getattr(module, 'title', 'Current Module'))
        module_desc = escape_curly_braces(getattr(module, 'description', 'No description'))

        context_parts = [
            f"# CURRENT MODULE DETAILS",
            f"**Title**: {module_title}",
            f"**Description**: {module_desc}",
            "",
            "## Module Submodules Structure:"
        ]

        if hasattr(module, 'submodules') and module.submodules:
            for i, sub in enumerate(module.submodules):
                is_current = i == current_sub_id
                status_indicator = " **\u2190 CURRENT SUBMODULE**" if is_current else ""

                sub_title = escape_curly_braces(getattr(sub, 'title', f'Submodule {i+1}'))
                sub_desc = escape_curly_braces(getattr(sub, 'description', 'No description'))

                context_parts.append(f"### {i+1}. {sub_title}{status_indicator}")
                context_parts.append(f"**Description**: {sub_desc}")

                if hasattr(sub, 'key_components') and sub.key_components:
                    components = ', '.join([escape_curly_braces(comp) for comp in sub.key_components])
                    context_parts.append(f"**Key Components**: {components}")

                if hasattr(sub, 'learning_objective'):
                    objective = escape_curly_braces(getattr(sub, 'learning_objective', ''))
                    if objective:
                        context_parts.append(f"**Learning Objective**: {objective}")

                context_parts.append("")
        else:
            context_parts.append("No submodules defined for this module.")

        return "\n".join(context_parts)

    except Exception as e:
        logging.error(f"Error building module context: {str(e)}")
        return f"Error building module context: {str(e)}"


def build_adjacent_context(module: EnhancedModule, current_sub_id: int) -> str:
    try:
        if not hasattr(module, 'submodules') or not module.submodules:
            return "No adjacent submodules available."

        context_parts = ["# LEARNING PROGRESSION CONTEXT\n"]

        if current_sub_id > 0:
            prev_sub = module.submodules[current_sub_id - 1]
            prev_title = escape_curly_braces(getattr(prev_sub, 'title', f'Previous Submodule'))
            prev_desc = escape_curly_braces(getattr(prev_sub, 'description', 'No description'))

            context_parts.append(f"## Previous Submodule ({current_sub_id}): {prev_title}")
            context_parts.append(f"**Description**: {prev_desc}")

            if hasattr(prev_sub, 'core_concept'):
                prev_concept = escape_curly_braces(getattr(prev_sub, 'core_concept', ''))
                if prev_concept:
                    context_parts.append(f"**Core Concept**: {prev_concept}")

            context_parts.append("*This provides the foundation for the current submodule.*")
            context_parts.append("")
        else:
            context_parts.append("## Previous Submodule: None (This is the first submodule)")
            context_parts.append("")

        if current_sub_id < len(module.submodules) - 1:
            next_sub = module.submodules[current_sub_id + 1]
            next_title = escape_curly_braces(getattr(next_sub, 'title', f'Next Submodule'))
            next_desc = escape_curly_braces(getattr(next_sub, 'description', 'No description'))

            context_parts.append(f"## Next Submodule ({current_sub_id + 2}): {next_title}")
            context_parts.append(f"**Description**: {next_desc}")

            if hasattr(next_sub, 'core_concept'):
                next_concept = escape_curly_braces(getattr(next_sub, 'core_concept', ''))
                if next_concept:
                    context_parts.append(f"**Core Concept**: {next_concept}")

            context_parts.append("*The current submodule should prepare learners for this next step.*")
        else:
            context_parts.append("## Next Submodule: None (This is the final submodule)")
            context_parts.append("*This submodule should provide comprehensive closure for the module.*")

        return "\n".join(context_parts)

    except Exception as e:
        logging.error(f"Error building adjacent context: {str(e)}")
        return f"Error building adjacent context: {str(e)}"


def build_enhanced_search_context(search_results: List[SearchServiceResult]) -> str:
    try:
        if not search_results:
            return "No research materials available for this submodule."

        context_parts = []
        total_sources = 0
        max_results_per_query = 4

        for result_group in search_results:
            if result_group.search_provider_error:
                logging.warning(f"Skipping failed search: {result_group.search_provider_error}")
                continue

            query = escape_curly_braces(result_group.query)
            context_parts.append(f"\n## Research Query: \"{query}\"")
            context_parts.append(f"*This search aimed to gather information relevant to the submodule development.*")
            context_parts.append("")

            valid_results = 0
            for i, result_item in enumerate(result_group.results):
                if valid_results >= max_results_per_query:
                    break

                has_content = bool(result_item.scraped_content or result_item.search_snippet)
                if not has_content:
                    continue

                valid_results += 1
                total_sources += 1

                title = escape_curly_braces(result_item.title or 'Untitled Source')
                url = result_item.url or 'No URL'

                context_parts.append(f"### Source {valid_results}: {title}")
                context_parts.append(f"**URL**: {url}")

                if result_item.scraped_content:
                    content = escape_curly_braces(result_item.scraped_content)
                    truncated_content = content[:MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT * 2]
                    if len(content) > MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT * 2:
                        truncated_content += "\n\n*(Content truncated for brevity)*"

                    context_parts.append(f"**Content Summary**:")
                    context_parts.append(truncated_content)

                elif result_item.search_snippet:
                    snippet = escape_curly_braces(result_item.search_snippet)
                    error_info = ""
                    if result_item.scrape_error:
                        error_info = f" *(Note: Full content scraping failed - {escape_curly_braces(result_item.scrape_error)})*"

                    truncated_snippet = snippet[:MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT]
                    if len(snippet) > MAX_CHARS_PER_SCRAPED_RESULT_CONTEXT:
                        truncated_snippet += "\n\n*(Snippet truncated)*"

                    context_parts.append(f"**Search Snippet**:{error_info}")
                    context_parts.append(truncated_snippet)

                context_parts.append("")

            if valid_results == 0:
                context_parts.append("*No usable content was found for this research query.*")
                context_parts.append("")
            else:
                context_parts.append(f"*Found {valid_results} relevant sources for this query.*")
                context_parts.append("")

        summary_header = [
            f"# COMPREHENSIVE RESEARCH MATERIALS",
            f"*The following {total_sources} sources provide research context and information to enhance submodule content development.*",
            ""
        ]

        return "\n".join(summary_header + context_parts)

    except Exception as e:
        logging.error(f"Error building enhanced search context: {str(e)}")
        return f"Error building research context: {str(e)}"
