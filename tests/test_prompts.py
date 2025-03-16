"""
Tests for the prompt extraction implementation.
"""

import unittest
from prompts.learning_path_prompts import (
    SUBMODULE_PLANNING_PROMPT,
    SUBMODULE_QUERY_GENERATION_PROMPT,
    SUBMODULE_CONTENT_DEVELOPMENT_PROMPT
)
from prompts.prompt_registry import registry, PromptTemplate


class TestPromptExtraction(unittest.TestCase):
    """Test the prompt extraction implementation."""
    
    def test_prompt_content(self):
        """Test that all prompt templates contain expected content markers."""
        self.assertIn("EXPERT TEACHING ASSISTANT INSTRUCTIONS", SUBMODULE_PLANNING_PROMPT)
        self.assertIn("MODULE INFORMATION", SUBMODULE_PLANNING_PROMPT)
        
        self.assertIn("expert research assistant", SUBMODULE_QUERY_GENERATION_PROMPT)
        self.assertIn("exactly 5 search queries", SUBMODULE_QUERY_GENERATION_PROMPT)
        
        self.assertIn("EXPERT TEACHING ASSISTANT INSTRUCTIONS", SUBMODULE_CONTENT_DEVELOPMENT_PROMPT)
        self.assertIn("MODULE CLOSURE", SUBMODULE_CONTENT_DEVELOPMENT_PROMPT)
    
    def test_prompt_registry(self):
        """Test that the prompt registry contains all expected prompts."""
        # Check that all prompts are registered
        self.assertIsNotNone(registry.get("submodule_planning"))
        self.assertIsNotNone(registry.get("submodule_query_generation"))
        self.assertIsNotNone(registry.get("submodule_content_development"))
        
        # Check categories
        planning_prompts = registry.list_prompts(category="planning")
        self.assertEqual(len(planning_prompts), 1)
        self.assertIn("submodule_planning", planning_prompts)
        
        research_prompts = registry.list_prompts(category="research")
        self.assertEqual(len(research_prompts), 1)
        self.assertIn("submodule_query_generation", research_prompts)
        
        content_prompts = registry.list_prompts(category="content")
        self.assertEqual(len(content_prompts), 1)
        self.assertIn("submodule_content_development", content_prompts)
    
    def test_prompt_formatting(self):
        """Test that prompts can be formatted correctly."""
        test_data = {
            "user_topic": "Python Programming",
            "module_title": "Object-Oriented Programming",
            "module_description": "Learn about classes and objects",
            "format_instructions": "Return JSON"
        }
        
        # Test direct formatting
        formatted = SUBMODULE_PLANNING_PROMPT.format(**test_data)
        self.assertIn("Python Programming", formatted)
        self.assertIn("Object-Oriented Programming", formatted)
        
        # Test registry formatting
        registry_formatted = registry.get_formatted("submodule_planning", **test_data)
        self.assertEqual(formatted, registry_formatted)


if __name__ == "__main__":
    unittest.main() 