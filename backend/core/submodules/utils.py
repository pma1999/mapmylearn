import re
import json
from typing import Optional, Dict, Any


def extract_json_from_markdown(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from text that might be formatted as markdown code blocks.

    Args:
        text: The text that may contain markdown-formatted JSON

    Returns:
        Parsed JSON object or None if extraction failed
    """
    # First try to parse directly as JSON (in case it's already valid JSON)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code blocks
    code_block_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    matches = re.findall(code_block_pattern, text)

    # If we found code blocks, try each one
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    # If no code blocks or none contained valid JSON, try a more lenient approach
    # Look for text that appears to be JSON (starting with { and ending with })
    json_object_pattern = r'(\{[\s\S]*\})'
    object_matches = re.findall(json_object_pattern, text)

    for match in object_matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    # If we couldn't extract JSON, return None
    return None
