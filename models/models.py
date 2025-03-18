from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, TypedDict, Annotated, Callable

# Topic Analysis Models
class TopicAnalysis(BaseModel):
    core_concepts: List[str] = Field(..., description="Primary and supporting concepts")
    knowledge_structure: Dict[str, List[str]] = Field(..., description="Fundamental principles and relationships")
    complexity_layers: Dict[str, List[str]] = Field(..., description="Progression from basic to expert-level concepts")
    
# Module Planning Model
class ModulePlanning(BaseModel):
    progression_design: str = Field(..., description="How modules build expertise")
    topic_focus: str = Field(..., description="Focus of each module")
    knowledge_building: str = Field(..., description="How complexity builds gradually")
    module_connections: str = Field(..., description="How modules interconnect")
    depth_balance: str = Field(..., description="Balance between depth and accessibility")

# Search Query Model
class SearchQuery(BaseModel):
    keywords: str = Field(..., description="Search query keywords")
    rationale: str = Field(..., description="Rationale for the search query")

# Basic Module Model
class Module(BaseModel):
    title: str = Field(..., description="Title of the module")
    description: str = Field(..., description="Detailed description of the module")

# Enhanced Module Model
class EnhancedModule(BaseModel):
    title: str = Field(..., description="Title of the module")
    description: str = Field(..., description="Detailed description of the module")
    core_concept: str = Field(default="", description="Main concept")
    learning_objective: str = Field(default="", description="Learning objective")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites")
    key_components: List[str] = Field(default_factory=list, description="Key components")
    expected_outcomes: List[str] = Field(default_factory=list, description="Expected outcomes")
    submodules: List["Submodule"] = Field(default_factory=list, description="List of submodules")

# Submodule Model
class Submodule(BaseModel):
    title: str = Field(..., description="Title of the submodule")
    description: str = Field(..., description="Description of the submodule")
    order: int = Field(default=0, description="Order within the module")
    core_concept: str = Field(default="", description="Main concept")
    learning_objective: str = Field(default="", description="Educational goal")
    key_components: List[str] = Field(default_factory=list, description="Key topics")
    depth_level: str = Field(default="intermediate", description="Level: basic, intermediate, advanced, expert")

# Enhanced SubmoduleContent Model
class SubmoduleContent(BaseModel):
    module_id: int = Field(..., description="ID of the parent module")
    submodule_id: int = Field(..., description="ID of the submodule")
    title: str = Field(..., description="Title of the submodule")
    description: str = Field(..., description="Submodule description")
    search_queries: List[SearchQuery] = Field(..., description="Search queries for submodule research")
    search_results: List[Dict[str, Any]] = Field(..., description="Search results for submodule")
    content: str = Field(..., description="Developed content")
    summary: str = Field(default="", description="Brief summary")
    connections: Dict[str, str] = Field(default_factory=dict, description="Connections to other modules/submodules")

# ModuleContent Model
class ModuleContent(BaseModel):
    module_id: int = Field(..., description="Module index")
    title: str = Field(..., description="Module title")
    description: str = Field(..., description="Module description")
    search_queries: List[SearchQuery] = Field(..., description="Search queries used")
    search_results: List[Dict[str, Any]] = Field(..., description="Search results used")
    content: str = Field(..., description="Developed module content")
    summary: str = Field(default="", description="Brief summary")
    connections: Dict[str, str] = Field(default_factory=dict, description="Connections to other modules")

# Container Models
class SearchQueryList(BaseModel):
    queries: List[SearchQuery] = Field(..., description="List of search queries")

class ModuleList(BaseModel):
    modules: List[Module] = Field(..., description="List of basic modules")

class EnhancedModuleList(BaseModel):
    modules: List[EnhancedModule] = Field(..., description="List of enhanced modules")

class SubmoduleList(BaseModel):
    submodules: List[Submodule] = Field(..., description="List of submodules")

# Global State for the Graph (TypedDict)
class LearningPathState(TypedDict):
    user_topic: str
    topic_analysis: Optional[TopicAnalysis]
    module_planning: Optional[ModulePlanning]
    search_queries: Optional[List[SearchQuery]]
    search_results: Optional[List[Dict[str, Any]]]
    modules: Optional[List[Module]]
    steps: Annotated[List[str], ...]
    current_module_index: Optional[int]
    module_search_queries: Optional[List[SearchQuery]]
    module_search_results: Optional[List[Dict[str, Any]]]
    developed_modules: Optional[List[ModuleContent]]
    final_learning_path: Optional[Dict[str, Any]]
    parallel_count: Optional[int]
    module_batches: Optional[List[List[int]]]
    current_batch_index: Optional[int]
    modules_in_process: Optional[Dict[int, Dict[str, Any]]]
    progress_callback: Optional[Callable]
    search_parallel_count: Optional[int]
    enhanced_modules: Optional[List[EnhancedModule]]
    submodule_parallel_count: Optional[int]
    submodule_batches: Optional[List[List[tuple]]]
    current_submodule_batch_index: Optional[int]
    submodules_in_process: Optional[Dict[tuple, Dict[str, Any]]]
    developed_submodules: Optional[List[SubmoduleContent]]
    google_api_key: Optional[str]
    pplx_api_key: Optional[str]
    desired_module_count: Optional[int]
    desired_submodule_count: Optional[int]

    
# Enable forward references for EnhancedModule.submodules
EnhancedModule.model_rebuild()
SubmoduleList.model_rebuild()
