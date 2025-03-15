import logging
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("learning_path_generator")

@dataclass
class Submodule:
    """A submodule within a learning module."""
    title: str
    description: str

@dataclass
class Module:
    """A module in the learning path."""
    id: int
    title: str
    description: str

@dataclass
class EnhancedModule:
    """A module with planned submodules."""
    id: int
    title: str
    description: str
    submodules: List[Submodule] = field(default_factory=list)

@dataclass
class SubmoduleContent:
    """Content for a processed submodule."""
    id: int
    title: str
    content: str
    search_queries: List[str]
    search_results: List[Dict[str, Any]]

@dataclass
class CompletedModule:
    """A completely processed module with all its submodules."""
    id: int
    title: str
    description: str
    submodules: List[SubmoduleContent] = field(default_factory=list)

class LearningPathState:
    """
    State for the Learning Path Generator.
    Holds all data needed during the generation process.
    """
    
    def __init__(
        self, 
        user_topic: str, 
        llm=None, 
        search_tool=None,
        parallel_count: int = 2,
        progress_callback=None
    ):
        # Core data
        self.user_topic = user_topic
        self.llm = llm
        self.search_tool = search_tool
        self.progress_callback = progress_callback
        
        # Topic exploration 
        self.search_queries = []
        self.search_results = []
        
        # Module definition
        self.initial_modules = []
        self.enhanced_modules = []
        
        # Parallel processing parameters
        self.parallel_count = parallel_count
        self.module_batches = []
        self.current_batch_index = 0
        self.modules_in_parallel_process = {}
        
        # Output collection
        self.completed_modules = []
        self.finalized_learning_path = None
        
        # Tracking
        self.steps = [] 