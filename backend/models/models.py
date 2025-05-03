from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Any, Optional, TypedDict, Annotated, Callable, TYPE_CHECKING, Tuple

# Import the key provider types but only for type checking
if TYPE_CHECKING:  
    from services.key_provider import GoogleKeyProvider, PerplexityKeyProvider, BraveKeyProvider

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

# Resource Model
class Resource(BaseModel):
    title: str = Field(..., description="Title of the resource")
    description: str = Field(..., description="Description of what the resource offers")
    url: str = Field(..., description="URL to access the resource")
    type: str = Field(..., description="Type of resource (article, video, book, course, code, etc.)")

class ResourceList(BaseModel):
    resources: List[Resource] = Field(default_factory=list, description="List of resources")

class ResourceQuery(BaseModel):
    query: str = Field(..., description="Search query for finding resources")
    context: str = Field(..., description="Context information for the resource search")
    target_level: str = Field(..., description="Target level (topic, module, submodule)")

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
    resources: List[Resource] = Field(default_factory=list, description="Additional resources for this module")

# Submodule Model
class Submodule(BaseModel):
    title: str = Field(..., description="Title of the submodule")
    description: str = Field(..., description="Description of the submodule")
    order: int = Field(default=0, description="Order within the module")
    core_concept: str = Field(default="", description="Main concept")
    learning_objective: str = Field(default="", description="Educational goal")
    key_components: List[str] = Field(default_factory=list, description="Key topics")
    depth_level: str = Field(default="intermediate", description="Level: basic, intermediate, advanced, expert")
    resources: List[Resource] = Field(default_factory=list, description="Additional resources for this submodule")

# Quiz Question Model
class QuizOption(BaseModel):
    text: str = Field(..., description="The text of this answer option")
    is_correct: bool = Field(..., description="Whether this option is the correct answer")

class QuizQuestion(BaseModel):
    question: str = Field(..., description="The question text")
    options: List[QuizOption] = Field(..., description="List of answer options (typically 4)")
    explanation: str = Field(..., description="Explanation of the correct answer")

class QuizQuestionList(BaseModel):
    questions: List[QuizQuestion] = Field(..., description="List of quiz questions for a submodule")

# Enhanced SubmoduleContent Model
class SubmoduleContent(BaseModel):
    module_id: int = Field(..., description="ID of the parent module")
    submodule_id: int = Field(..., description="ID of the submodule")
    title: str = Field(..., description="Title of the submodule")
    description: str = Field(..., description="Submodule description")
    search_queries: List[SearchQuery] = Field(..., description="Search queries for submodule research")
    search_results: List[Dict[str, Any]] = Field(..., description="Search results for submodule")
    content: str = Field(..., description="Developed content")
    quiz_questions: Optional[List[QuizQuestion]] = Field(default=None, description="Quiz questions for this submodule")
    summary: str = Field(default="", description="Brief summary")
    connections: Dict[str, str] = Field(default_factory=dict, description="Connections to other modules/submodules")
    resources: List[Resource] = Field(default_factory=list, description="Additional resources for this submodule")
    resource_search_query: Optional[ResourceQuery] = Field(default=None, description="Query used to find resources")
    resource_search_results: Optional[List[Dict[str, Any]]] = Field(default=None, description="Raw results from resource search")

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
    resources: List[Resource] = Field(default_factory=list, description="Additional resources for this module")
    resource_search_query: Optional[ResourceQuery] = Field(default=None, description="Query used to find resources")
    resource_search_results: Optional[List[Dict[str, Any]]] = Field(default=None, description="Raw results from resource search")

# Container Models
class SearchQueryList(BaseModel):
    queries: List[SearchQuery] = Field(..., description="List of search queries")

class ModuleList(BaseModel):
    modules: List[Module] = Field(..., description="List of basic modules")

class EnhancedModuleList(BaseModel):
    modules: List[EnhancedModule] = Field(..., description="List of enhanced modules")

class SubmoduleList(BaseModel):
    submodules: List[Submodule] = Field(..., description="List of submodules")

# Models for Search Service results (e.g., Brave Search + Scraper)
class ScrapedResult(BaseModel):
    title: Optional[str] = Field(default=None, description="Title of the web page")
    url: str = Field(..., description="URL of the scraped page")
    search_snippet: Optional[str] = Field(default=None, description="Original snippet from search result (e.g., Brave)")
    scraped_content: Optional[str] = Field(default=None, description="Cleaned textual content scraped from the URL")
    scrape_error: Optional[str] = Field(default=None, description="Error message if scraping failed for this URL")

class SearchServiceResult(BaseModel):
    query: str = Field(..., description="The original search query performed")
    results: List[ScrapedResult] = Field(default_factory=list, description="List of scraped results for the query")
    search_provider_error: Optional[str] = Field(default=None, description="Error from the search provider API (e.g., Brave)")

# Global State for the Graph (TypedDict)
class LearningPathState(TypedDict):
    user_topic: str
    topic_analysis: Optional[TopicAnalysis]
    module_planning: Optional[ModulePlanning]
    search_queries: Optional[List[SearchQuery]]
    search_results: Optional[List[SearchServiceResult]]
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
    # Quiz generation tracking
    quiz_generation_enabled: Optional[bool]
    quiz_questions_by_submodule: Optional[Dict[str, List[QuizQuestion]]]
    quiz_generation_in_progress: Optional[Dict[str, bool]]
    quiz_generation_errors: Optional[Dict[str, str]]
    # Key provider references instead of direct API keys
    google_key_provider: Optional[Any]  # GoogleKeyProvider but avoiding import cycles
    pplx_key_provider: Optional[Any]    # PerplexityKeyProvider but avoiding import cycles
    brave_key_provider: Optional[Any]  # Changed TavilyKeyProvider reference to BraveKeyProvider
    # Optional token fields for reference
    google_key_token: Optional[str]
    pplx_key_token: Optional[str]
    brave_key_token: Optional[str] # Changed tavily_key_token to brave_key_token
    # Language settings
    language: Optional[str]  # ISO language code for content generation
    explanation_style: Optional[str] # Style for content explanations
    search_language: Optional[str]  # ISO language code for search queries
    # Other optional settings
    desired_module_count: Optional[int]
    desired_submodule_count: Optional[int]
    # Resource generation settings and tracking
    resource_generation_enabled: Optional[bool]  # Flag to enable/disable resource generation
    topic_resources: Optional[List[Resource]]  # Resources for the entire topic
    topic_resource_query: Optional[ResourceQuery]  # Query used for topic resources
    topic_resource_search_results: Optional[List[Dict[str, Any]]] # TODO: Refactor if topic resource search changes
    module_resources_in_process: Optional[Dict[int, Dict[str, Any]]]  # Tracking module resource generation
    submodule_resources_in_process: Optional[Dict[str, Dict[str, Any]]]  # Tracking submodule resource generation
    
# Enable forward references for EnhancedModule.submodules
EnhancedModule.model_rebuild()
SubmoduleList.model_rebuild()
