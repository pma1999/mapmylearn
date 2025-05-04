# Prompt System

This directory contains the prompt templates used throughout the course generation system.

## Overview

Prompts are extracted from the core functionality code to improve:
- Maintainability
- Reusability
- Readability
- Version control
- Testing

## Structure

- `learning_path_prompts.py`: Contains all prompt templates organized by function
- `prompt_registry.py`: A more advanced registry system for prompt management
- `__init__.py`: Package initialization

## Usage

### Basic Usage

Import prompt templates directly:

```python
from prompts.learning_path_prompts import SUBMODULE_PLANNING_PROMPT

# Use the template with langchain
prompt = ChatPromptTemplate.from_template(SUBMODULE_PLANNING_PROMPT)
```

### Advanced Usage with Registry

```python
from prompts.prompt_registry import registry

# Get a formatted prompt directly from the registry
formatted_prompt = registry.get_formatted("submodule_planning", 
    user_topic="Python Programming",
    module_title="Data Types",
    # other variables...
)

# Get all prompts in a category
research_prompts = registry.list_prompts(category="research")
```

## Adding New Prompts

1. Add the prompt template to `learning_path_prompts.py`
2. Register it in `prompt_registry.py` 
3. Add tests to verify its correctness

## Prompt Design Principles

All prompts should:
- Clearly indicate required variables with {variable_name} format
- Include version information
- Be organized by function/category
- Have descriptive naming
- Include instructions for the LLM

## Future Enhancements

- External prompt loading from YAML/JSON files
- A/B testing infrastructure
- Prompt versioning and rollback
- Prompt template inheritance 