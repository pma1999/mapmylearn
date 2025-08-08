from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from backend.models.models import (
    SearchQueryList, SearchQuery, EnhancedModuleList,
    ModuleList, 
    SubmoduleList, 
    TopicAnalysis, 
    ModulePlanning, 
    QuizQuestionList,
    ResourceList,
    ResourceSelectionList,
    ResourceQuery,
    ResearchEvaluation,
    RefinementQueryList,
    ContentEvaluation,
    ContentRefinementQueryList
)
import re
import logging
from typing import Optional, List

logger = logging.getLogger("learning_path.parsers")

search_queries_parser = PydanticOutputParser(pydantic_object=SearchQueryList)
modules_parser = PydanticOutputParser(pydantic_object=ModuleList)
module_queries_parser = PydanticOutputParser(pydantic_object=SearchQueryList)
submodule_parser = PydanticOutputParser(pydantic_object=SubmoduleList)
topic_analysis_parser = PydanticOutputParser(pydantic_object=TopicAnalysis)
module_planning_parser = PydanticOutputParser(pydantic_object=ModulePlanning)
enhanced_modules_parser = PydanticOutputParser(pydantic_object=EnhancedModuleList)
quiz_questions_parser = PydanticOutputParser(pydantic_object=QuizQuestionList)
resource_list_parser = PydanticOutputParser(pydantic_object=ResourceList)
resource_selection_parser = PydanticOutputParser(pydantic_object=ResourceSelectionList)
resource_query_parser = PydanticOutputParser(pydantic_object=ResourceQuery)
research_evaluation_parser = PydanticOutputParser(pydantic_object=ResearchEvaluation)
refinement_query_parser = PydanticOutputParser(pydantic_object=RefinementQueryList)
content_evaluation_parser = PydanticOutputParser(pydantic_object=ContentEvaluation)
content_refinement_query_parser = PydanticOutputParser(pydantic_object=ContentRefinementQueryList)
# NEW: Alias for planning evaluation (reuse ResearchEvaluation schema)
planning_research_evaluation_parser = PydanticOutputParser(pydantic_object=ResearchEvaluation)

def parse_initial_flow_response(response_text: str) -> Optional[EnhancedModuleList]:
    """
    Parse initial flow response from LLM into EnhancedModuleList object.
    Uses existing enhanced_modules_parser as the structure is the same.
    
    Args:
        response_text: Raw LLM response text
        
    Returns:
        EnhancedModuleList object or None if parsing fails
    """
    try:
        # Use the existing enhanced_modules_parser since the structure is the same
        return enhanced_modules_parser(response_text)
    except Exception as e:
        logger.error(f"Error parsing initial flow response: {str(e)}")
        return None


def parse_search_queries(response_text: str) -> Optional[List[SearchQuery]]:
    """
    Parse search queries from LLM response.
    
    Args:
        response_text: Raw LLM response text containing search queries
        
    Returns:
        List of SearchQuery objects or None if parsing fails
    """
    try:
        # Use existing search_queries_parser function
        return search_queries_parser(response_text)
    except Exception as e:
        logger.error(f"Error parsing search queries: {str(e)}")
        return None


def parse_resource_queries(response_text: str) -> Optional[List[ResourceQuery]]:
    """
    Parse resource queries from LLM response.
    
    Args:
        response_text: Raw LLM response text containing resource queries
        
    Returns:
        List of ResourceQuery objects or None if parsing fails
    """
    try:
        # Extract resource queries from response
        lines = response_text.strip().split('\n')
        queries = []
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '*')) or 
                        line.lower().startswith(('find', 'search', 'look', 'research'))):
                # Clean the query
                query = re.sub(r'^\d+\.\s*', '', line)  # Remove numbering
                query = re.sub(r'^[-*]\s*', '', query)  # Remove bullet points
                query = query.strip()
                
                if query and len(query) > 5:  # Minimum reasonable query length
                    queries.append(ResourceQuery(query=query))
        
        if not queries:
            # Fallback: treat the entire response as a single query if no structured format found
            clean_query = response_text.strip()
            if clean_query and len(clean_query) > 5:
                queries.append(ResourceQuery(query=clean_query))
        
        return queries if queries else None
        
    except Exception as e:
        logger.error(f"Error parsing resource queries: {str(e)}")
        return None
