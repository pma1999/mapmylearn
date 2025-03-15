from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Callable, Tuple, TypedDict, Annotated
from operator import add

# Modelo que representa una consulta de búsqueda.
class SearchQuery(BaseModel):
    keywords: str = Field(..., description="The search query keywords")
    rationale: str = Field(..., description="Explanation of why this search is important")

# Modelo base para un módulo de aprendizaje.
class Module(BaseModel):
    title: str = Field(..., description="Title of the learning module")
    description: str = Field(..., description="Detailed description of the module content")

# Modelo para representar un submódulo.
class Submodule(BaseModel):
    title: str = Field(..., description="Title of the submodule")
    description: str = Field(..., description="Description of what this submodule covers")
    order: int = Field(..., description="Order of this submodule within its parent module")

# Modelo de módulo que incluye una lista de submódulos.
class EnhancedModule(BaseModel):
    title: str = Field(..., description="Title of the module")
    description: str = Field(..., description="Description of the module content")
    submodules: List[Submodule] = Field(..., description="Submodules contained in this module")

# Modelo que recoge el contenido desarrollado para un submódulo.
class SubmoduleContent(BaseModel):
    module_id: int = Field(..., description="ID of the parent module")
    submodule_id: int = Field(..., description="ID of the submodule within the module")
    title: str = Field(..., description="Title of the submodule")
    description: str = Field(..., description="Description of the submodule")
    search_queries: List[SearchQuery] = Field(..., description="Search queries used for submodule research")
    search_results: List[Dict[str, Any]] = Field(..., description="Search results used to develop the submodule")
    content: str = Field(..., description="Fully developed submodule content")

# Modelo que recoge el contenido desarrollado para un módulo.
class ModuleContent(BaseModel):
    module_id: int = Field(..., description="Index of the module in the learning path")
    title: str = Field(..., description="Title of the learning module")
    description: str = Field(..., description="Description of the module content")
    search_queries: List[SearchQuery] = Field(..., description="Search queries used for module research")
    search_results: List[Dict[str, Any]] = Field(..., description="Search results used to develop the module")
    content: str = Field(..., description="Fully developed module content")

# Contenedor para una lista de queries.
class SearchQueryList(BaseModel):
    queries: List[SearchQuery] = Field(..., description="List of search queries")

# Contenedor para una lista de módulos.
class ModuleList(BaseModel):
    modules: List[Module] = Field(..., description="List of learning modules")

# Contenedor para una lista de submódulos.
class SubmoduleList(BaseModel):
    submodules: List[Submodule] = Field(..., description="List of submodules")

# Estado global del flujo de generación de la ruta de aprendizaje.
class LearningPathState(TypedDict):
    user_topic: str
    search_queries: Optional[List[SearchQuery]]
    search_results: Optional[List[Dict[str, Any]]]
    modules: Optional[List[Module]]
    steps: Annotated[List[str], add]
    
    # Campos para el desarrollo de módulos (para el flujo inicial)
    current_module_index: Optional[int]
    module_search_queries: Optional[List[SearchQuery]]
    module_search_results: Optional[List[Dict[str, Any]]]
    developed_modules: Optional[List[ModuleContent]]
    final_learning_path: Optional[Dict[str, Any]]
    
    # Campos de control de procesamiento paralelo
    parallel_count: Optional[int]
    module_batches: Optional[List[List[int]]]
    current_batch_index: Optional[int]
    modules_in_process: Optional[Dict[int, Dict[str, Any]]]
    progress_callback: Optional[Callable]
    search_parallel_count: Optional[int]
    
    # Campos para la planificación y procesamiento de submódulos
    enhanced_modules: Optional[List[EnhancedModule]]
    submodule_parallel_count: Optional[int]
    submodule_batches: Optional[List[List[Tuple[int, int]]]]
    current_submodule_batch_index: Optional[int]
    submodules_in_process: Optional[Dict[Tuple[int, int], Dict[str, Any]]]
    developed_submodules: Optional[List[SubmoduleContent]]
