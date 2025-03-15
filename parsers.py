from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from models import (
    SearchQueryList, 
    ModuleList, 
    SubmoduleList, 
    EnhancedModuleList,
    TopicAnalysis,
    ModulePlanning
)

# Parser para la generación de consultas de búsqueda.
search_queries_parser = PydanticOutputParser(pydantic_object=SearchQueryList)

# Parser para la generación de la lista inicial de módulos.
modules_parser = PydanticOutputParser(pydantic_object=ModuleList)

# Parser para la generación de consultas específicas de módulo.
module_queries_parser = PydanticOutputParser(pydantic_object=SearchQueryList)

# Parser para la generación de submódulos.
submodule_parser = PydanticOutputParser(pydantic_object=SubmoduleList)

# Nuevos parsers para los modelos mejorados
topic_analysis_parser = PydanticOutputParser(pydantic_object=TopicAnalysis)
module_planning_parser = PydanticOutputParser(pydantic_object=ModulePlanning)
enhanced_modules_parser = PydanticOutputParser(pydantic_object=EnhancedModuleList)
