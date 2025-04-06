from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from backend.models.models import (
    SearchQueryList, 
    ModuleList, 
    SubmoduleList, 
    EnhancedModuleList, 
    TopicAnalysis, 
    ModulePlanning, 
    QuizQuestionList,
    ResourceList,
    ResourceQuery
)

search_queries_parser = PydanticOutputParser(pydantic_object=SearchQueryList)
modules_parser = PydanticOutputParser(pydantic_object=ModuleList)
module_queries_parser = PydanticOutputParser(pydantic_object=SearchQueryList)
submodule_parser = PydanticOutputParser(pydantic_object=SubmoduleList)
topic_analysis_parser = PydanticOutputParser(pydantic_object=TopicAnalysis)
module_planning_parser = PydanticOutputParser(pydantic_object=ModulePlanning)
enhanced_modules_parser = PydanticOutputParser(pydantic_object=EnhancedModuleList)
quiz_questions_parser = PydanticOutputParser(pydantic_object=QuizQuestionList)
resource_list_parser = PydanticOutputParser(pydantic_object=ResourceList)
resource_query_parser = PydanticOutputParser(pydantic_object=ResourceQuery)
