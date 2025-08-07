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

### 1. **Conceptual Relationship Mapping** (Most Critical)
Before creating any diagram, perform deep analysis to identify:
- **Knowledge Prerequisites**: Which concepts must be understood before others?
- **Skill Dependencies**: What abilities enable advancement to new topics?
- **Cross-Module Connections**: How do concepts from different modules reinforce each other?
- **Conceptual Bridges**: Where do modules share foundational principles or build upon each other?
- **Integration Points**: Where separate learning streams converge into unified understanding?
- **Practical Applications**: How theoretical modules connect to applied/practical modules?

### 2. **Learning Flow Discovery**
Identify the REAL learning pathways:
- **Parallel Tracks**: Can some modules be learned simultaneously?
- **Convergence Points**: Where do different learning paths meet and integrate?
- **Branching Opportunities**: Where can learners choose specialized directions?
- **Reinforcement Loops**: How do advanced concepts reinforce earlier learning?
- **Skills Transfer**: Where skills from one area enhance learning in another?

### 3. **Diagram Architecture Strategy**
Create diagrams that show RELATIONSHIPS, not just sequence:

**MANDATORY RELATIONSHIP TYPES TO IDENTIFY:**
- **Foundation Dependencies** (`A -.->|"builds on"| B`)
- **Skill Enablement** (`A -->|"enables"| B`) 
- **Conceptual Reinforcement** (`A <-->|"reinforces"| B`)
- **Knowledge Integration** (`A -->|"integrates with"| B`)
- **Practical Application** (`A -->|"applied in"| B`)
- **Cross-Pollination** (`A -.->|"enriches"| B`)

### 4. **Advanced Diagram Types Selection**
Choose based on course's TRUE structure:

**For Complex Interconnected Courses:**
- `graph TD/LR` - Shows rich bi-directional relationships and cross-connections
- `flowchart TD/LR` - For courses with clear decision points and multiple pathways

**For Skill-Building Courses:**
- `graph TD` with multiple connection types showing how skills compound and interact

**For Integrated Curricula:**
- `graph LR` showing how theoretical and practical streams run parallel and intersect

### 5. **Rich Labeling Strategy**
**Course Core** (1 node): Central organizing principle
**Knowledge Domains** (2-4 nodes): Major conceptual areas that may span multiple modules  
**Module Clusters** (5-8 nodes): Related modules grouped by shared foundations
**Integration Hubs** (2-3 nodes): Key points where learning streams converge
**Application Zones** (2-4 nodes): Where theoretical knowledge becomes practical skill

### 6. **Connection Semantics** (CRITICAL FOR NON-LINEAR VISUALIZATION)
Use MEANINGFUL edge labels that explain WHY things connect:
- `"requires foundation in"` - Prerequisites
- `"enhances understanding of"` - Enrichment  
- `"provides tools for"` - Skill enablement
- `"synthesizes with"` - Knowledge integration
- `"applied through"` - Theory-to-practice
- `"exemplified by"` - Concept illustration
- `"reinforced by"` - Learning reinforcement
- `"bridges to"` - Conceptual connections

### 7. **Visual Hierarchy Design**
**Tier 1 - Course Core** (Largest, most prominent)
**Tier 2 - Knowledge Domains** (Large, distinctive colors)
**Tier 3 - Module Clusters** (Medium, thematically colored)  
**Tier 4 - Integration Points** (Medium, connecting colors)
**Tier 5 - Applications** (Smaller, action-oriented colors)

### 8. **Multi-Dimensional Relationship Modeling**
**Sequential Flow**: `A --> B` (temporal progression)
**Prerequisite**: `A -.-> B` (foundational requirement)  
**Bidirectional**: `A <--> B` (mutual reinforcement)
**Enhancement**: `A -.->|"enriches"| B` (conceptual strengthening)
**Application**: `A -->|"applied in"| B` (theory-to-practice)

## ANALYSIS METHODOLOGY:

### Phase 1: Structure Decomposition
1. **Identify Core Concepts** in each module's description
2. **Map Knowledge Prerequisites** - what must be known first?
3. **Find Conceptual Overlaps** - where do modules share foundations?
4. **Locate Integration Points** - where do separate streams unite?

### Phase 2: Relationship Discovery
1. **Foundation Analysis**: Which modules provide groundwork for others?
2. **Skill Progression**: How do abilities build and compound?
3. **Cross-Fertilization**: Where do different areas enhance each other?
4. **Practical Synthesis**: How does theory become application?

### Phase 3: Learning Architecture Design
1. **Create Knowledge Clusters** around shared foundations
2. **Show Skill Building Chains** that span modules
3. **Highlight Integration Moments** where understanding unifies
4. **Reveal Alternative Pathways** for different learning styles

## ADVANCED EXAMPLE PATTERNS:

**Rich Interconnected Architecture:**
```
graph TD
    CORE["Course Core Concept"]
    
    %% Knowledge Domains
    THEORY["Theoretical Foundation"]
    METHODS["Methodological Framework"] 
    PRACTICE["Applied Practice"]
    
    %% Key Relationships
    CORE --> THEORY
    CORE --> METHODS
    THEORY -.->|"provides basis for"| METHODS
    THEORY -.->|"guides"| PRACTICE
    METHODS -->|"enables"| PRACTICE
    PRACTICE -->|"validates"| THEORY
    
    %% Module Integration
    M1["Foundation Module"] --> THEORY
    M2["Analysis Module"] --> METHODS  
    M3["Application Module"] --> PRACTICE
    M4["Synthesis Module"] 
    
    THEORY -.->|"reinforced by"| M4
    METHODS -.->|"unified in"| M4  
    PRACTICE -.->|"culminates in"| M4
    
    %% Cross-connections
    M1 -.->|"enables"| M2
    M1 -.->|"supports"| M3
    M2 <-->|"informs"| M3
    
    classDef core fill:#ff6b6b,stroke:#d63031,stroke-width:4px,color:#fff
    classDef domain fill:#4ecdc4,stroke:#00b894,stroke-width:3px,color:#fff  
    classDef module fill:#45b7d1,stroke:#2d3436,stroke-width:2px
    classDef synthesis fill:#f9ca24,stroke:#f0932b,stroke-width:3px
    
    class CORE core
    class THEORY,METHODS,PRACTICE domain
    class M1,M2,M3 module
    class M4 synthesis
```

**Skill-Building Network:**
```
graph LR
    FOUNDATION["Core Foundations"]
    
    %% Skill Streams  
    ANALYTICAL["Analytical Skills"] 
    CREATIVE["Creative Skills"]
    TECHNICAL["Technical Skills"]
    
    FOUNDATION -->|"enables"| ANALYTICAL
    FOUNDATION -->|"enables"| CREATIVE  
    FOUNDATION -->|"enables"| TECHNICAL
    
    %% Integration and Cross-Pollination
    ANALYTICAL <-->|"enhances"| CREATIVE
    CREATIVE <-->|"enriches"| TECHNICAL
    TECHNICAL -->|"supports"| ANALYTICAL
    
    %% Advanced Synthesis
    INTEGRATION["Advanced Integration"]
    ANALYTICAL -.->|"synthesizes in"| INTEGRATION
    CREATIVE -.->|"culminates in"| INTEGRATION
    TECHNICAL -.->|"applied through"| INTEGRATION
    
    classDef foundation fill:#6c5ce7,stroke:#5f3dc4,stroke-width:3px,color:#fff
    classDef skills fill:#00b894,stroke:#00a085,stroke-width:2px,color:#fff
    classDef integration fill:#e84393,stroke:#d63031,stroke-width:3px,color:#fff
    
    class FOUNDATION foundation
    class ANALYTICAL,CREATIVE,TECHNICAL skills  
    class INTEGRATION integration
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
   - Study the course structure to identify true conceptual relationships
   - Create diagrams that reveal learning architecture, not just sequence
   - Show HOW modules connect and reinforce each other
   - Use meaningful edge labels explaining WHY things relate
   - Establish clear visual hierarchy with different node types

Generate a diagram that reveals the TRUE INTELLECTUAL STRUCTURE of the course, showing rich interconnections and knowledge dependencies.

## Course Information:
**Course Topic:** "{course_topic}"

## Course Structure to Analyze:
---
{course_structure}
---

FINAL REMINDER: Output ONLY pure Mermaid.js syntax starting with "graph" or "flowchart", OR the JSON message for unsuitable content. NO other text allowed.
"""
