"""
Learning path prompt templates.

This module contains all the prompt templates used in the learning path
generation process, organized by their function in the system.
"""

# Version information for prompt tracking
__version__ = "1.0.0"

# =========================================================================
# Module and Submodule Planning Prompts
# =========================================================================

SUBMODULE_PLANNING_PROMPT = """
# EXPERT TEACHING ASSISTANT INSTRUCTIONS

Your task is to break down a learning module into logical submodules that provide deep, comprehensive coverage.

## MODULE INFORMATION
Title: {module_title}
Description: {module_description}

This module is part of a learning path about "{user_topic}".

## CONTEXT
{learning_path_context}

## STRUCTURAL RESEARCH INSIGHTS
Based on web searches about how to structure the topic "{module_title}", here are some insights:
{planning_search_context}
---

## LANGUAGE INSTRUCTIONS
Generate all content (titles, descriptions, explanations) in {language}.

## SUBMODULE PLANNING PRINCIPLES

### A) Progressive Depth Development
- First submodule must establish fundamental concepts for this module
- Each subsequent submodule builds depth systematically
- Technical complexity increases progressively
- Final submodules should reach deep understanding of this module's focus

### B) Narrative and Conceptual Flow
- Submodules should flow naturally like chapters in a story
- Each submodule must have ONE clear conceptual focus
- Ensure conceptual continuity between submodules
- Create a narrative arc that builds understanding

### C) Exhaustive Coverage
- Together, submodules must cover ALL aspects of the module's topic
- Each submodule should be thorough within its focused scope
- Ensure no critical components or concepts are missed
- Provide both breadth and depth through careful submodule design

## INSTRUCTIONS & REQUIREMENTS
**Critically evaluate the STRUCTURAL RESEARCH INSIGHTS provided above.** Use these insights, along with the module description and overall path context, to inform your submodule plan.

Create 3-5 logical submodules that:
1. Cover different aspects of the module topic, informed by common structures found in the research.
2. Build upon each other in a narrative sequence.
3. Are comprehensive yet focused.
4. Together completely fulfill the module's description.

For each submodule provide:
1. A clear, descriptive title reflecting its place in the structure.
2. A detailed description explaining what this submodule will cover.
3. The core concept this submodule focuses on.
4. Clear learning objectives.
5. Key components to be covered.
6. The depth level (basic, intermediate, advanced, or expert).

Ensure the submodules create a complete, cohesive learning experience for this module, leveraging insights from the structural research.

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
Learning Path Topic: "{user_topic}"

## LEARNING PATH CONTEXT
{learning_path_context}

## LANGUAGE STRATEGY
- The final learning path will be presented in {language}.
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
- Use terms like: '"{module_title}" curriculum structure', '"{module_title}" module breakdown', 'teaching "{module_title}" sequence', '"{module_title}" syllabus example', '"{module_title}" learning objectives progression'.
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
Learning Path Topic: "{user_topic}"

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
- Prioritize queries that find detailed explanations ('how {key_concept} works', 'explanation {key_concept}'), practical examples ('{key_concept} code example', '{key_concept} use case'), tutorials ('{key_concept} tutorial'), common pitfalls ('{key_concept} common errors'), and best practices ('{key_concept} best practices') relevant to '{submodule_title}'.
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
which is part of the module "{module_title}" in a learning path about "{user_topic}".

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
Part of: Module "{module_title}" in Learning Path on "{user_topic}"

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

Your task is to create the SINGLE MOST EFFECTIVE search query to find **high-quality, comprehensive external learning resources** (e.g., books, articles, online courses, tutorials, videos, official documentation) for a learning path on "{user_topic}".

## LEARNING PATH OVERVIEW
This search query aims to find top-tier external learning materials providing broad, authoritative coverage of the entire learning path topic.

## LEARNING PATH STRUCTURE
{learning_path_context}

## LANGUAGE STRATEGY
- Content will be presented to users in {language}.
- For search queries, use {search_language} to maximize information quality.
- If {user_topic} is culturally/regionally specific, consider language optimization.

## SEARCH QUERY REQUIREMENTS

### 1. Keyword-Focused Format for Finding Quality Resources
Your query MUST be optimized for a search engine API (like Google or Tavily) to find **excellent learning materials**:
- Combine the core topic "{user_topic}" with a smart combination of quality indicators and resource type keywords.
- Use a mix like: **best {user_topic} tutorial**, **comprehensive {user_topic} guide**, **recommended {user_topic} online course**, **definitive {user_topic} book**, **official {user_topic} documentation**, **essential {user_topic} reference**, **{user_topic} video course**, **authoritative {user_topic} article**.
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
Part of learning path on: "{user_topic}"

## MODULE CONTEXT
This module is part of a larger learning path:
{learning_path_context}

## LANGUAGE STRATEGY
- Content will be presented to users in {language}.
- For search queries, use {search_language} to maximize information quality.
- If this module covers culturally/regionally specific content, consider language optimization.

## SEARCH QUERY REQUIREMENTS

### 1. Keyword-Focused Format for Finding Quality Resources
Your query MUST be optimized for a search engine API (like Google or Tavily) to find **excellent learning materials** relevant to this module:
- Combine specific keywords from "{module_title}" and its description with terms indicating resource types or learning goals. Ensure the query reflects the key concepts and objectives mentioned in the module description: {module_description}.
- Use keywords like: **tutorial {module_title}**, **practical guide {module_title}**, **{module_title} applied examples**, **{module_title} key concepts**, **detailed tutorial {module_title}**, **{module_title} exercises**, **article {module_title}**, **{module_title} video lecture**, **documentation {module_title}**, **best practices {module_title}**.
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
Learning Path Topic: "{user_topic}"

## CONTEXT
Module context: {module_context}
Adjacent submodules: {adjacent_context}

## LANGUAGE STRATEGY
- Content will be presented to users in {language}.
- For search queries, use {search_language} to maximize information quality.
- If this submodule covers specialized or regional content, consider language optimization.

## SEARCH QUERY REQUIREMENTS

### 1. Keyword-Focused Format for Finding Specific Resources
Your query MUST be optimized for a search engine API (like Google or Tavily) to find **specific, high-quality learning materials** for this submodule:
- Combine very specific technical terms from "{submodule_title}" and its description with terms indicating resource types, application, or specific content areas.
- Use keywords like: **tutorial {submodule_title}**, **{submodule_title} code example**, **{submodule_title} explanation**, **{submodule_title} case study**, **implement {submodule_title}**, **apply {submodule_title}**, **debug {submodule_title}**, **{submodule_title} common issues**, **{submodule_title} practical example**, **how to use {submodule_title}**, **{submodule_title} video tutorial**, **official documentation {submodule_title}**, **{submodule_title} practice exercise**.
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
# Submodule Chatbot Prompts
# =========================================================================

CHATBOT_SYSTEM_PROMPT = """
# EXPERT SUBMODULE TUTOR INSTRUCTIONS

You are an expert, friendly, and encouraging AI tutor embedded within a specific learning module. Your primary goal is to help the user deeply understand the content of the submodule titled "{submodule_title}". You should explain concepts clearly, intuitively, and in detail, making complex topics accessible, much like the Feynman technique.

## YOUR CURRENT CONTEXT
Learning Path Topic: "{user_topic}"
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
    *   DO NOT answer questions about topics unrelated to "{submodule_title}" or its immediate context within the learning path.
    *   DO NOT invent information or speculate. If the provided content and your reliable general knowledge don't cover a user's question adequately, state that clearly and politely.
    *   Politely redirect users asking about other submodules or topics, suggesting they navigate to the relevant section using the Learning Path Structure.

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