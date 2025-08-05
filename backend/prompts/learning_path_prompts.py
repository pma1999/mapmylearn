"""
Learning path prompt templates.

This module contains all the prompt templates used in the course
generation process, organized by their function in the system.
"""

# Version information for prompt tracking
__version__ = "1.0.0"

# =========================================================================
# Module and Submodule Planning Prompts
# =========================================================================

SUBMODULE_PLANNING_PROMPT = """
# EXPERT LEARNING ARCHITECT INSTRUCTIONS

As an expert in educational microstructure design, your task is to decompose a course module into focused, sequential submodules that collectively provide comprehensive coverage while maintaining conceptual atomicity.

## MODULE CONTEXT
- **Module Title**: {module_title}
- **Module Description**: {module_description}
- **Course Topic**: "{user_topic}"
- **Course Structure**: {learning_path_context}

## STRUCTURAL RESEARCH
Based on web searches about structuring "{module_title}":
{planning_search_context}

## REQUIREMENTS
- **Language**: Generate all content in {language}
- **Quantity**: Create 3-5 distinct submodules
- **Atomicity**: Each submodule must focus on ONE specific concept/skill

## DESIGN PRINCIPLES
1. **Search-Optimized Atomicity**: Each submodule must address a single, distinct concept that would yield specific, relevant search results.

2. **Progressive Mastery Path**:
   - Begin with fundamental concepts essential for this module
   - Gradually increase complexity and depth
   - End with advanced application or integration

3. **Conceptual Narrative Flow**:
   - Each submodule must build directly on knowledge from previous submodules
   - Create clear conceptual dependencies between successive submodules
   - Ensure smooth transitions between adjacent topics

4. **Comprehensive Coverage**:
   - The submodules must collectively cover ALL aspects of the module
   - Eliminate critical knowledge gaps
   - Balance breadth and depth appropriately

## ANALYTICAL PROCESS
1. First, analyze the research insights to identify standard topic divisions and approaches
2. Map the conceptual dependencies within the module topic
3. Determine optimal sequencing for progressive learning
4. Identify distinct, searchable concepts for each submodule

## SUBMODULE SPECIFICATION
For each submodule, provide:

1. **Title**: Clear, concept-focused title (searchable keyword phrase)
2. **Description**: Detailed explanation of submodule content and boundaries (50-100 words)
3. **Core Concept**: The ONE central idea/skill this submodule focuses on (1 sentence)
4. **Learning Objectives**: 2-3 specific, measurable outcomes
5. **Key Components**: 3-5 essential elements/topics covered
6. **Depth Level**: Specify as Basic, Intermediate, Advanced, or Expert

Ensure each submodule has clear conceptual boundaries and could stand alone as a searchable learning unit.

{format_instructions}
"""

# =========================================================================
# Search Query Generation Prompts
# =========================================================================

MODULE_SUBMODULE_PLANNING_QUERY_GENERATION_PROMPT = """
# EXPERT CURRICULUM STRUCTURE ANALYST INSTRUCTIONS

Your task is to generate optimal search queries to find information specifically about how to STRUCTURE and ORGANIZE the content of a given learning module into logical submodules.

## MODULE INFORMATION
Title: "{module_title}"
Description: {module_description}
Position: Module {module_order} of {module_count}
Course Topic: "{user_topic}"

## LEARNING PATH CONTEXT
{learning_path_context}

## LANGUAGE STRATEGY
- The final course will be presented in {language}.
- Generate search queries in {search_language} to maximize retrieval of structural information (e.g., syllabi, curriculum design discussions, standard breakdowns).

## SEARCH FOCUS: MODULE STRUCTURE
These queries are NOT for finding content about the module topic itself, but for understanding HOW TO BREAK DOWN the module topic {module_title} into smaller, teachable sub-units (submodules).

Focus on finding information about:
- Standard curriculum structures for "{module_title}" or similar topics.
- Common ways "{module_title}" is divided in courses or textbooks.
- Prerequisites and logical sequencing *within* the module topic.
- Different approaches to teaching or structuring "{module_title}".
- Example syllabi, course outlines, or breakdowns for "{module_title}".

## SEARCH QUERY REQUIREMENTS
Generate EXACTLY 3 search queries that will help determine the optimal submodule structure.

For each search query:
- Make it specific to retrieving STRUCTURAL and ORGANIZATIONAL information about "{module_title}".
- Combine the essence of "{module_title}" with terms indicating structural or organizational aspects. For example, think about using keywords such as "curriculum structure", "module breakdown", "teaching sequence", "syllabus example", or "learning objectives progression" in conjunction with the specific concepts of "{module_title}".
- QUOTE USAGE RULE: Use quotes sparingly, ONLY for the exact module title "{module_title}" if it's a multi-word phrase or a very specific term that needs to be searched together. Combine structural keywords without quotes otherwise.
    - GOOD Example (Title quoted): `"Machine Learning Foundations"` curriculum design breakdown
    - GOOD Example (Title not quoted): `Physics kinematics module structure syllabus example`
- Explain precisely how this query helps determine the submodule structure (number, titles, sequence).
- Ensure queries are distinct and target different facets of structural planning.

Your response should be exactly 3 search queries, each with a detailed rationale.

{format_instructions}
"""

SUBMODULE_QUERY_GENERATION_PROMPT = """
# EXPERT RESEARCH ASSISTANT INSTRUCTIONS

Your task is to generate optimal search queries that will gather comprehensive information for developing educational content.

## SUBMODULE INFORMATION
Title: "{submodule_title}"
Description: {submodule_description}
Position: Submodule {submodule_order} of {submodule_count} in Module {module_order} of {module_count}
Module Title: "{module_title}"
Course Topic: "{user_topic}"

## CONTEXT
Module context: {module_context}
Learning path context: {learning_path_context}

## SEARCH LANGUAGE STRATEGY
Important: While the content will be presented in {language}, you should generate search queries in the language most likely to yield comprehensive information. For universal topics, this is typically English, but for regionally specific topics (e.g., history of Spain), consider using the appropriate regional language.

## SEARCH STRATEGY

Based on thorough analysis of this submodule's requirements, generate 5 search queries that will:
1. Cover different critical aspects needed for developing this submodule
2. Target specific concepts, techniques, or examples that should be included
3. Ensure comprehensive understanding of the submodule's core focus
4. Address various complexity levels appropriate for this submodule
5. Target high-quality educational content from authoritative sources

For each search query:
- Make it specific and targeted to return useful results
- Explain why this search is essential for developing this submodule
- Ensure it addresses a different aspect needed for comprehensive coverage
- Design it to return high-quality educational content
- **QUOTE USAGE RULE: NEVER use more than ONE quoted phrase per query.** Quotes are ONLY for essential multi-word technical terms that MUST be searched together (e.g., "React Context API").
- **DO NOT put quotes around every keyword.** Combine specific keywords without quotes. 
    - BAD Example (Too many quotes): `"Spectral Analysis" "DFT" "FFT" "windowing functions"`
    - GOOD Example (One quote): `"Spectral Analysis" concepts DFT FFT tutorial`
    - GOOD Example (No quotes): `Spectral Analysis DFT FFT windowing functions common issues`
- **Getting *some* relevant results by combining specific unquoted terms is ALWAYS better than getting *zero* results from excessive quoting.**
- If the submodule has a defined depth level (e.g., basic, advanced), try to subtly reflect this in the search terms (e.g., 'introduction to...' or 'advanced techniques for...'), but without sacrificing getting results.

Your response should be exactly 5 search queries, each with its detailed rationale.

{format_instructions}
"""

# =========================================================================
# Content Development Prompts
# =========================================================================

SUBMODULE_CONTENT_DEVELOPMENT_PROMPT = """
# EXPERT EDUCATIONAL CONTENT ARCHITECT & STORYTELLER

Your mission is to craft an exceptional learning experience for the submodule "{submodule_title}". Imagine you are a world-class tutor who is passionate, deeply knowledgeable, and gifted at making complex topics feel intuitive and fascinating. Your goal is not just to present information, but to build a robust and lasting understanding for the learner.

## SUBMODULE CONTEXT
- **Course Topic**: "{user_topic}"
- **Module**: "{module_title}"
- **Submodule**: "{submodule_title}"
- **Description**: {submodule_description}

## CONTEXT WITHIN THE LEARNING JOURNEY
- **Module Context**: {module_context}
- **Adjacent Submodules**: {adjacent_context}
- **Full Learning Path**: {learning_path_context}

## LANGUAGE
- Generate all content in **{language}**.

## RESEARCH MATERIAL
- You have been provided with the following research to inform your writing:
{search_results}

## THE CORE PHILOSOPHY: A DIDACTIC DEEP DIVE

This is not a summary. This is a comprehensive, rigorous, and exhaustive exploration of the submodule's topic. The learner should finish this text feeling they have a perfect, detailed, and intuitive grasp of the subject.

**1. Let the Content Dictate the Structure:**
   - The structure of your explanation should flow organically from the topic itself. While a typical structure might include an introduction, several core explanatory sections, practical examples, and a conclusion, you are not bound by a rigid template.
   - The best structure is the one that best helps the learner build knowledge step-by-step. Analyze the topic and decide the most logical and engaging path to guide the learner from basic understanding to deep mastery.

**2. Be Exhaustive and Rigorous:**
   - Go deep. Explain the "how" and, most importantly, the "why". Unpack the mechanisms "under the hood".
   - Cover the topic completely, including essential nuances, edge cases, and common misconceptions.
   - Your explanation should be substantial. Aim for a length of **1500-2500 words** of rich, valuable content. This length should come from depth, not repetition.

**3. Be a Masterful Teacher:**
   - **Didactic and Step-by-Step**: Guide the learner by the hand. Build concepts layer by layer, ensuring one is solid before introducing the next. Break down complexity into manageable, digestible steps.
   - **Engaging and Entertaining**: Write with a narrative flair. Make the topic fascinating. Use powerful analogies and clear, relevant examples that illuminate, rather than distract from, the core concepts. Your tone should be authoritative yet encouraging and approachable.
   - **Clarity is Paramount**: Use precise language, but always ensure it's accessible. The goal is to create "aha!" moments and build mental models that last. Leave no room for ambiguity.

**4. Connect to the Bigger Picture:**
   - While your focus is this submodule, remember it's part of a larger journey. Briefly connect the concepts to what the learner already knows and what they will learn next, using the provided context. This helps them build a cohesive map of the subject.

## FINAL OUTPUT REQUIREMENTS

- Produce a single, continuous, and beautifully written piece of educational content.
- Do not include any meta-commentary or notes to the developer. The output should be only the text for the learner.
- Conclude with a brief "SUBMODULE WRAP-UP" section that summarizes the key takeaways and smoothly transitions to the next topic, mentioning what it is and why it's the logical next step.

---
**SUBMODULE WRAP-UP**

In this submodule, we've taken a deep dive into [summarize the core topic]. We started by [mention starting point] and journeyed through [mention key concepts covered], ultimately understanding [mention the final, deeper understanding].

Now that you have a solid grasp of this, you are perfectly prepared for our next submodule. There, we will explore [briefly describe the next topic], which builds directly on what we've learned here by [explain the connection].
---
"""

# =========================================================================
# Quiz Generation Prompts
# =========================================================================

SUBMODULE_QUIZ_GENERATION_PROMPT = """
# EXPERT ASSESSMENT DESIGNER INSTRUCTIONS

You are tasked with creating 10 high-quality multiple-choice quiz questions that comprehensively assess a learner's understanding of a specific submodule.

## SUBMODULE DETAILS
Title: "{submodule_title}"
Description: {submodule_description}
Part of: Module "{module_title}" in Course on "{user_topic}"

## LANGUAGE INSTRUCTIONS
Create all questions, options, and explanations in {language}. This is the language the user has selected for learning.

## SUBMODULE CONTENT TO ASSESS
{submodule_content}

## ASSESSMENT DESIGN REQUIREMENTS

### Question Design Principles
1. **Comprehensive Coverage**: Create questions that test the full breadth of concepts presented in the submodule
2. **Depth Assessment**: Include questions that test both basic recall and deeper understanding
3. **Conceptual Understanding**: Focus on testing conceptual understanding rather than mere memorization
4. **Real-World Application**: Include questions that ask learners to apply concepts to scenarios
5. **Progressive Difficulty**: Include a mix of easy, medium, and challenging questions

### Question Structure Requirements
1. Each question must have EXACTLY 4 answer options (A, B, C, D)
2. Exactly ONE option must be correct
3. All incorrect options (distractors) must be plausible but clearly incorrect
4. Distractors should represent common misconceptions or errors in understanding
5. Questions must be clear, concise, and unambiguous
6. Questions should directly relate to the content presented in the submodule

### Explanation Requirements 
For each question, provide a detailed explanation that:
1. Clearly explains why the correct answer is correct
2. Optionally explains why incorrect options are wrong
3. References relevant portions of the submodule content
4. Provides additional context or clarification when helpful
5. Reinforces the key concept being tested

## ASSESSMENT COVERAGE GUIDELINES
Your 10 questions should assess comprehensively the submodule's content.

## OUTPUT FORMAT REQUIREMENTS
{format_instructions}
"""

# =========================================================================
# Resource Generation Prompts
# =========================================================================

TOPIC_RESOURCE_QUERY_GENERATION_PROMPT = """
# EXPERT RESEARCHER INSTRUCTIONS

Your task is to create the SINGLE MOST EFFECTIVE search query to find **high-quality, comprehensive external learning resources** (e.g., books, articles, online courses, tutorials, videos, official documentation) for a course on "{user_topic}".

## LEARNING PATH OVERVIEW
This search query aims to find top-tier external learning materials providing broad, authoritative coverage of the entire course topic.

## LEARNING PATH STRUCTURE
{learning_path_context}

## LANGUAGE STRATEGY
- Content will be presented to users in {language}.
- For search queries, use {search_language} to maximize information quality.
- If {user_topic} is culturally/regionally specific, consider language optimization.

## SEARCH QUERY REQUIREMENTS

### 1. Keyword-Focused Format for Finding Quality Resources
Your query MUST be optimized for a search engine API (like Google or Brave Search) to find **excellent learning materials**:
- Combine the core topic "{user_topic}" with a smart combination of quality indicators (e.g., "best", "comprehensive", "authoritative", "definitive", "essential", "recommended") and resource type keywords (e.g., "tutorial", "guide", "online course", "book", "official documentation", "reference", "video course", "article"). The goal is to find top-tier learning materials.
- **QUOTE USAGE RULE: NEVER use more than ONE quoted phrase per query.** Quotes are ONLY appropriate if the core "{user_topic}" itself is an essential multi-word phrase (e.g., "machine learning").
- **DO NOT add quotes around quality indicators or resource types.** Combine terms without quotes.
    - BAD Example (Too many quotes): `"best" "machine learning" "tutorial" "guide"`
    - GOOD Example (One quote, only if topic needs it): `best "machine learning" tutorial guide`
    - GOOD Example (No quotes): `best machine learning tutorial guide comprehensive`
- **Getting *some* high-quality resource results is ALWAYS better than getting *zero* results from excessive quoting.**
- Focus on keywords that signal quality but keep the search broad enough to return results.
- Avoid conversational language.

### 2. Comprehensive Resource Discovery Goal
Your query should aim to find resources covering "{user_topic}" broadly:
- Foundational concepts
- Key principles
- Typical progression paths
- Different depths (beginner to advanced)
- Both theoretical and practical aspects

### 3. Implied Quality and Authority
Use keywords that suggest quality (like "best", "comprehensive", "authoritative", "official") while keeping the query open enough to return actual results.

### 4. Educational Focus
The keywords must emphasize finding **learning resources** specifically.

### 5. Search Engine Optimization
- CRITICAL: Balance specificity with breadth - too restrictive queries return no results.
- Limit to 3-6 keywords/terms total for best results.
- Follow the **QUOTE USAGE RULE** strictly: **NEVER more than ONE quoted phrase**, and only if the topic itself requires it.
- Prioritize getting useful, high-quality results over perfect precision.

## OUTPUT REQUIREMENTS
Provide:
1. A single, powerful search engine query string (keywords, phrases) optimized to find **comprehensive, high-quality external learning resources** for the topic.
2. A detailed explanation of your search strategy and why this query is likely to find excellent resources.

{format_instructions}
"""

MODULE_RESOURCE_QUERY_GENERATION_PROMPT = """
# EXPERT RESEARCHER INSTRUCTIONS

Your task is to create the SINGLE MOST EFFECTIVE search query to find **high-quality, relevant external learning resources** for the specific module titled "{module_title}".

## MODULE DETAILS
Title: "{module_title}"
Description: {module_description}
Part of course on: "{user_topic}"

## MODULE CONTEXT
This module is part of a larger course:
{learning_path_context}

## LANGUAGE STRATEGY
- Content will be presented to users in {language}.
- For search queries, use {search_language} to maximize information quality.
- If this module covers culturally/regionally specific content, consider language optimization.

## SEARCH QUERY REQUIREMENTS

### 1. Keyword-Focused Format for Finding Quality Resources
Your query MUST be optimized for a search engine API (like Google or Brave Search) to find **excellent learning materials** relevant to this module:
- Combine specific keywords derived from the essence of "{module_title}" and its description ({module_description}) with terms indicating resource types (e.g., "tutorial", "practical guide", "article", "video lecture", "documentation") or learning goals/content aspects (e.g., "applied examples", "key concepts", "exercises", "best practices"). Ensure the query reflects the key concepts and objectives of the module.
- **QUOTE USAGE RULE: NEVER use more than ONE quoted phrase per query.** Quotes are ONLY for the most essential multi-word technical term specific to this module (e.g., "React Hooks"), if absolutely necessary.
- **DO NOT put quotes around every keyword.** Combine specific module terms without quotes.
    - BAD Example (Too many quotes): `"tutorial" "React Hooks" "examples" "best practices"`
    - GOOD Example (One quote): `tutorial "React Hooks" examples best practices`
    - GOOD Example (No quotes): `React Hooks tutorial examples best practices guide`
- **Getting *some* relevant module resources is ALWAYS better than getting *zero* results from excessive quoting.**
- Focus on keywords likely to yield high-quality educational content for this specific module.
- Avoid conversational language.

### 2. Module-Specific Focus
Your query must target resources specifically relevant to {module_title}, addressing its core concepts and key components.

### 3. Implied Quality and Authority
Use keywords that suggest quality ("best", "guide", "documentation", "official") while ensuring the query isn't too restrictive to return results.

### 4. Educational Value
The query keywords must emphasize finding **learning resources** specifically relevant to this module.

### 5. Search Engine Optimization
- CRITICAL: Balance specificity with breadth - too restrictive queries return no results. It is crucial to find RELEVANT resources for THIS MODULE. It's better to have a slightly broader query that returns good resources related to '{module_title}' than a hyper-specific one that returns nothing.
- Limit to 3-6 keywords/terms total for best results.
- Follow the **QUOTE USAGE RULE** strictly: **NEVER more than ONE quoted phrase**, and only if a key technical term requires it.
- Prioritize getting useful results over perfect precision.

## OUTPUT REQUIREMENTS
Provide:
1. A single, powerful search engine query string (keywords, phrases) optimized to find **relevant, high-quality external learning resources** for this module.
2. A detailed explanation of your search strategy and why this query is likely to find good resources for this specific module.

{format_instructions}
"""

SUBMODULE_RESOURCE_QUERY_GENERATION_PROMPT = """
# EXPERT RESEARCHER INSTRUCTIONS

Your task is to create the SINGLE MOST EFFECTIVE search query to find **highly targeted external learning resources** for the specific submodule titled "{submodule_title}".

## SUBMODULE DETAILS
Title: "{submodule_title}"
Description: {submodule_description}
Position: Submodule {submodule_order} of {submodule_count} in Module {module_order} of {module_count}
Module: "{module_title}"
Course Topic: "{user_topic}"

## CONTEXT
Module context: {module_context}
Adjacent submodules: {adjacent_context}

## LANGUAGE STRATEGY
- Content will be presented to users in {language}.
- For search queries, use {search_language} to maximize information quality.
- If this submodule covers specialized or regional content, consider language optimization.

## SEARCH QUERY REQUIREMENTS

### 1. Keyword-Focused Format for Finding Specific Resources
Your query MUST be optimized for a search engine API (like Google or Brave Search) to find **specific, high-quality learning materials** for this submodule:
- Combine very specific technical terms derived from the essence of "{submodule_title}" and its description with terms indicating resource types (e.g., "tutorial", "video tutorial", "official documentation"), content focus (e.g., "code example", "explanation", "case study", "common issues", "practical example", "practice exercise"), or actions relevant to learning (e.g., "implement", "apply", "debug").
- **QUOTE USAGE RULE: NEVER use more than ONE quoted phrase per query.** Quotes are ONLY for the SINGLE most critical multi-word technical term defining this submodule (e.g., a specific API name like "useState Hook"), IF ABSOLUTELY NECESSARY.
- **DO NOT put quotes around every keyword.** Combine specific keywords without quotes.
    - BAD Example (Too many quotes): `"hominin fossil record" "key examples" "Lucy" "Taung Child"`
    - GOOD Example (One quote): `"hominin fossil record" significance analysis Lucy`
    - GOOD Example (No quotes): `hominin fossil record key examples significance Lucy Taung Child`
- **Getting *some* relevant results by combining specific unquoted terms is VASTLY preferable to getting *zero* results from excessive quoting.**
- Focus on keywords likely to yield targeted and authoritative educational content.
- Avoid conversational language.

### 2. Laser-Focused Targeting
Your query must target resources that specifically address the exact concepts and skills covered in **this submodule**.

### 3. Implied Quality and Diversity
The query keywords should help find a mix of high-quality external learning resources like specific tutorials, code examples, documentation pages, explanatory articles, or videos.

### 4. Contextual Relevance
The query keywords should reflect the specific focus of this submodule and its need for **targeted external learning materials**.

### 5. Search Engine Optimization
- ABSOLUTELY CRITICAL: Balance specificity with breadth. It is infinitely better to generate a slightly less specific query that returns USEFUL and RELEVANT resources for '{submodule_title}' than a 'perfectly' specific query that returns ZERO results. The number one priority is finding helpful learning material. Optimize for obtaining relevant results.
- Choose the 3-5 most important terms or keywords that will find resources.
- Follow the **QUOTE USAGE RULE** strictly: **NEVER more than ONE quoted phrase**, and only if essential.
- Select only the most essential terms from the submodule title/description.

## OUTPUT REQUIREMENTS
Provide:
1. A single, powerful search engine query string (keywords, phrases) optimized to find **specific, high-quality external learning resources** for this submodule.
2. A detailed explanation of your search strategy and why it's ideal for finding relevant resources for this particular submodule.

{format_instructions}
"""

RESOURCE_EXTRACTION_PROMPT = """
# EXPERT RESOURCE CURATOR INSTRUCTIONS

Your task is to extract and format the absolute best resources from search results for a learning topic.

## SEARCH CONTEXT
Search Query: "{search_query}"
Target Level: {target_level} (topic, module, or submodule)
Topic: "{user_topic}"
{additional_context}

## SCRAPED SOURCE TABLE
Each source below has an ID. Use the ID to reference the source in your output.
{source_table}

## SEARCH RESULTS
{search_results}

## RESOURCE CURATION REQUIREMENTS

### Selection Criteria
Select {resource_count} high-quality resources that:
1. Provide exceptional educational value
2. Come from authoritative sources
3. Match the specific focus of the search query
4. Offer clear explanations and examples
5. Present information in an accessible way
6. Provide appropriate depth for the target level
7. Include diverse resource types (articles, videos, books, courses, etc.)

### Resource Diversity
Your selection MUST include a mix of resource types (do not select all of the same type):
- At least one interactive or video resource
- At least one text-based tutorial or guide
- Other diverse formats (books, courses, documentation, etc.)

### Required Resource Information
For each resource, provide:
1. ID: Numeric ID of the chosen source from the table above
2. Title: Clear, descriptive title
3. Description: 1-2 sentences explaining what value this resource provides
4. Type: The resource type (article, video, book, course, documentation, etc.)

## SOURCE SELECTION INSTRUCTIONS
- ONLY use IDs from the SCRAPED SOURCE TABLE above
- Do NOT include URLs in your response
- If a resource does not have a corresponding ID, do NOT include it

## OUTPUT FORMAT
Provide exactly {resource_count} resources formatted according to the requirements.
Ensure resources are diverse, high-quality, and specifically relevant to the search query.
Do not include general search results or low-quality resources.

{format_instructions}
"""

# =========================================================================
# Research Evaluation and Refinement Prompts (Following Google Pattern)
# =========================================================================

RESEARCH_EVALUATION_PROMPT = """
# EXPERT CURRICULUM ARCHITECT: RESEARCH EVALUATOR

Your task is to act as a curriculum architect and evaluate if the initial research provides enough information to **design a comprehensive course STRUCTURE** for the topic: "{user_topic}".

At this stage, you are **NOT** evaluating if there's enough content to **WRITE** the full course. Your focus is solely on whether the gathered information is sufficient to **OUTLINE** a high-quality, well-organized learning path.

## LANGUAGE INSTRUCTIONS
Conduct your analysis and provide responses in {language}.

## EVALUATION CRITERIA: STRUCTURAL SUFFICIENCY

Review the provided research summary and assess if it contains enough information to define the following for a course structure:

1.  **Foundational Concepts & Prerequisites:** Are the essential starting points and prerequisite ideas clearly identifiable?
2.  **Core Sub-domains & Key Topics:** Is there enough breadth to divide the subject into 3-7 coherent, self-contained modules?
3.  **Learning Progression & Dependencies:** Do the results reveal how concepts build on each other so you can order the modules logically?
4.  **High-Level Practical Focus:** Is there evidence of practical or applied dimensions that can be translated into *one or more* modules (without needing very granular examples)?
5.  **Advanced or Specialized Areas:** Is it clear what constitutes more advanced material that would appear near the end of the course?

## EVALUATION PROCESS & SUFFICIENCY STANDARDS

1.  **Analyze Research**: Review the depth and breadth of the search results summary below.
2.  **Identify Structural Gaps**: Pinpoint specific areas where information is missing *for the purpose of outlining the course structure*.
3.  **Assess Readiness for Design**: Determine if you can confidently design a course outline (Modules and their sequence).
4.  **Rate Confidence**: Give a confidence score (0.0 to 1.0) on how ready the research is for the *structural design phase*.

Research is **SUFFICIENT for STRUCTURING** if:
- All 5 evaluation criteria are adequately covered.
- You can confidently define a logical sequence of 3-7 modules.
- Your confidence score is 0.7 or higher.

Research is **INSUFFICIENT** if:
- One or more criteria are poorly covered (e.g., you can't determine a logical flow).
- The information is too superficial to define distinct modules.
- Confidence is below 0.7.

## KNOWLEDGE GAP IDENTIFICATION

If INSUFFICIENT, list **high-level structural gaps only** (do **NOT** ask for very specific content or examples). Each gap statement should:
- Reference the missing structural dimension in general terms.
- Avoid demanding concrete lesson examples or deep content details.

Examples of acceptable gap statements:
- "Insufficient coverage of foundational concepts to define the opening module."
- "Cannot determine a clear learning progression across the main sub-domains."
- "Lacks high-level practical context to justify an application-focused module."

Avoid overly granular statements such as requesting specific case studies or niche applications.

## OUTPUT REQUIREMENTS
Provide your evaluation in the structured format defined by the tool.

{format_instructions}

## CURRENT RESEARCH SUMMARY TO EVALUATE
{search_results_summary}
"""

REFINEMENT_QUERY_GENERATION_PROMPT = """
# EXPERT RESEARCH REFINEMENT SPECIALIST INSTRUCTIONS

Your task is to generate targeted search queries that will address specific knowledge gaps identified in the current research for the topic: "{user_topic}".

## LANGUAGE INSTRUCTIONS
- Generate analysis in {language}
- Create search queries in {search_language} to maximize information quality

## KNOWLEDGE GAPS TO ADDRESS
{knowledge_gaps}

## EXISTING SEARCH QUERIES (Avoid Redundancy)
{existing_queries}

## REFINEMENT STRATEGY

### 1. GAP-SPECIFIC TARGETING
For each knowledge gap, design queries that:
- Target the specific missing information precisely
- Use terminology likely to find authoritative, detailed sources
- Focus on curriculum design and educational structure insights
- Avoid redundancy with existing searches

### 2. AUTHORITATIVE SOURCE OPTIMIZATION
Structure queries to find:
- Academic syllabi and curriculum documents
- Educational frameworks and standards
- Expert discussions and pedagogical research
- Comprehensive guides and authoritative references
- Structured learning approaches and methodologies

### 3. DEPTH AND SPECIFICITY BALANCE
- Make queries specific enough to address the exact gaps
- Keep them broad enough to return useful results
- Target different types of authoritative sources
- Ensure each query addresses a distinct aspect of the gaps

## SEARCH QUERY REQUIREMENTS

Generate 3-5 targeted search queries that:

### Query Design Rules:
- **QUOTE USAGE RULE: NEVER use more than ONE quoted phrase per query**
- Quotes are ONLY for essential multi-word concepts that MUST be searched together
- **DO NOT quote every keyword** - combine specific terms without quotes
- **Getting some relevant gap-filling results is ALWAYS better than zero results from excessive quoting**

### Examples of Proper Query Formation:
- BAD (Too many quotes): "curriculum structure" "learning progression" "educational framework"
- GOOD (One quote): "curriculum structure" learning progression educational framework
- GOOD (No quotes): curriculum structure learning progression educational framework design

### Target Content Types:
- Educational curriculum documents and syllabi
- Pedagogical research and teaching methodologies  
- Learning progression frameworks and standards
- Expert discussions on teaching approaches
- Comprehensive educational resources and guides

### Gap Alignment:
- Each query must target specific identified knowledge gaps
- Queries should complement rather than duplicate existing searches
- Focus on filling the most critical information voids
- Target information needed for comprehensive curriculum design

## TARGETING STRATEGY EXPLANATION

Provide a clear explanation of how your query set:
- Strategically addresses each identified knowledge gap
- Complements existing research without redundancy
- Targets authoritative educational sources
- Will likely yield curriculum-relevant information

## OUTPUT REQUIREMENTS

{format_instructions}
"""

# =========================================================================
# Submodule Research Evaluation Prompts (Google-Style Pattern)
# =========================================================================

SUBMODULE_RESEARCH_EVALUATION_PROMPT = """# EXPERT SUBMODULE RESEARCH EVALUATOR

You are reviewing collected web research to determine if there is enough
information to write high-quality educational content for the submodule
"{submodule_title}" in the module "{module_title}" of the course about
"{user_topic}".

## LANGUAGE INSTRUCTIONS
- Provide your analysis in {language}.

## EVALUATION CRITERIA
- Coverage of the submodule description and depth level
- Diversity and credibility of sources
- Overall sufficiency to write a detailed explanation

Summarize missing areas as **knowledge gaps** if the research is insufficient.

{format_instructions}

## CURRENT RESEARCH SUMMARY
{search_results_summary}
"""

SUBMODULE_REFINEMENT_QUERY_GENERATION_PROMPT = """# SUBMODULE RESEARCH REFINEMENT

Generate additional search queries to fill the knowledge gaps for the submodule
"{submodule_title}" of module "{module_title}" in the course on "{user_topic}".

## LANGUAGE INSTRUCTIONS
- Write your analysis in {language}
- Formulate search queries in {search_language}

## KNOWLEDGE GAPS
{knowledge_gaps}

## EXISTING QUERIES
{existing_queries}

Provide 1-3 concise follow-up queries that address the gaps without duplicating
existing searches.

{format_instructions}
"""

# =========================================================================
# Submodule Chatbot Prompts
# =========================================================================

# Premium version with search capabilities for grounded users
CHATBOT_SYSTEM_PROMPT_PREMIUM = """
# EXPERT SUBMODULE TUTOR INSTRUCTIONS

You are an expert, friendly, and encouraging AI tutor embedded within a specific learning module. Your primary goal is to help the user deeply understand the content of the submodule titled "{submodule_title}". You should explain concepts clearly, intuitively, and in detail, making complex topics accessible, much like the Feynman technique.

## YOUR CURRENT CONTEXT
Course Topic: "{user_topic}"
Current Module: "{module_title}" (Module {module_order} of {module_count})
Current Submodule: "{submodule_title}" (Submodule {submodule_order} of {submodule_count})
Submodule Description: {submodule_description}

## FULL LEARNING PATH STRUCTURE (FOR CONTEXT)
{learning_path_structure}

## KNOWLEDGE BASE & CAPABILITIES
1.  **Primary Source:** Your main knowledge source is the specific SUBMODULE CONTENT provided below, along with the RAW RESEARCH MATERIALS. Base your explanations and answers fundamentally on this information.
2.  **Online Search Capability:** You have access to real-time online search capabilities to enrich your explanations with current, relevant information. Use this to:
    *   Find up-to-date examples, case studies, or recent discoveries related to the submodule topic.
    *   Provide additional credible sources that complement and expand on the submodule content.
    *   Answer questions that go beyond the provided text but are directly related to "{submodule_title}".
    *   Verify and supplement information with authoritative sources when helpful.
3.  **Enrichment with General Knowledge:** You MAY also use your general knowledge to:
    *   Provide intuitive analogies and relatable examples to clarify concepts mentioned in the submodule.
    *   Explain prerequisite concepts briefly if they are essential to understanding the submodule content.
    *   **Crucially:** Always relate these explanations back to the context of "{submodule_title}".
    *   **Transparency:** When using online sources or extending beyond the provided text, mention it naturally (e.g., "I found some current examples..." or "Recent research shows...").
4.  **Scope Boundaries:**
    *   Focus primarily on topics related to "{submodule_title}" and its immediate context within the course.
    *   If asked about unrelated topics, politely redirect while offering to search for connections to the current submodule if relevant.
    *   Always prioritize accuracy and cite credible sources when using online information.

## *** SUBMODULE CONTENT (YOUR KNOWLEDGE BASE) ***
--- START SUBMODULE CONTENT ---
{submodule_content}
--- END SUBMODULE CONTENT ---

## RAW RESEARCH MATERIALS (Secondary Source)
{submodule_research}

## TUTORING & RESPONSE GUIDELINES
1.  **Explain Intuitively:** Break down complex ideas. Use analogies and real-world examples relevant to the user's potential experience where possible. Avoid unnecessary jargon; if technical terms are needed, explain them simply.
2.  **Aim for Depth and Clarity:** Provide thorough explanations. Anticipate potential points of confusion. Ensure your explanations are accurate and directly support learning the submodule's content.
3.  **Leverage Online Resources:** When it would enhance understanding, use your search capabilities to find current examples, additional explanations, or authoritative sources that complement the submodule content.
4.  **Be Conversational & Encouraging:** Maintain a friendly, patient, and enthusiastic tone. Act as a supportive tutor who can access the latest information to help you learn.
5.  **Check Understanding (Optional but Recommended):** Occasionally ask simple clarifying questions to gauge understanding (e.g., "Does that explanation make sense?", "Would an example help clarify that point?").
6.  **Language Flexibility:** Default to {language}. However, if the user communicates consistently in another language, adapt and respond in that language for a better experience. Prioritize the user's active language.
7.  **Handle Ambiguity:** If a question is unclear, ask for clarification before providing an answer.
8.  **Completeness within Scope:** Answer the user's query fully using all available resources (submodule content, research materials, online search, and general knowledge). Clearly indicate when you're enhancing the base content with external sources.
"""

# Standard version for regular users (restricted to provided content)
CHATBOT_SYSTEM_PROMPT = """
# EXPERT SUBMODULE TUTOR INSTRUCTIONS

You are an expert, friendly, and encouraging AI tutor embedded within a specific learning module. Your primary goal is to help the user deeply understand the content of the submodule titled "{submodule_title}". You should explain concepts clearly, intuitively, and in detail, making complex topics accessible, much like the Feynman technique.

## YOUR CURRENT CONTEXT
Course Topic: "{user_topic}"
Current Module: "{module_title}" (Module {module_order} of {module_count})
Current Submodule: "{submodule_title}" (Submodule {submodule_order} of {submodule_count})
Submodule Description: {submodule_description}

## FULL LEARNING PATH STRUCTURE (FOR CONTEXT)
{learning_path_structure}

## KNOWLEDGE BASE & SCOPE
1.  **Primary Source:** Your main knowledge source is the specific SUBMODULE CONTENT provided below, along with the RAW RESEARCH MATERIALS. Base your explanations and answers fundamentally on this information.
2.  **Enrichment with General Knowledge:** You MAY use your general knowledge to:
    *   Provide intuitive analogies and relatable examples to clarify concepts mentioned in the submodule.
    *   Explain prerequisite concepts briefly if they are essential to understanding the submodule content and not explicitly covered.
    *   Answer questions directly related to the submodule's topic, even if the specific detail isn't in the text, BUT ONLY IF you are highly confident in the accuracy.
    *   **Crucially:** Always relate these explanations back to the context of "{submodule_title}".
    *   **Transparency:** If you use general knowledge that significantly extends beyond the provided text, briefly mention it (e.g., "Drawing on general concepts of X..." or "While the text focuses on Y, it's related to the broader idea of Z...").
3.  **Strict Boundaries:**
    *   DO NOT answer questions about topics unrelated to "{submodule_title}" or its immediate context within the course.
    *   DO NOT invent information or speculate. If the provided content and your reliable general knowledge don't cover a user's question adequately, state that clearly and politely.
    *   Politely redirect users asking about other submodules or topics, suggesting they navigate to the relevant section using the Course Structure.

## *** SUBMODULE CONTENT (YOUR KNOWLEDGE BASE) ***
--- START SUBMODULE CONTENT ---
{submodule_content}
--- END SUBMODULE CONTENT ---

## RAW RESEARCH MATERIALS (Secondary Source)
{submodule_research}

## TUTORING & RESPONSE GUIDELINES
1.  **Explain Intuitively:** Break down complex ideas. Use analogies and real-world examples relevant to the user's potential experience where possible. Avoid unnecessary jargon; if technical terms are needed, explain them simply.
2.  **Aim for Depth and Clarity:** Provide thorough explanations. Anticipate potential points of confusion. Ensure your explanations are accurate and directly support learning the submodule's content.
3.  **Be Conversational & Encouraging:** Maintain a friendly, patient, and enthusiastic tone. Act as a supportive tutor.
4.  **Check Understanding (Optional but Recommended):** Occasionally ask simple clarifying questions to gauge understanding (e.g., "Does that explanation make sense?", "Would an example help clarify that point?").
5.  **Language Flexibility:** Default to {language}. However, if the user communicates consistently in another language, adapt and respond in that language for a better experience. Prioritize the user's active language.
6.  **Handle Ambiguity:** If a question is unclear, ask for clarification before providing an answer.
7.  **Completeness within Scope:** Answer the user's query fully based on the available information (submodule content, research materials, and allowed general knowledge). If the information isn't available within your scope, state that.
"""

# =========================================================================
# Content Evaluation and Refinement Prompts (Following Google Pattern for Content Quality)
# =========================================================================

CONTENT_EVALUATION_PROMPT = """# EXPERT EDUCATIONAL CONTENT EVALUATOR INSTRUCTIONS

Your task is to rigorously evaluate educational content across multiple critical dimensions to determine if it meets high-quality educational standards for effective learning.

## CONTENT EVALUATION CONTEXT
- Subject Topic: {user_topic}
- Module: {module_title}
- Submodule: {submodule_title}
- Submodule Description: {submodule_description}
- Content Depth Level: {depth_level}
- Target Learning Style: {explanation_style}

## CONTENT TO EVALUATE
{submodule_content}

## EVALUATION FRAMEWORK
Assess the content quality across these critical dimensions:

### 1. DEPTH AND COMPLETENESS
- Does the content adequately cover the submodule topic with appropriate depth?
- Are key concepts, principles, and mechanisms explained thoroughly?
- Are there missing fundamental elements that should be included?
- Does the depth match the specified level and learning requirements?

### 2. CLARITY AND ACCESSIBILITY
- Is the content clearly written and well-structured?
- Are complex concepts explained in an understandable manner?
- Is the logical flow and progression appropriate?
- Are explanations accessible for the intended learning style?

### 3. ACCURACY AND PRECISION
- Is the technical information accurate and up-to-date?
- Are concepts and terminology used correctly?
- Are there any factual errors or misleading statements?
- Does the content reflect current best practices?

### 4. EDUCATIONAL EFFECTIVENESS
- Does the content support meaningful learning outcomes?
- Are examples and illustrations helpful and relevant?
- Is the content engaging and well-organized for learning?
- Does it provide sufficient context and practical applications?

### 5. COMPREHENSIVENESS
- Are all essential aspects of the submodule topic covered?
- Are important subtopics or related concepts addressed?
- Is there a good balance between theory and practical application?
- Are prerequisites and follow-up connections clear?

### 6. PEDAGOGICAL QUALITY
- Does the content follow sound educational principles?
- Is information presented in a logical learning sequence?
- Are there appropriate transitions and connections between concepts?
- Does it facilitate understanding and retention?

## EVALUATION CRITERIA
Rate the content on whether it meets **high-quality educational standards** suitable for effective learning. Consider:
- **SUFFICIENT**: Content is comprehensive, clear, accurate, and educationally effective
- **INSUFFICIENT**: Content has significant gaps, unclear explanations, or pedagogical weaknesses

## QUALITY THRESHOLD
Set the bar HIGH. Content should be:
- Educationally sound and effective for learning
- Comprehensive enough to achieve stated learning objectives
- Clear and accessible to the intended audience
- Technically accurate and current
- Well-structured with good pedagogical flow

## OUTPUT REQUIREMENTS
Provide a thorough, objective evaluation determining whether the content meets these high educational standards. If content is insufficient, identify specific gaps and improvement areas that would make it educationally effective.

{format_instructions}
"""

CONTENT_REFINEMENT_QUERY_GENERATION_PROMPT = """# EXPERT CONTENT ENHANCEMENT RESEARCHER INSTRUCTIONS

Your task is to generate highly targeted search queries to address specific content quality gaps and enhance educational material to meet high educational standards.

## CONTENT REFINEMENT CONTEXT
- Subject Topic: {user_topic}
- Module: {module_title}
- Submodule: {submodule_title}
- Content Evaluation Status: {content_status}
- Current Content Loop: {current_loop}/{max_loops}

## IDENTIFIED CONTENT GAPS
{content_gaps}

## IMPROVEMENT AREAS NEEDED
{improvement_areas}

## CURRENT CONTENT ASSESSMENT
### Depth Assessment:
{depth_assessment}

### Clarity Assessment:
{clarity_assessment}

### Quality Issues:
{quality_issues}

## EXISTING RESEARCH FOUNDATION
### Previous Search Queries:
{existing_queries}

### Available Information:
{current_research_summary}

## CONTENT ENHANCEMENT MISSION
Generate precise, targeted search queries that will find specific information to enhance the educational content and address the identified quality gaps.

## REFINEMENT QUERY STRATEGY

### 1. Gap-Specific Enhancement
- Target each specific content deficiency with focused queries
- Seek information that directly improves the identified weak areas
- Look for deeper explanations, better examples, or clearer methodologies

### 2. Quality Enhancement Focus
- Find supplementary information that enhances content depth
- Seek better pedagogical approaches and explanations
- Look for practical examples, case studies, and real-world applications

### 3. Educational Effectiveness
- Target information that improves learning outcomes
- Seek content that enhances clarity and understanding
- Look for better ways to explain complex concepts

### 4. Complementary Research
- Build on existing information rather than duplicating it
- Find perspectives or details not covered in current research
- Seek information that fills specific educational gaps

### 5. Content Type Targeting
- Seek explanation methodologies and teaching approaches
- Look for practical examples and demonstration techniques
- Find analogies, visualizations, or frameworks that aid understanding

## SEARCH QUERY REQUIREMENTS

Generate 2-4 targeted search queries that:

### Query Design Rules:
- **QUOTE USAGE RULE: NEVER use more than ONE quoted phrase per query**
- Quotes are ONLY for essential multi-word technical concepts that MUST be searched together
- **DO NOT quote every keyword** - combine specific terms without quotes
- **Getting relevant enhancement information is ALWAYS better than zero results from excessive quoting**

### Examples of Proper Query Formation:
- BAD (Too many quotes): "tutorial explanation" "practical examples" "step by step"
- GOOD (One quote): "tutorial explanation" practical examples step by step guide
- GOOD (No quotes): tutorial explanation practical examples step by step guide methods

### Target Content Types:
- Detailed explanations and clarification methods
- Practical examples and real-world applications
- Educational approaches and pedagogical techniques
- Visual aids, analogies, and demonstration methods
- Case studies and implementation examples

### Enhancement Goals:
- Address specific content gaps identified
- Improve clarity and accessibility
- Add practical examples and applications
- Enhance pedagogical effectiveness
- Fill missing educational elements

## TARGETING STRATEGY EXPLANATION
Provide a clear explanation of how your query set:
- Strategically addresses each identified content gap
- Complements existing content research without redundancy
- Targets information for educational enhancement
- Will likely yield content improvement materials

## SEARCH LANGUAGE STRATEGY
- Search queries in {search_language} for maximum information quality
- Final enhanced content will be presented in {output_language}
- Consider technical terminology and specialized educational resources

## OUTPUT REQUIREMENTS

{format_instructions}
"""

# Initial Flow Generation Prompt
INITIAL_FLOW_PROMPT = """Create a comprehensive learning path for the given topic. Structure the response as a detailed course with multiple modules and submodules.

Format your response as a JSON object with the following structure:
{
  "modules": [
    {
      "title": "Module Title",
      "description": "Brief description of what this module covers",
      "submodules": [
        {
          "title": "Submodule Title",
          "description": "Detailed description of the submodule content",
          "content": "Main educational content for this submodule",
          "duration_minutes": 30,
          "difficulty": "beginner|intermediate|advanced",
          "learning_objectives": ["objective1", "objective2", "objective3"]
        }
      ]
    }
  ]
}

Guidelines:
- Create 3-5 main modules
- Each module should have 2-4 submodules
- Content should be comprehensive and educational
- Include practical examples where applicable
- Ensure logical progression from basic to advanced concepts
- Duration should be realistic for the content depth
- Learning objectives should be specific and measurable"""

# Search Query Regeneration Prompt
REGENERATE_SEARCH_QUERY_PROMPT = """The search query "{failed_query}" didn't return useful results for the topic: {original_topic}

Generate a new, more effective search query that might find better information about this topic.

Guidelines:
- Try different keywords or synonyms
- Consider related concepts or broader/narrower terms
- Make the query more specific or more general as needed
- Focus on educational or informational content

Return only the new search query, nothing else."""

# Topic Resource Search Prompt
TOPIC_RESOURCE_SEARCH_PROMPT = """Generate 2-3 search queries to find educational resources for the topic: {topic}

{flow_context}

Focus on finding:
- Official documentation or guides
- Educational websites and tutorials
- Academic resources or research papers
- Practical examples and case studies

Format your response as a numbered list:
1. [first search query]
2. [second search query]
3. [third search query]"""

# Resource Query Regeneration Prompt
REGENERATE_RESOURCE_QUERY_PROMPT = """The resource search query "{failed_query}" didn't find good educational resources for: {original_topic}

Create a new search query that might find better educational resources, documentation, or learning materials.

Guidelines:
- Try different combinations of keywords
- Consider official sources, tutorials, or guides
- Look for specific resource types (documentation, examples, tutorials)
- Make the query more targeted to educational content

Return only the new search query, nothing else."""

# =========================================================================
# Enhanced Submodule Content Development Prompt (Comprehensive & Detailed)
# =========================================================================

ENHANCED_SUBMODULE_CONTENT_DEVELOPMENT_PROMPT = """
# EXPERT EDUCATIONAL CONTENT ARCHITECT

You are an expert educational content developer creating comprehensive, engaging learning material. Your task is to develop detailed, step-by-step content for a specific submodule. Your work must achieve a perfect balance between two critical goals: unyielding depth for the submodule's core topics and strategic, concise cross-referencing for topics covered elsewhere.

## SUBMODULE CONTEXT
- **Topic**: {user_topic}
- **Module**: {module_title} (Module {module_order} of {module_count})
- **Current Submodule**: {submodule_title} (Submodule {submodule_order} of {submodule_count})
- **Description**: {submodule_description}
- **Core Concept**: {core_concept}
- **Learning Objective**: {learning_objective}
- **Key Components**: {key_components}
- **Depth Level**: {depth_level}

## COURSE STRUCTURE CONTEXT
{learning_path_context}

## MODULE CONTEXT
{module_context}

## ADJACENT SUBMODULES
{adjacent_context}

## CONTENT DEVELOPMENT REQUIREMENTS

### 1. PRIMARY GOAL: UNYIELDING DEPTH & EXHAUSTIVE DETAIL (FOR THIS SUBMODULE'S CORE TOPICS)
Your foremost responsibility is to create a deeply comprehensive and engaging explanation of the concepts that are the **primary focus of THIS submodule**. For these topics, you must:

- **Be Truly Exhaustive**: Cover every key component of this submodule completely. Dive deep into mechanisms, processes, nuances, and edge cases. Explain how things work "under the hood."
- **Build Deep Understanding**: Take the learner by the hand and guide them into the depths of the topic. Explain everything thoroughly, breaking down complex ideas into digestible pieces. Address the "why" behind every important concept.
- **Achieve Substantial Length**: The core explanation for this submodule's unique topics should be a minimum of **1500-2500 words**. This length should be achieved through rich, detailed explanations, not filler.
- **Use an Engaging & Didactic Approach**:
    - **Narrative Flow**: Create a compelling learning journey that flows like a well-told story.
    - **Practical Examples**: Include relevant, illustrative examples throughout.
    - **Real-World Applications**: Connect theory to practical applications and use cases.
    - **Step-by-Step Guidance**: Break complex concepts into digestible steps.

### 2. SECONDARY GOAL: STRATEGIC CONTENT SCOPING & CROSS-REFERENCING
To maintain focus and avoid redundancy, you must intelligently handle concepts that overlap with other submodules. Use the `COURSE STRUCTURE CONTEXT` to determine the primary home for every concept.

**Rule for Handling Overlapping Concepts:**
- **IF a concept's main explanation belongs in ANOTHER submodule:**
    - **DO NOT** provide a detailed explanation here.
    - **DO** provide a brief, concise reference (1-2 sentences) to establish context.
    - **DO** explicitly and clearly direct the learner to the correct submodule for the deep dive.

- **IF a concept is the PRIMARY FOCUS of THIS submodule:**
    - **DO** explain it with the comprehensive, exhaustive detail required by Goal #1.

**Example of Correct Cross-Referencing:**
- **Correct:** "Before we dive into advanced query optimization, it's important to have a solid grasp of database indexing. Indexing is a fundamental technique for improving database performance by enabling faster data retrieval. **This concept is covered in full detail in the submodule: 'Module 2: Database Fundamentals - Submodule 2.3: Understanding Database Indexes'.** We will now build on that knowledge to explore..."
- **Incorrect:** (A multi-paragraph, detailed explanation of what database indexing is, how it works, B-trees, etc.)

### 3. STYLE ADAPTATION
{style_instructions}

### 4. CONTENT STRUCTURE REQUIREMENTS
- **Introduction** (150-200 words): Set context and preview what will be learned.
- **Core Content Sections** (1200-2000 words): 4-6 substantial sections covering this submodule's key components in great depth.
- **Practical Applications** (200-300 words): Real-world examples and use cases for this submodule's concepts.
- **Integration & Connections** (100-150 words): How this connects to other learning, using the cross-referencing rule.
- **Summary & Next Steps** (100-150 words): Consolidate learning and preview progression.

## LANGUAGE REQUIREMENTS
- **Content Language**: Write all content in {language}
- **Technical Accuracy**: Ensure precise use of terminology.
- **Accessibility**: Make complex concepts understandable at the specified depth level.

## OUTPUT REQUIREMENTS
Provide ONLY the comprehensive educational content. Do NOT include:
- Meta-commentary about the content creation process
- Explanations of your approach
- Headers describing the structure unless they're part of the educational content

The content should flow naturally and engage the learner from start to finish.

## RESEARCH RESOURCES & CONTEXT
The following research materials and scraped content provide additional context and information to enhance your content development. Use these resources to create more comprehensive, accurate, and detailed educational material:

{search_results_context}
"""