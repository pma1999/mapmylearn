"""
Prompt registry for managing and accessing prompt templates.

This module provides a registry system for managing prompt templates,
allowing for easier version control, retrieval, and potential A/B testing.
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass
import importlib

@dataclass
class PromptTemplate:
    """A template for a prompt with metadata."""
    name: str
    template: str
    version: str
    description: str
    category: str
    
    def format(self, **kwargs: Any) -> str:
        """Format the prompt template with the provided variables."""
        return self.template.format(**kwargs)


class PromptRegistry:
    """Registry for managing and retrieving prompt templates."""
    
    def __init__(self):
        self._prompts: Dict[str, PromptTemplate] = {}
    
    def register(self, prompt: PromptTemplate) -> None:
        """Register a prompt template."""
        self._prompts[prompt.name] = prompt
    
    def get(self, name: str) -> Optional[PromptTemplate]:
        """Get a prompt template by name."""
        return self._prompts.get(name)
    
    def get_formatted(self, name: str, **kwargs: Any) -> str:
        """Get a formatted prompt by name."""
        prompt = self.get(name)
        if not prompt:
            raise KeyError(f"Prompt '{name}' not found in registry")
        return prompt.format(**kwargs)
    
    def list_prompts(self, category: Optional[str] = None) -> Dict[str, PromptTemplate]:
        """List all registered prompts, optionally filtered by category."""
        if category:
            return {k: v for k, v in self._prompts.items() if v.category == category}
        return self._prompts


# Global registry instance
registry = PromptRegistry()


def initialize_registry() -> None:
    """Initialize the registry with all prompts from the learning_path_prompts module."""
    from prompts.learning_path_prompts import (
        __version__,
        SUBMODULE_PLANNING_PROMPT,
        SUBMODULE_QUERY_GENERATION_PROMPT,
        SUBMODULE_CONTENT_DEVELOPMENT_PROMPT
    )
    
    registry.register(PromptTemplate(
        name="submodule_planning",
        template=SUBMODULE_PLANNING_PROMPT,
        version=__version__,
        description="Breaks down a learning module into logical submodules",
        category="planning"
    ))
    
    registry.register(PromptTemplate(
        name="submodule_query_generation",
        template=SUBMODULE_QUERY_GENERATION_PROMPT,
        version=__version__,
        description="Generates search queries for a submodule",
        category="research"
    ))
    
    registry.register(PromptTemplate(
        name="submodule_content_development",
        template=SUBMODULE_CONTENT_DEVELOPMENT_PROMPT,
        version=__version__,
        description="Develops comprehensive content for a submodule",
        category="content"
    ))


# Initialize the registry when this module is imported
initialize_registry() 