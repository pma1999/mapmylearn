"""
Visualization prompt templates for interactive diagram generation.

This module contains prompts used to generate Mermaid.js syntax
for interactive visualizations of submodule content.
"""

MERMAID_VISUALIZATION_PROMPT = """\
You are an expert data visualizer and instructional designer specializing in educational diagrams.

Your task is to analyze the following submodule content and generate Mermaid.js syntax for an interactive and insightful diagram that visually represents the key concepts, relationships, processes, or structures within the content. The diagram should be as visually appealing and impactful as possible within Mermaid's capabilities.

## Submodule Information:
**Title:** "{submodule_title}"
**Description:** "{submodule_description}"

## Content to Visualize:
---
{submodule_content}
---

## Instructions:

1. **Content Analysis:** Carefully analyze the provided content to identify the most salient information that can be effectively visualized. Look for:
   - Key concepts and their relationships
   - Processes or workflows
   - Hierarchical structures
   - Cause-and-effect relationships
   - Temporal sequences
   - Classifications or categories

2. **Diagram Type Selection:** Choose the MOST SUITABLE Mermaid diagram type:
   - `flowchart TD/LR` - For processes, workflows, decision trees
   - `graph TD/LR` - For concept relationships and hierarchies
   - `sequenceDiagram` - For interactions, communications, temporal sequences
   - `classDiagram` - For structural relationships, object models
   - `stateDiagram-v2` - For state changes, lifecycle processes
   - `mindmap` - For conceptual breakdowns and idea relationships
   - `timeline` - For chronological events and historical progressions
   - `gitgraph` - For branching processes or parallel developments
   - `pie` - For proportional data or category distributions

3. **Syntax Requirements:**
   - Generate valid and complete Mermaid.js syntax
   - Use descriptive and concise labels for all nodes and edges. **Labels should be short enough to fit comfortably within typical node shapes without truncation. If a concept is too long for a single node, consider breaking it into multiple linked nodes or using abbreviations where clear.**
   - Ensure proper syntax formatting and indentation
   - Include styling where appropriate to enhance visual appeal
   - Use meaningful node IDs and connection syntax

4. **Visual Enhancement:**
   - Apply consistent styling using classDef when beneficial
   - Use appropriate node shapes (rectangles, circles, diamonds, etc.)
   - Consider color coding for different types of concepts
   - Ensure the diagram is well-organized and easy to follow

5. **Content Suitability Check:**
   If the content is primarily abstract text without clear relationships, processes, or structures that would benefit from diagrammatic representation, respond with ONLY this JSON:
   {{"message": "This content is not optimally suited for a Mermaid diagram representation. The material would be better understood through text-based learning."}}

6. **Output Format:**
   If a diagram is feasible, respond with ONLY the Mermaid syntax itself, starting directly with the diagram type declaration. Do NOT include:
   - Explanatory text before or after
   - Markdown code blocks like ```mermaid
   - Additional commentary or descriptions

## Example Output Formats:

**For Process/Workflow Content:**
```
flowchart TD
    A["Problem Identification"] --> B{{"Analyze Requirements"}}
    B --> C["Design Solution"]
    B --> D["Research Alternatives"]
    C --> E["Implementation"]
    D --> E
    E --> F["Testing & Validation"]
    F --> G["Deployment"]
    
    classDef startEnd fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef process fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef decision fill:#fff3e0,stroke:#e65100,stroke-width:2px
    
    class A,G startEnd
    class C,D,E,F process
    class B decision
```

**For Concept Relationships:**
```
graph TD
    A["Central Concept"] --> B["Key Principle 1"]
    A --> C["Key Principle 2"]
    A --> D["Key Principle 3"]
    B --> E["Application 1"]
    B --> F["Application 2"]
    C --> G["Real-world Example"]
    D --> H["Related Theory"]
    
    classDef central fill:#ffeb3b,stroke:#f57f17,stroke-width:3px
    classDef principle fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef application fill:#ffcdd2,stroke:#c62828,stroke-width:2px
    
    class A central
    class B,C,D principle
    class E,F,G,H application
```

Generate a diagram that is "impactante" (impactful) and "perfecta" (perfect) in conveying insights about the submodule content.
""" 