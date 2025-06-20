import logging
import json
import asyncio
from typing import Dict, Optional, Any

from backend.services.services import get_llm
from backend.prompts.visualization_prompts import MERMAID_VISUALIZATION_PROMPT
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

async def generate_mermaid_visualization(
    submodule_title: str,
    submodule_description: str,
    submodule_content: str,
    language: str,
    google_key_provider: Optional[Any] = None,
    user: Optional[Any] = None  # Add user parameter for model selection
) -> Dict[str, Optional[str]]:
    """
    Generates Mermaid.js syntax for a submodule using an LLM.
    
    Args:
        submodule_title: The title of the submodule
        submodule_description: The description of the submodule  
        submodule_content: The main content of the submodule
        language: Target language for diagram labels (ISO code)
        google_key_provider: Optional key provider for Google API
        user: Optional user parameter for model selection
        
    Returns:
        Dictionary containing either:
        - {"mermaid_syntax": str, "message": None} for successful generation
        - {"mermaid_syntax": None, "message": str} for unsuitable content or errors
    """
    try:
        # Get LLM instance
        llm = await get_llm(google_key_provider, user=user)
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_template(MERMAID_VISUALIZATION_PROMPT)
        
        # Create processing chain
        chain = prompt | llm | StrOutputParser()

        logger.info(f"Requesting Mermaid visualization from LLM for submodule: {submodule_title}")
        
        # Generate response
        from backend.utils.language_utils import get_full_language_name
        language_name = get_full_language_name(language)
        response_text = await chain.ainvoke({
            "submodule_title": submodule_title,
            "submodule_description": submodule_description or "No description provided",
            "submodule_content": submodule_content[:15000],  # Limit content length for LLM
            "language": language_name,
        })

        # Try to parse as JSON first (for "not suitable" message)
        try:
            json_response = json.loads(response_text.strip())
            if "message" in json_response:
                logger.info(f"LLM indicated content not suitable for Mermaid: {json_response['message']}")
                return {"mermaid_syntax": None, "message": json_response["message"]}
        except json.JSONDecodeError:
            # Not JSON, assume it's Mermaid syntax
            pass

        # Clean and validate Mermaid syntax
        response_cleaned = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_cleaned.startswith("```mermaid"):
            # Extract content between ```mermaid and ```
            lines = response_cleaned.split('\n')
            if len(lines) > 1:
                # Remove first line (```mermaid) and last line if it's just ```
                start_index = 1
                end_index = len(lines)
                
                # Check if last line is just ```
                if lines[-1].strip() == "```":
                    end_index = -1
                
                # Extract the actual Mermaid content
                mermaid_lines = lines[start_index:end_index]
                response_cleaned = '\n'.join(mermaid_lines).strip()
        elif response_cleaned.startswith("```"):
            # Handle generic code blocks
            lines = response_cleaned.split('\n')
            if len(lines) > 1:
                start_index = 1
                end_index = len(lines)
                if lines[-1].strip() == "```":
                    end_index = -1
                mermaid_lines = lines[start_index:end_index]
                response_cleaned = '\n'.join(mermaid_lines).strip()
        
        # Check if response starts with known Mermaid diagram types
        mermaid_keywords = [
            "graph", "flowchart", "sequenceDiagram", "classDiagram", 
            "stateDiagram", "stateDiagram-v2", "gantt", "pie", 
            "mindmap", "timeline", "gitgraph", "journey", "quadrantChart",
            "subgraph"  # Add subgraph as it can also start diagrams
        ]
        
        if any(response_cleaned.startswith(keyword) for keyword in mermaid_keywords):
            logger.info(f"LLM returned valid Mermaid syntax for: {submodule_title}")
            return {"mermaid_syntax": response_cleaned, "message": None}
        else:
            logger.warning(f"LLM response for {submodule_title} doesn't start with recognized Mermaid syntax: {response_cleaned[:200]}...")
            return {
                "mermaid_syntax": None, 
                "message": "Generated content doesn't appear to be valid Mermaid syntax. The content might be unsuitable for visualization."
            }

    except asyncio.TimeoutError:
        logger.error(f"Timeout generating Mermaid visualization for {submodule_title}")
        return {"mermaid_syntax": None, "message": "Visualization generation timed out. Please try again."}
    
    except Exception as e:
        logger.exception(f"Error generating Mermaid visualization for {submodule_title}: {e}")
        return {"mermaid_syntax": None, "message": "An error occurred while generating the visualization. Please try again later."}


def validate_mermaid_syntax(mermaid_code: str) -> bool:
    """
    Basic validation of Mermaid syntax.
    
    Args:
        mermaid_code: The Mermaid code to validate
        
    Returns:
        True if the syntax appears valid, False otherwise
    """
    if not mermaid_code or not isinstance(mermaid_code, str):
        return False
    
    # Remove comments and empty lines
    lines = [line.strip() for line in mermaid_code.split('\n') if line.strip() and not line.strip().startswith('%%')]
    
    if not lines:
        return False
    
    # Check if first line is a valid diagram declaration
    first_line = lines[0].lower()
    valid_declarations = [
        'graph', 'flowchart', 'sequencediagram', 'classdiagram', 
        'statediagram', 'gantt', 'pie', 'mindmap', 'timeline', 'gitgraph'
    ]
    
    return any(first_line.startswith(decl) for decl in valid_declarations) 