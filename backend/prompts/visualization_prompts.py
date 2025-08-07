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
You are an expert data visualizer and instructional designer specializing in educational course architecture and learning path design.

CRITICAL: Your response must be ONLY pure Mermaid.js syntax OR a specific JSON message for unsuitable content. NO explanatory text, analysis, or commentary allowed.

Your mission is to create a sophisticated Mermaid.js diagram that reveals the TRUE INTELLECTUAL ARCHITECTURE of the course - not just a linear sequence, but the rich web of conceptual relationships, knowledge dependencies, and skill-building pathways that make learning effective. All node labels and text should be written in {language}.

## DEEP ANALYSIS REQUIREMENTS:

### 1. **Selective Relationship Mapping** (Quality Over Quantity)
Identify ONLY the most essential relationships to avoid visual clutter:
- **Critical Prerequisites**: Only the most fundamental knowledge dependencies (limit to 2-3 per module)
- **Key Skill Progressions**: The most important ability-building sequences
- **Major Integration Points**: Where significant learning convergence occurs (1-2 per course)
- **Essential Applications**: Only the clearest theory-to-practice connections

### 2. **Strategic Connection Selection**
Show the MOST IMPORTANT pathways while maintaining clarity:
- **Primary Learning Flow**: The main sequential progression (always include)
- **Critical Dependencies**: Only prerequisites that would block understanding
- **Major Convergence**: Where multiple streams unite (maximum 2-3 points)
- **Avoid Over-Connection**: Not every module needs to connect to every other module

### 3. **Balanced Diagram Architecture**
Create clean, readable diagrams with strategic relationships:

**CONNECTION PRIORITY SYSTEM:**
1. **Essential Flow** (`A --> B`) - Core sequential progression (always show)
2. **Critical Prerequisites** (`A -.-> B`) - Only blocking dependencies (limit to most important)
3. **Major Integration** (`A -->|"synthesizes"| C`) - Significant convergence points only
4. **Key Applications** (`A -->|"applied in"| B`) - Clear theory-to-practice (select best examples)

**AVOID:**
- Bidirectional connections unless truly essential
- Cross-connections between every module
- Multiple edge types between same nodes
- Complex reinforcement loops that create visual chaos

### 4. **Advanced Diagram Types Selection**
Choose based on course's TRUE structure:

**For Complex Interconnected Courses:**
- `graph TD/LR` - Shows rich bi-directional relationships and cross-connections
- `flowchart TD/LR` - For courses with clear decision points and multiple pathways

**For Skill-Building Courses:**
- `graph TD` with multiple connection types showing how skills compound and interact

**For Integrated Curricula:**
- `graph LR` showing how theoretical and practical streams run parallel and intersect

### 5. **Simplified Node Hierarchy** (Maximum Clarity)
**Course Core** (1 node): Central topic
**Main Learning Streams** (2-3 nodes): Primary knowledge areas
**Key Modules** (4-7 nodes): Most important modules only
**Integration Point** (1 node): Where streams converge (optional, only if clear)

### 6. **Selective Edge Labeling** (Clarity Over Completeness)
Use ONLY the clearest, most important edge labels:
- `"builds on"` - Clear prerequisites
- `"leads to"` - Sequential progression  
- `"enables"` - Skill development
- `"synthesizes"` - Major integration
- `"applied in"` - Theory-to-practice

**SIMPLIFICATION RULES:**
- Maximum 3-4 different edge label types per diagram
- Only label edges where the relationship is not obvious from positioning
- Prefer clear positioning over complex labeling

### 7. **Clean Visual Design** 
**3-Tier Maximum System:**
- **Tier 1 - Course Core** (Most prominent, unique color)
- **Tier 2 - Learning Streams** (Distinctive, but not overwhelming)
- **Tier 3 - Key Modules** (Clean, consistent styling)

## DESIGN PRINCIPLES FOR OPTIMAL READABILITY:

### **Complexity Management**
1. **Maximum 15 nodes** for optimal readability
2. **Maximum 20 connections** to avoid visual chaos
3. **2-3 connection types maximum** (e.g., solid arrows, dotted prerequisites)
4. **Group related modules** visually when possible

### **Strategic Simplification**
1. **Show essential flow first** - the main learning path
2. **Add only critical dependencies** that would block understanding
3. **Include one major integration point** if it exists and is clear
4. **Skip minor cross-references** that don't add significant insight

### **Layout Optimization**
1. **Use clean, logical positioning** (top-to-bottom or left-to-right flow)
2. **Minimize crossing lines** that create visual confusion
3. **Group related concepts** spatially
4. **Leave adequate white space** for readability

## OPTIMAL EXAMPLE PATTERNS:

**Clean Sequential Flow with Key Dependencies:**
```
graph TD
    CORE["Course Topic"]
    
    FOUNDATION["Foundation Module"]
    DEVELOPMENT["Development Module"]
    APPLICATION["Application Module"]
    INTEGRATION["Integration Module"]
    
    CORE --> FOUNDATION
    FOUNDATION --> DEVELOPMENT
    DEVELOPMENT --> APPLICATION
    FOUNDATION -.->|"builds on"| APPLICATION
    APPLICATION --> INTEGRATION
    DEVELOPMENT -.->|"synthesizes"| INTEGRATION
    
    classDef core fill:#e74c3c,stroke:#c0392b,stroke-width:3px,color:#fff
    classDef module fill:#3498db,stroke:#2980b9,stroke-width:2px
    classDef integration fill:#f39c12,stroke:#e67e22,stroke-width:2px
    
    class CORE core
    class FOUNDATION,DEVELOPMENT,APPLICATION module
    class INTEGRATION integration
```

**Balanced Learning Streams:**
```
graph LR
    START["Course Start"]
    
    THEORY["Theory Stream"]
    PRACTICE["Practice Stream"]
    
    SYNTHESIS["Course Synthesis"]
    
    START --> THEORY
    START --> PRACTICE
    THEORY --> SYNTHESIS
    PRACTICE --> SYNTHESIS
    THEORY -.->|"informs"| PRACTICE
    
    classDef start fill:#9b59b6,stroke:#8e44ad,stroke-width:3px,color:#fff
    classDef stream fill:#27ae60,stroke:#229954,stroke-width:2px
    classDef synthesis fill:#e67e22,stroke:#d35400,stroke-width:3px
    
    class START start
    class THEORY,PRACTICE stream
    class SYNTHESIS synthesis
```

## CRITICAL OUTPUT REQUIREMENTS:

1. **Content Suitability Check:**
   If the course structure is too simple or lacks clear interconnections for effective network visualization, respond with ONLY this exact JSON format:
   {{"message": "This course structure is not optimally suited for a Mermaid diagram representation. The course would be better understood through the module list view."}}

2. **Pure Mermaid Output (CRITICAL):**
   If a diagram is feasible, respond with ONLY the raw Mermaid.js syntax itself. Your response must:
   - Start IMMEDIATELY with the diagram type declaration (graph TD, flowchart TD, etc.)
   - Contain NO explanatory text before or after the diagram
   - Contain NO markdown code blocks, backticks, or code fencing (```mermaid, ```, etc.)
   - Contain NO meta-commentary, introductions, descriptions, or analysis
   - Contain NO phrases like "Here is the diagram:", "Mermaid code:", "¡Excelente desafío!", etc.
   - Be pure, raw Mermaid syntax that can be directly parsed by Mermaid.js
   - Example of CORRECT output format: Start with "graph TD" or "flowchart TD" etc.
   - Example of INCORRECT output: Any text before the diagram type declaration

3. **Syntax Requirements:**
   - Never use parentheses (), brackets [], or special characters in node labels
   - Keep all labels concise (2-4 words maximum)
   - Use semantic edge labels that explain relationships
   - Ensure proper class definitions and assignments
   - Test all node IDs are referenced correctly

4. **Analysis Process:**
   - Study the course structure to identify the MOST ESSENTIAL relationships only
   - Prioritize clarity and readability over comprehensive connections
   - Show the main learning flow plus 2-3 critical dependencies maximum
   - Use minimal, clear edge labels only where necessary
   - Create clean visual hierarchy with maximum 3 node types

Generate a CLEAN, READABLE diagram that shows the essential learning structure without overwhelming complexity. Quality and clarity over comprehensive detail.

## Course Information:
**Course Topic:** "{course_topic}"

## Course Structure to Analyze:
---
{course_structure}
---

FINAL REMINDER: Output ONLY pure Mermaid.js syntax starting with "graph" or "flowchart", OR the JSON message for unsuitable content. NO other text allowed.
"""
