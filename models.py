from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Callable, Tuple, TypedDict, Annotated
from operator import add

# Topic Analysis Models
class TopicAnalysis(BaseModel):
    """Detailed breakdown of the topic's components for comprehensive understanding."""
    core_concepts: List[str] = Field(..., description="Primary and supporting concepts that form the foundation")
    knowledge_structure: Dict[str, List[str]] = Field(..., description="Fundamental principles, relationships, and context")
    complexity_layers: Dict[str, List[str]] = Field(..., description="Progression from basic to expert-level concepts")
    
class ModulePlanning(BaseModel):
    """Strategic approach to module creation following pedagogical principles."""
    progression_design: str = Field(..., description="How modules build expertise systematically")
    topic_focus: str = Field(..., description="Specific focus of each module")
    knowledge_building: str = Field(..., description="How complexity builds gradually")
    module_connections: str = Field(..., description="How modules interconnect")
    depth_balance: str = Field(..., description="How depth is balanced with accessibility")

# Modelo que representa una consulta de búsqueda.
class SearchQuery(BaseModel):
    keywords: str = Field(..., description="The search query keywords")
    rationale: str = Field(..., description="Explanation of why this search is important")

# Modelo base para un módulo de aprendizaje.
class Module(BaseModel):
    title: str = Field(..., description="Title of the learning module")
    description: str = Field(..., description="Detailed description of the module content")

# Enhanced Module with richer metadata
class EnhancedModule(BaseModel):
    title: str = Field(..., description="Title of the learning module")
    description: str = Field(..., description="Detailed description of the module content")
    core_concept: str = Field(default="", description="Single main concept this module focuses on")
    learning_objective: str = Field(default="", description="Clear goal of this module")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites for this module")
    key_components: List[str] = Field(default_factory=list, description="Brief outline of components")
    expected_outcomes: List[str] = Field(default_factory=list, description="What will be learned")
    submodules: List["Submodule"] = Field(default_factory=list, description="Submodules contained in this module")

# Modelo para representar un submódulo.
class Submodule(BaseModel):
    title: str = Field(..., description="Title of the submodule")
    description: str = Field(..., description="Description of what this submodule covers")
    order: int = Field(default=0, description="Order of this submodule within its parent module")
    core_concept: str = Field(default="", description="Single main concept this submodule focuses on")
    learning_objective: str = Field(default="", description="Clear educational goal")
    key_components: List[str] = Field(default_factory=list, description="Main components to be covered")
    depth_level: str = Field(default="intermediate", description="Level of depth: basic, intermediate, advanced, or expert")

# Enhanced SubmoduleContent with narrative structure
class SubmoduleContent(BaseModel):
    module_id: int = Field(..., description="ID of the parent module")
    submodule_id: int = Field(..., description="ID of the submodule within the module")
    title: str = Field(..., description="Title of the submodule")
    description: str = Field(..., description="Description of the submodule")
    search_queries: List[SearchQuery] = Field(..., description="Search queries used for submodule research")
    search_results: List[Dict[str, Any]] = Field(..., description="Search results used to develop the submodule")
    content: str = Field(..., description="Fully developed submodule content")
    summary: str = Field(default="", description="Brief summary of the submodule's content")
    connections: Dict[str, str] = Field(default_factory=dict, description="Connections to other modules/submodules")

# Modelo que recoge el contenido desarrollado para un módulo.
class ModuleContent(BaseModel):
    module_id: int = Field(..., description="Index of the module in the learning path")
    title: str = Field(..., description="Title of the learning module")
    description: str = Field(..., description="Description of the module content")
    search_queries: List[SearchQuery] = Field(..., description="Search queries used for module research")
    search_results: List[Dict[str, Any]] = Field(..., description="Search results used to develop the module")
    content: str = Field(..., description="Fully developed module content")
    summary: str = Field(default="", description="Brief summary of the module's content")
    connections: Dict[str, str] = Field(default_factory=dict, description="Connections to other modules")

# Contenedor para una lista de queries.
class SearchQueryList(BaseModel):
    queries: List[SearchQuery] = Field(..., description="List of search queries")

# Contenedor para una lista de módulos.
class ModuleList(BaseModel):
    modules: List[Module] = Field(..., description="List of learning modules")

# Contenedor para una lista de módulos mejorados.
class EnhancedModuleList(BaseModel):
    modules: List[EnhancedModule] = Field(..., description="List of enhanced learning modules")

# Contenedor para una lista de submódulos.
class SubmoduleList(BaseModel):
    submodules: List[Submodule] = Field(..., description="List of submodules")

# Estado global del flujo de generación de la ruta de aprendizaje.
class LearningPathState(TypedDict):
    user_topic: str
    topic_analysis: Optional[TopicAnalysis]
    module_planning: Optional[ModulePlanning]
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
