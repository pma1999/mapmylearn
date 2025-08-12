from pydantic import BaseModel, Field, HttpUrl, AliasChoices
from typing import List, Dict, Any, Optional, TypedDict, Annotated, Callable, TYPE_CHECKING, Tuple
import operator
from typing import Literal

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

class ResourceSelection(BaseModel):
    """LLM-selected resource referencing a scraped source by ID."""
    id: int = Field(..., description="Identifier of the scraped source")
    title: str = Field(..., description="Title of the resource")
    description: str = Field(..., description="Description of what the resource offers")
    type: str = Field(..., description="Type of resource (article, video, book, course, code, etc.)")

class ResourceSelectionList(BaseModel):
    resources: List[ResourceSelection] = Field(default_factory=list, description="List of selected resources by ID")

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
    text: str = Field(validation_alias=AliasChoices('text', 'text_content'))
    is_correct: bool

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

# Models for Search Service results (e.g., Brave Search + Scraper or Google Search Native)
class ScrapedResult(BaseModel):
    title: Optional[str] = Field(default=None, description="Title of the web page")
    url: str = Field(..., description="URL of the scraped page")
    search_snippet: Optional[str] = Field(default=None, description="Original snippet from search result (e.g., Brave)")
    scraped_content: Optional[str] = Field(default=None, description="Cleaned textual content scraped from the URL")
    scrape_error: Optional[str] = Field(default=None, description="Error message if scraping failed for this URL")

class GoogleSearchMetadata(BaseModel):
    """Metadata from Google Search native grounding"""
    grounding_chunks: List[Dict[str, Any]] = Field(default_factory=list, description="Google Search grounding chunks with web sources")
    web_search_queries: List[str] = Field(default_factory=list, description="Search queries executed by Google Search")
    search_entry_point: Optional[Dict[str, Any]] = Field(default=None, description="Search entry point metadata")
    grounding_sources: int = Field(default=0, description="Number of grounding sources found")

class SearchServiceResult(BaseModel):
    query: str = Field(..., description="The original search query performed")
    results: List[ScrapedResult] = Field(default_factory=list, description="List of scraped results for the query")
    search_provider_error: Optional[str] = Field(default=None, description="Error from the search provider API (e.g., Brave)")
    # New fields for Google Search native support
    grounding_metadata: Optional[GoogleSearchMetadata] = Field(default=None, description="Google Search grounding metadata for premium users")
    is_native_google_search: bool = Field(default=False, description="Whether this used native Google Search instead of Brave+scraping")
    native_response_content: Optional[str] = Field(default=None, description="Content generated by Google Search native when applicable")

# Research Evaluation Models (for self-reflection loop following Google pattern)
class ResearchEvaluation(BaseModel):
    is_sufficient: bool = Field(..., description="Whether current research is sufficient for quality course planning")
    knowledge_gaps: List[str] = Field(default_factory=list, description="Specific areas needing deeper research")
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5, description="Confidence in research completeness (0.0-1.0)")
    rationale: str = Field(..., description="Detailed explanation of the sufficiency assessment")

class RefinementQueryList(BaseModel):
    queries: List[SearchQuery] = Field(..., description="Follow-up search queries to address knowledge gaps")
    targeting_strategy: str = Field(..., description="Strategy for targeting identified knowledge gaps")

# Content Evaluation Models (for content refinement loop following Google pattern)
class ContentEvaluation(BaseModel):
    is_sufficient: bool = Field(..., description="Whether content meets quality standards for educational effectiveness")
    content_gaps: List[str] = Field(default_factory=list, description="Specific content deficiencies and missing elements")
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5, description="Quality confidence score (0.0-1.0)")
    improvement_areas: List[str] = Field(default_factory=list, description="Areas needing enhancement or clarification")
    depth_assessment: str = Field(..., description="Analysis of content depth and technical coverage")
    clarity_assessment: str = Field(..., description="Analysis of content clarity and accessibility")
    rationale: str = Field(..., description="Detailed evaluation reasoning and quality analysis")

class ContentRefinementQueryList(BaseModel):
    queries: List[SearchQuery] = Field(..., description="Targeted queries for content improvement and gap filling")
    targeting_strategy: str = Field(..., description="Strategy for addressing identified content gaps")
    focus_areas: List[str] = Field(..., description="Specific content areas being targeted for enhancement")

# Curiosity Items for Loading Screen
class CuriosityItem(BaseModel):
    text: str = Field(..., description="Concise, high-signal curiosity text in the output language")
    category: Literal[
        "fun_fact",
        "key_insight",
        "best_practice",
        "common_pitfall",
        "myth_buster",
        "historical_context",
        "practical_tip",
        "advanced_nugget"
    ] = Field(..., description="Category of the curiosity item")

class CuriosityItemList(BaseModel):
    items: List[CuriosityItem] = Field(default_factory=list, description="List of curiosity items for the loading screen")

# Global State for the Graph (TypedDict)
class LearningPathState(TypedDict):
    user_topic: str
    user: Optional[Any]  # User object for model selection
    topic_analysis: Optional[TopicAnalysis]
    module_planning: Optional[ModulePlanning]
    search_queries: Annotated[List[SearchQuery], operator.add]  # Changed to accumulative for research loop
    search_results: Annotated[List[SearchServiceResult], operator.add]  # Changed to accumulative for research loop
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
    # Research evaluation loop control (following Google pattern)
    research_loop_count: Optional[int]  # Counter for research iterations
    max_research_loops: Optional[int]  # Maximum allowed research iterations (default 3)
    is_research_sufficient: Optional[bool]  # Whether research is deemed sufficient
    research_knowledge_gaps: Optional[List[str]]  # Identified knowledge gaps
    research_confidence_score: Optional[float]  # Confidence in current research (0.0-1.0)
    refinement_queries: Optional[List[SearchQuery]]  # Queries generated to address gaps
    # Content evaluation loop control (following Google pattern for content refinement)
    content_search_queries: Annotated[List[SearchQuery], operator.add]  # Accumulative content search queries
    content_search_results: Annotated[List[SearchServiceResult], operator.add]  # Accumulative content search results
    content_loop_count: Optional[int]  # Counter for content refinement iterations
    max_content_loops: Optional[int]  # Maximum allowed content refinement iterations (default 2)
    is_content_sufficient: Optional[bool]  # Whether content quality is deemed sufficient
    content_gaps: Optional[List[str]]  # Identified content gaps and deficiencies
    content_confidence_score: Optional[float]  # Confidence in content quality (0.0-1.0)
    content_refinement_queries: Optional[List[SearchQuery]]  # Queries generated for content improvement
    # Planning loop configuration (module-level iterative planning)
    max_planning_loops: Optional[int]
    planning_min_confidence: Optional[float]
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
    # Curiosities generation tracking
    curiosities_generation_started: Optional[bool]
    
# Enable forward references for EnhancedModule.submodules
# Pydantic <2 uses `update_forward_refs` while >=2 uses `model_rebuild`
if hasattr(EnhancedModule, "model_rebuild"):
    EnhancedModule.model_rebuild()
    SubmoduleList.model_rebuild()
else:  # pragma: no cover - compatibility for older Pydantic versions
    EnhancedModule.update_forward_refs()
    SubmoduleList.update_forward_refs()
