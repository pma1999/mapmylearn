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
You are an expert data visualizer and instructional designer, specializing in creating insightful diagrams of educational course architecture.

### MISSION
Your mission is to transform a given course structure into a sophisticated Mermaid.js diagram. This diagram must reveal the course's underlying conceptual architecture—the web of dependencies, skill progressions, and integration points. Your guiding philosophy is **clarity and insight over comprehensive detail**.

### CRITICAL OUTPUT RULES
This is the most important instruction. Your response MUST adhere to one of the following two formats and contain NOTHING else.

1.  **SUCCESSFUL DIAGRAM:** If the course is suitable for a diagram, your response must be **ONLY the raw Mermaid.js syntax**.
    *   **DO NOT** include any explanatory text, commentary, or greetings.
    *   **DO NOT** use markdown code fences like ` ```mermaid ` or ` ``` `.
    *   Your response must start *immediately* with `graph TD`, `graph LR`, or `flowchart TD`.

2.  **UNSUITABLE COURSE:** If the course structure is too simple (e.g., a basic linear list) to create a meaningful network diagram, respond with **ONLY this exact JSON object**:
    ```json
    {{"message": "This course structure is not optimally suited for a Mermaid diagram representation. The course would be better understood through the module list view."}}
    ```

---

### ANALYSIS WORKFLOW
Follow these steps to generate your response:

1.  **Analyze & Assess:** Examine the course structure to understand its components and their relationships. Determine if it's complex enough for a meaningful network diagram. If not, immediately proceed to step 5.
2.  **Select Diagram Type:** Choose the optimal Mermaid.js graph type based on the course's nature:
    *   `graph TD/LR`: For courses with rich, interconnected concepts.
    *   `flowchart TD/LR`: For courses with clear decision points or branching paths.
3.  **Construct Diagram:** Build the diagram by applying the DESIGN HEURISTICS below.
4.  **Translate Text:** Ensure all node labels and edge text are written in the specified language: {language}.
5.  **Generate Output:** Produce the final output according to the CRITICAL OUTPUT RULES.

---

### DESIGN HEURISTICS

**1. Radical Simplification & Focus:**
*   **Node Limit:** Maximum **15 nodes** for readability.
*   **Connection Limit:** Maximum **20 connections** to avoid a "spaghetti diagram."
*   **Hierarchy:** Use a clear 3-tier visual hierarchy:
    *   **Tier 1: Course Core (1 node):** The central theme. Style prominently.
    *   **Tier 2: Learning Streams (2-4 nodes):** The main knowledge areas or pillars.
    *   **Tier 3: Key Modules (4-8 nodes):** The most essential individual modules.
*   **Principle:** Show the *story* of the course, not every single detail.

**2. Quality over Quantity in Connections:**
*   **Primary Flow:** Always show the main sequential learning path.
*   **Critical Dependencies:** Only map prerequisites that would fundamentally block a learner's understanding if missed. Use a distinct line style (e.g., dotted).
*   **Major Integrations:** Highlight the 1-2 key points where multiple learning streams converge to create a new, synthesized understanding.
*   **AVOID:** Do not connect every module to every other. Avoid minor cross-references that clutter the diagram without adding significant insight.

**3. Clarity in Labeling & Layout:**
*   **Node Labels:** Keep them concise (2-4 words max). Do not use special characters (`()`, `[]`, etc.).
*   **Edge Labels:** Use a minimal set of clear, semantic labels only where the relationship isn't obvious from the layout.
    *   **Examples:** `"builds on"`, `"enables"`, `"applied in"`, `"synthesizes"`.
*   **Layout:** Prioritize a clean top-to-bottom (`TD`) or left-to-right (`LR`) flow. Minimize crossing lines and use spatial grouping for related concepts.

---

### EXAMPLES OF EXCELLENT OUTPUT

**Example 1: Clean Sequential Flow with Key Dependencies**
```mermaid
graph TD
    CORE["Course Topic"]

    subgraph Foundation
        A["Module A"]
    end
    subgraph Development
        B["Module B"]
        C["Module C"]
    end
    subgraph Application
        D["Module D"]
    end

    CORE --> A
    A --> B
    B --> C
    C --> D
    A -.->|"critical prerequisite"| C

    classDef core fill:#e74c3c,stroke:#c0392b,color:#fff;
    class CORE core;
```

**Example 2: Balanced Parallel Streams**
```mermaid
graph LR
    CORE["Course Core"]

    subgraph Theory Stream
        T1["Theory 1"] --> T2["Theory 2"]
    end
    subgraph Practice Stream
        P1["Practice 1"] --> P2["Practice 2"]
    end
    subgraph Synthesis
        S["Final Project"]
    end

    CORE --> T1
    CORE --> P1
    T2 --> S
    P2 --> S
    T1 -.->|"informs"| P1

    classDef core fill:#9b59b6,stroke:#8e44ad,color:#fff;
    classDef synthesis fill:#e67e22,stroke:#d35400;
    class CORE core;
    class S synthesis;
```

---

### TASK: GENERATE THE DIAGRAM

**Course Topic:** "{course_topic}"
**Language for Text:** {language}

**Course Structure to Analyze:**
---
{course_structure}
---
"""
