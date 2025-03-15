from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from models import SearchQueryList, ModuleList, SubmoduleList

# Parser para la generación de consultas de búsqueda.
search_queries_parser = PydanticOutputParser(pydantic_object=SearchQueryList)

# Parser para la generación de la lista inicial de módulos.
modules_parser = PydanticOutputParser(pydantic_object=ModuleList)

# Parser para la generación de consultas específicas de módulo.
module_queries_parser = PydanticOutputParser(pydantic_object=SearchQueryList)

# Parser para la generación de submódulos.
submodule_parser = PydanticOutputParser(pydantic_object=SubmoduleList)
