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
# EXPERT TEACHING ASSISTANT INSTRUCTIONS

Your task is to create comprehensive educational content for a submodule titled "{submodule_title}" 
which is part of the module "{module_title}" in a course about "{user_topic}".

## SUBMODULE INFORMATION
Description: {submodule_description}
Position: Submodule {submodule_order} of {submodule_count} in Module {module_order} of {module_count}

## CONTEXT
Module context: {module_context}
Adjacent submodules: {adjacent_context}
Learning path context: {learning_path_context}

## LANGUAGE INSTRUCTIONS
Generate all content in {language}. This is the language selected by the user for learning the material.

## RESEARCH INFORMATION
{search_results}

## EXPLANATION REQUIREMENTS

### Core Principles

#### A) A Deep Dive That Builds Understanding
- Take the learner by the hand and guide them into the depths of the topic
- Explain everything thoroughly - leave no concept unclear
- Break down complex ideas into digestible pieces without losing their essence
- Build understanding layer by layer, ensuring each layer is solid before adding the next
- Make abstract concepts concrete through careful explanation
- Connect theory with practice, showing how things work in the real world
- Address the "why" behind every important concept
- Anticipate and clear up potential confusions before they arise

#### B) Truly Exhaustive and Detailed
- Cover every aspect of the submodule's focus completely
- Don't just scratch the surface - dive deep into mechanisms and processes
- Explain how things work "under the hood"
- Include critical nuances and edge cases
- Share practical implications and real-world considerations
- Provide rich context that enhances understanding
- Address common misconceptions explicitly
- Include expert insights that bring the topic to life

#### C) Naturally Flowing and Engaging
- Let the explanation flow like a well-told story
- Make complex topics fascinating by revealing their inherent interest
- Build natural connections between ideas
- Use analogies and examples that illuminate rather than distract
- Keep the reader engaged through narrative progression
- Make technical content approachable without oversimplifying
- Create "aha moments" through careful concept building
- Maintain a tone that's both authoritative and engaging

#### D) Perfect for the Learner's Journey
- Remember this submodule's place in their path to expertise
- Build naturally on their current knowledge
- Fill any potential knowledge gaps seamlessly
- Create solid foundations for future concepts
- Help them develop expert intuition
- Show how this piece fits into the bigger picture
- Build confidence alongside competence
- Ensure they're fully prepared for what comes next

#### E) Absolutely Clear and Memorable 
- Make every explanation crystal clear
- Use precise language while remaining accessible
- Illuminate rather than impress
- Create understanding that sticks
- Make complex ideas graspable
- Ensure key points are memorable
- Build mental models that last
- Leave no room for confusion

### Extension and Depth Requirements

- Core explanation should be at least 2000 words (excluding introduction and conclusion)
- Develop at least 15-20 substantial paragraphs that dive deep into the topic
- Each major concept should receive multiple paragraphs of thorough treatment
- Include detailed examples and applications that illuminate the concepts
- Include multiple levels of understanding (surface, mechanical, theoretical, practical, expert)
- Explore implications and connections extensively
- Address edge cases and special considerations in detail
- Include real-world applications and practical insights

Write a comprehensive, narrative explanation that deeply explores this submodule's topic.
Your explanation should be a single, continuous narrative. Let the nature of the content guide its flow.
Focus entirely on helping the reader truly understand and engage with the material.

At the end, include a brief section called "MODULE CLOSURE" that summarizes what was covered
and creates a bridge to the next submodule if applicable:

# MODULE CLOSURE

In this submodule, we have deeply explored [topic], starting with [initial concept] and gradually developing our understanding until [final concept]. We have analyzed in detail [key aspects], considering [special cases/applications] and establishing crucial connections with [related concepts].

The next submodule will focus on [next topic], where we will explore [detailed preview]. This will allow us to [benefit/connection with what was learned].
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

## SEARCH RESULTS
{search_results}

## CITATION LINKS
The following URLs were extracted from the search results and should be used as source links for your resource recommendations:
{search_citations}

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
1. Title: Clear, descriptive title
2. Description: 1-2 sentences explaining what value this resource provides
3. URL: Direct link to the resource - IMPORTANT: Use the citation links provided above whenever possible
4. Type: The resource type (article, video, book, course, documentation, etc.)

## CITATION USAGE INSTRUCTIONS
- ONLY use the exact URLs from the CITATION LINKS section above
- Match resources mentioned in the search results with their corresponding citation link
- DO NOT invent or make up any URLs. Never use generic URLs like "example.com" or similar placeholder formats
- If a resource mentioned in the search results does not have a corresponding real URL in the citation links, DO NOT include that resource

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
# EXPERT CURRICULUM RESEARCH EVALUATOR INSTRUCTIONS

Your task is to evaluate whether the current research information is sufficient to create a high-quality, comprehensive learning path for the topic: "{user_topic}".

## LANGUAGE INSTRUCTIONS
Conduct your analysis and provide responses in {language}.

## CURRENT RESEARCH SUMMARY
{search_results_summary}

## EVALUATION CRITERIA

Assess the research completeness across these CRITICAL DIMENSIONS for curriculum design:

### 1. FOUNDATIONAL KNOWLEDGE COVERAGE
- Are fundamental concepts, prerequisites, and core principles adequately covered?
- Is there sufficient depth on basic building blocks needed for learning progression?

### 2. COMPREHENSIVE TOPIC BREADTH 
- Are all major sub-domains and essential areas within "{user_topic}" represented?
- Is coverage balanced across different aspects of the field?

### 3. LOGICAL LEARNING PROGRESSION
- Is there enough information to understand natural learning sequences and dependencies?
- Can you determine how concepts build upon each other?

### 4. PRACTICAL APPLICATION INSIGHTS
- Are real-world applications, examples, and skill development approaches covered?
- Is there sufficient information about what learners should be able to DO?

### 5. COMPLEXITY AND DEPTH MAPPING
- Is there information covering different skill levels (beginner to advanced)?
- Are challenging areas and common learning obstacles identified?

### 6. STRUCTURED TEACHING APPROACHES
- Is there insight into how this topic is typically taught or organized?
- Are there examples of successful curriculum structures or pedagogical approaches?

## EVALUATION PROCESS

1. **Analyze Research Quality**: Review the depth, authority, and comprehensiveness of current research
2. **Identify Coverage Gaps**: Pinpoint specific areas where information is insufficient or missing
3. **Assess Curriculum Readiness**: Determine if current information can support high-quality module design
4. **Calculate Confidence**: Rate your confidence in the research completeness (0.0-1.0 scale)

## SUFFICIENCY STANDARDS

Research is considered SUFFICIENT when:
- All 6 critical dimensions have adequate coverage for curriculum design
- Enough specific information exists to create detailed, well-structured modules
- No major knowledge gaps would result in superficial or incomplete learning modules
- Confidence level is 0.7 or higher

Research is INSUFFICIENT when:
- Any critical dimension lacks adequate coverage
- Key areas have only surface-level information
- Major gaps would compromise learning module quality
- Confidence level is below 0.7

## KNOWLEDGE GAP IDENTIFICATION

If research is insufficient, identify specific gaps using this format:
- "Insufficient coverage of [specific area] for [specific curriculum design need]"
- "Missing information about [specific aspect] needed to [specific design goal]"
- "Superficial treatment of [specific topic] requires deeper research for [specific reason]"

Be specific and actionable - these gaps will guide targeted follow-up research.

## OUTPUT REQUIREMENTS

Provide your evaluation in the following structured format:

{format_instructions}
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