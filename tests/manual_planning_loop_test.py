import asyncio
import types

# Import directly the specific modules to avoid triggering graph_nodes __init__ re-exports
from backend.core.submodules.planning import plan_and_research_module_submodules
from backend.models.models import EnhancedModule, Submodule, SearchQuery, SearchServiceResult, ScrapedResult
from backend.parsers import parsers as PP
import backend.core.graph_nodes.helpers as helpers
import backend.core.graph_nodes.search_utils as search_utils
import backend.core.submodules.evaluation as evaluation


def make_stub_run_chain():
    submodule_parser = PP.submodule_parser
    search_queries_parser = PP.search_queries_parser
    refinement_query_parser = PP.refinement_query_parser

    async def stub_run_chain(prompt, llm_factory, parser, params, *args, **kwargs):
        if parser is search_queries_parser:
            return types.SimpleNamespace(
                queries=[
                    SearchQuery(keywords="module structure syllabus example", rationale="structure"),
                    SearchQuery(keywords="teaching sequence breakdown", rationale="sequence"),
                ]
            )
        if parser is refinement_query_parser:
            return types.SimpleNamespace(
                queries=[
                    SearchQuery(keywords="curriculum structure standard breakdown", rationale="gap-fill"),
                ]
            )
        if parser is submodule_parser:
            return types.SimpleNamespace(
                submodules=[
                    Submodule(title="Foundations", description="Basics", order=1),
                    Submodule(title="Core Concepts", description="Core", order=2),
                    Submodule(title="Applications", description="Apply", order=3),
                ]
            )
        return types.SimpleNamespace()

    return stub_run_chain


async def stub_evaluate_module_planning_sufficiency(state, module_id, module, planning_search_results):
    is_sufficient = len(planning_search_results) > 0
    return types.SimpleNamespace(
        is_sufficient=is_sufficient,
        knowledge_gaps=[] if is_sufficient else ["Need more examples of sequencing"],
        confidence_score=0.9 if is_sufficient else 0.4,
    )


def make_stub_execute_search_with_llm_retry():
    async def stub(query=None, state=None, **kwargs):
        results = [
            ScrapedResult(title="Syllabus Sample", url="https://example.com/syllabus", search_snippet="module breakdown", scraped_content="Module 1, Module 2"),
            ScrapedResult(title="Teaching Sequence", url="https://example.com/sequence", search_snippet="sequence", scraped_content="Foundations then Applications"),
        ]
        return SearchServiceResult(query=str(query), results=results, search_provider_error=None)
    return stub


async def main():
    helpers.run_chain = make_stub_run_chain()
    evaluation.evaluate_module_planning_sufficiency = stub_evaluate_module_planning_sufficiency
    search_utils.execute_search_with_llm_retry = make_stub_execute_search_with_llm_retry()

    async def progress_callback(message: str, **kwargs):
        pass

    state = {
        "user_topic": "Test Topic",
        "modules": [EnhancedModule(title="Test Module", description="Desc")],
        "enhanced_modules": [EnhancedModule(title="Test Module", description="Desc", submodules=[])],
        "language": "en",
        "search_language": "en",
        "max_planning_loops": 2,
        "planning_min_confidence": 0.75,
        "progress_callback": progress_callback,
    }

    module = EnhancedModule(title="Test Module", description="Desc")

    res = await plan_and_research_module_submodules(state, 0, module)
    assert isinstance(res, EnhancedModule)
    assert res.submodules and len(res.submodules) >= 1
    print("TEST_OK", len(res.submodules))


if __name__ == "__main__":
    asyncio.run(main())
