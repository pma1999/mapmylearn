"""
Visualization prompt templates for interactive diagram generation.

This module contains prompts used to generate Mermaid.js syntax
for interactive visualizations of submodule content.
"""

MERMAID_VISUALIZATION_PROMPT = """\
You are an expert data visualizer and instructional designer specializing in educational diagrams.

Your task is to generate Mermaid.js syntax for an interactive and intuitive diagram. Follow these guidelines closely before analyzing the submodule content. All node labels and text should be written in {language}.

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

## Submodule Information:
**Title:** "{submodule_title}"
**Description:** "{submodule_description}"

## Content to Visualize:
---
{submodule_content}
---
"""

COURSE_MERMAID_VISUALIZATION_PROMPT = """\
You are an expert data visualizer and instructional designer specializing in educational course overviews.

Your task is to generate Mermaid.js syntax for an interactive course overview diagram that shows the complete learning path structure. Follow these guidelines closely. All node labels and text should be written in {language}.

## Instructions:

1. **Course Structure Analysis:** Analyze the provided course structure to create a comprehensive learning path visualization showing:
   - Course topic/title as the central element
   - Module progression and relationships
   - Key submodules within each module
   - Prerequisites and dependencies between modules
   - Learning flow and pathways

2. **Diagram Type Selection:** Choose the MOST SUITABLE Mermaid diagram type for course overview:
   - `flowchart TD/LR` - For learning progression and pathways
   - `graph TD/LR` - For module relationships and hierarchies
   - `mindmap` - For conceptual course breakdown
   - `timeline` - For sequential learning progression
   - `gitgraph` - For branching learning paths

3. **Complexity Guidelines:**
   - Show the overall course structure (keep it high-level)
   - Maximum 20-25 nodes for clarity
   - Include main modules and select key submodules
   - Show learning progression and dependencies
   - Maintain visual balance and readability

4. **Node and Label Guidelines:**
   - **Node IDs**: Use simple alphanumeric IDs (COURSE, M1, M2, S1_1, etc.)
   - **Course Title**: Central prominent node
   - **Module Labels**: Keep concise (2-4 words max): "Module 1: Basics"
   - **Submodule Labels**: Very short (1-3 words): "Introduction", "Practice"
   - **Avoid Special Characters**: Do NOT use parentheses (), brackets [], or other special characters
   - **Label Format**: Use quotes for multi-word labels: `M1["Module 1 Basics"]`

5. **Course-Specific Guidelines:**
   - **Start with Course Topic**: Central node representing the entire course
   - **Show Module Progression**: Clear flow from one module to the next
   - **Highlight Prerequisites**: Use different styling for prerequisite relationships
   - **Include Key Submodules**: Select 1-3 most important submodules per module
   - **Show Learning Paths**: Multiple routes through the course if applicable

6. **Edge and Connection Guidelines:**
   - **Learning Flow**: Use `A --> B` for sequential learning
   - **Prerequisites**: Use `A -.-> B` for prerequisite relationships
   - **Edge Labels**: Use descriptive labels like "requires", "builds on", "leads to"
   - **Branching**: Show alternative learning paths where applicable

7. **Styling Guidelines:**
   - **Course Topic**: Distinctive styling (larger, different color)
   - **Modules**: Consistent styling for main modules
   - **Submodules**: Lighter styling, smaller nodes
   - **Prerequisites**: Different line style (dotted/dashed)
   - Use 3-4 different node classes maximum

8. **Content Suitability Check:**
   If the course structure is too simple or complex for effective visualization, respond with ONLY this JSON:
   {{"message": "This course structure is not optimally suited for a Mermaid diagram representation. The course would be better understood through the module list view."}}

9. **Output Format:**
   If a diagram is feasible, respond with ONLY the Mermaid syntax itself, starting directly with the diagram type declaration.

## Example Output Format:

**For Sequential Course Structure:**
```
flowchart TD
    COURSE["Course Topic"] --> M1["Module 1 Introduction"]
    M1 --> S1_1["Basics"]
    M1 --> S1_2["Concepts"]
    S1_1 --> M2["Module 2 Intermediate"]
    S1_2 --> M2
    M2 --> S2_1["Practice"]
    M2 --> S2_2["Applications"]
    S2_1 --> M3["Module 3 Advanced"]
    S2_2 --> M3
    M3 --> S3_1["Projects"]
    M3 --> S3_2["Mastery"]
    
    classDef course fill:#ff9800,stroke:#e65100,stroke-width:3px,color:#fff
    classDef module fill:#2196f3,stroke:#1976d2,stroke-width:2px,color:#fff
    classDef submodule fill:#4caf50,stroke:#388e3c,stroke-width:1px
    
    class COURSE course
    class M1,M2,M3 module
    class S1_1,S1_2,S2_1,S2_2,S3_1,S3_2 submodule
```

**For Branching Course Structure:**
```
graph TD
    COURSE["Course Topic"] --> FOUNDATION["Foundation"]
    FOUNDATION --> M1["Track A"]
    FOUNDATION --> M2["Track B"]
    M1 --> S1_1["Concepts A"]
    M1 --> S1_2["Practice A"]
    M2 --> S2_1["Concepts B"]
    M2 --> S2_2["Practice B"]
    S1_1 -.-> M3["Integration"]
    S2_1 -.-> M3
    M3 --> FINAL["Final Project"]
    
    classDef course fill:#ff5722,stroke:#d84315,stroke-width:3px,color:#fff
    classDef foundation fill:#9c27b0,stroke:#7b1fa2,stroke-width:2px,color:#fff
    classDef track fill:#2196f3,stroke:#1976d2,stroke-width:2px
    classDef submodule fill:#4caf50,stroke:#388e3c,stroke-width:1px
    
    class COURSE course
    class FOUNDATION foundation
    class M1,M2,M3 track
    class S1_1,S1_2,S2_1,S2_2,FINAL submodule
```

**CRITICAL RULES:**
1. Never use parentheses () or brackets [] inside node labels
2. Keep all labels simple and short
3. Show clear learning progression
4. Highlight the course structure and main learning path
5. Include only the most essential submodules for clarity

Generate a course overview diagram that effectively shows the learning journey and course structure.

## Course Information:
**Course Topic:** "{course_topic}"

## Course Structure:
---
{course_structure}
---
"""
