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

3. **Complexity Guidelines:**
   - Keep diagrams focused and concise (maximum 15-20 nodes)
   - Use clear, short labels that fit comfortably in nodes
   - Avoid overly complex styling that might cause parsing issues
   - Ensure all syntax elements are complete and properly closed

4. **Node and Label Guidelines:**
   - **Node IDs**: Use simple alphanumeric IDs (A, B, C1, START, etc.)
   - **Node Labels**: Keep labels short (2-4 words max)
   - **Avoid Special Characters**: Do NOT use parentheses (), brackets [], or other special characters in node labels
   - **Use Simple Text**: Replace special characters with simple alternatives:
     * Instead of "Agustín (Maduro)" use "Agustín Maduro" or "Agustín Adulto"
     * Instead of "Contra Academicos" use "Contra Academicos" (avoid italics/formatting)
   - **Avoid List Numbering**: Do NOT start labels with numerals followed by a period ("1. Item"); use formats like "1 - Item" or "1) Item" if numbering is needed
   - **Label Format**: Use quotes for multi-word labels: `A["Simple Label"]`

5. **Edge and Connection Guidelines:**
   - **Simple Connections**: Use `A --> B` for basic connections
   - **Edge Text**: Use `A --"Text"--> B` format with quotes around edge text
   - **Avoid Complex Combinations**: Don't mix complex node labels with edge text
   - **Test Readability**: Ensure all connections are clear and unambiguous

6. **Styling Guidelines:**
   - Use simple, consistent styling with classDef
   - Limit to 3-5 different node classes maximum
   - Always ensure class assignments are complete: `class nodeId className`
   - Test that all referenced classes are properly defined

7. **Content Suitability Check:**
   If the content is primarily abstract text without clear relationships, processes, or structures that would benefit from diagrammatic representation, respond with ONLY this JSON:
   {{"message": "This content is not optimally suited for a Mermaid diagram representation. The material would be better understood through text-based learning."}}

8. **Output Format:**
   If a diagram is feasible, respond with ONLY the Mermaid syntax itself, starting directly with the diagram type declaration. Do NOT include:
   - Explanatory text before or after
   - Markdown code blocks like ```mermaid
   - Additional commentary or descriptions
   - Incomplete syntax elements

## Example Output Formats:

**For Process/Workflow Content:**
```
flowchart TD
    A["Problem Identification"] --> B{{"Analyze Requirements"}}
    B --> C["Design Solution"]
    B --> D["Research Alternatives"]
    C --> E["Implementation"]
    D --> E
    E --> F["Testing"]
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
    A["Central Concept"] --> B["Principle 1"]
    A --> C["Principle 2"]
    A --> D["Principle 3"]
    B --> E["Application A"]
    B --> F["Application B"]
    C --> G["Example"]
    D --> H["Theory"]
    
    classDef central fill:#ffeb3b,stroke:#f57f17,stroke-width:3px
    classDef principle fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef application fill:#ffcdd2,stroke:#c62828,stroke-width:2px
    
    class A central
    class B,C,D principle
    class E,F,G,H application
```

**For Historical/Temporal Content:**
```
graph TD
    A["Early Period"] --"Influenced by"--> B["Key Figure"]
    B --"Developed"--> C["Major Work"]
    C --"Led to"--> D["New Theory"]
    D --> E["Modern Impact"]
    
    classDef period fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef person fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef work fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    
    class A,E period
    class B person
    class C,D work
```

**CRITICAL RULES:**
1. Never use parentheses () or brackets [] inside node labels
2. Keep all labels simple and short
3. Ensure every class definition line includes both the node ID and the class name
4. Test that all node IDs are referenced correctly in edges
5. Avoid complex formatting or special characters

Generate a diagram that is impactful and perfect in conveying insights about the submodule content while maintaining strict syntactic correctness.
""" 