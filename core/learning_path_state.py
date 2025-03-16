import logging
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field

# These dataclasses represent legacy state structures for module/submodule processing.
# The main execution uses the TypedDict from models.
logger = logging.getLogger("learning_path_state")

@dataclass
class Submodule:
    title: str
    description: str

@dataclass
class Module:
    id: int
    title: str
    description: str

@dataclass
class EnhancedModule:
    id: int
    title: str
    description: str
    submodules: List[Submodule] = field(default_factory=list)

@dataclass
class SubmoduleContent:
    id: int
    title: str
    content: str
    search_queries: List[str]
    search_results: List[Dict[str, Any]]

@dataclass
class CompletedModule:
    id: int
    title: str
    description: str
    submodules: List[SubmoduleContent] = field(default_factory=list)

class LearningPathState:
    """
    Legacy state class for learning path generation.
    The current implementation uses a TypedDict defined in models.
    """
    def __init__(
        self, 
        user_topic: str, 
        llm=None, 
        search_tool=None,
        parallel_count: int = 2,
        progress_callback: Optional[Callable] = None
    ):
        self.user_topic = user_topic
        self.llm = llm
        self.search_tool = search_tool
        self.progress_callback = progress_callback
        self.search_queries = []
        self.search_results = []
        self.initial_modules = []
        self.enhanced_modules = []
        self.parallel_count = parallel_count
        self.module_batches = []
        self.current_batch_index = 0
        self.modules_in_parallel_process = {}
        self.completed_modules = []
        self.finalized_learning_path = None
        self.steps = []
