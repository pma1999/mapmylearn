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

## SUBMODULE REQUIREMENTS

Create 3-5 logical submodules that:
1. Cover different aspects of the module topic
2. Build upon each other in a narrative sequence
3. Are comprehensive yet focused
4. Together completely fulfill the module's description

For each submodule provide:
1. A clear, descriptive title
2. A detailed description explaining what this submodule will cover
3. The core concept this submodule focuses on
4. Clear learning objectives
5. Key components to be covered
6. The depth level (basic, intermediate, advanced, or expert)

Ensure the submodules create a complete, cohesive learning experience for this module.

{format_instructions}
"""

# =========================================================================
# Search Query Generation Prompts
# =========================================================================

SUBMODULE_QUERY_GENERATION_PROMPT = """
# EXPERT RESEARCH ASSISTANT INSTRUCTIONS

Your task is to generate optimal search queries that will gather comprehensive information for developing educational content for a specific submodule.

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
Important: While the content will be presented in {language}, you should generate search queries in the language most likely to yield comprehensive, high-quality information (often English for technical topics).

## SEARCH STRATEGY

Based on thorough analysis of this submodule's requirements, generate EXACTLY 5 search queries that will:
1. Cover different critical aspects needed for developing this submodule's content.
2. Target specific concepts, techniques, or examples that should be included.
3. Ensure comprehensive understanding of the submodule's core focus.
4. Address various complexity levels appropriate for this submodule (if applicable, consider terms like 'introduction to' or 'advanced techniques for').
5. Target high-quality educational content (explanations, examples, tutorials) from authoritative sources.

For each search query:
- **Prioritize queries that find:** Detailed explanations ('how {key_concept} works', 'explanation {key_concept}'), practical examples ('{key_concept} code example', '{key_concept} use case'), tutorials ('{key_concept} tutorial'), common pitfalls ('{key_concept} common mistakes'), and best practices ('{key_concept} best practices') relevant to "{submodule_title}".
- **USE QUOTES "" WITH EXTREME CAUTION:** Only for essential multi-word technical terms specific to this submodule (e.g., "React Context API"). Overusing quotes drastically reduces results. Getting *relevant* results is better than getting *no* results.
- Make it specific and targeted to return useful results for *writing the content* of this submodule.
- Explain why this search is essential for developing comprehensive content for this submodule.
- Ensure it addresses a different aspect needed for thorough coverage.

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

Your task is to create the SINGLE MOST EFFECTIVE search query to find **high-quality, comprehensive external learning resources** (e.g., books, articles, online courses, tutorials, videos, official documentation) for the overall learning path on "{user_topic}".

## LEARNING PATH OVERVIEW
This query aims to find top-tier external learning materials providing broad, authoritative coverage of the entire learning path topic.

## LEARNING PATH STRUCTURE
{learning_path_context}

## LANGUAGE STRATEGY
- Content will be presented to users in {language}.
- For the search query itself, use {search_language} (often English) to maximize information quality, unless {user_topic} is region-specific.

## SEARCH QUERY REQUIREMENTS

### 1. Keyword-Focused Format for Finding Quality Resources
Your query MUST be optimized for a search engine API (like Google or Tavily) to find **excellent learning materials**:
- **Combine '{user_topic}' intelligently with indicators of quality and resource type.** Use terms like: 'best tutorial', 'comprehensive guide', 'recommended online course', 'definitive book', 'official documentation', 'essential reference', 'video course', 'authoritative article'.
- **IMPORTANT - BALANCE QUALITY & RESULTS:** Aim for the BEST resources, but be realistic. Use only 1-2 quality indicators (like 'best', 'comprehensive') combined with '{user_topic}' and perhaps ONE resource type ('tutorial', 'book').
- **AVOID QUOTES ""** unless '{user_topic}' is an inseparable multi-word phrase. Prioritize getting a useful list of high-quality options over a perfectly precise query that yields nothing.
- Focus on keywords that signal quality but keep the search broad enough to return actual results.
- Avoid conversational language. Keep it concise (3-6 keywords/terms total).

### 2. Comprehensive Resource Discovery Goal
Your query should aim to find resources covering "{user_topic}" broadly: foundational concepts, key principles, typical progression, different depths, theoretical and practical aspects.

### 3. Implied Quality and Authority
Use keywords suggesting quality ('best', 'comprehensive', 'authoritative', 'official') strategically, without making the query too restrictive.

### 4. Educational Focus
Keywords must emphasize finding **learning resources** specifically.

## OUTPUT REQUIREMENTS
Provide:
1. A single, powerful search engine query string optimized to find **comprehensive, high-quality external learning resources** for the topic.
2. A detailed explanation of your search strategy and why this query is likely to find excellent broad resources.

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
- For the search query, use {search_language} (often English) to maximize information quality, unless the module covers region-specific content.

## SEARCH QUERY REQUIREMENTS

### 1. Keyword-Focused Format for Finding Quality Resources
Your query MUST be optimized for a search engine API to find **excellent learning materials** relevant to this module:
- Combine specific keywords from "{module_title}" and its description with terms indicating resource types or specific goals.
- **Consider terms reflecting module objectives:** 'practical guide {module_title}', 'applied examples {module_title}', '{module_title} key concepts', 'detailed tutorial {module_title}', '{module_title} exercises', 'best practices {module_title}'.
- **CRITICAL - BALANCE RELEVANCE & RESULTS:** It's vital to find resources RELEVANT to THIS MODULE. A slightly broader query returning good related resources is better than a hyper-specific one returning nothing.
- **USE QUOTES "" SPARINGLY:** Only if a key technical term crucial to the module *must* be kept together. Example: 'tutorial "React Hooks"' (if React Hooks is the module focus). Avoid quoting generic terms like 'tutorial' or 'examples'.
- Focus on keywords likely to yield high-quality educational content for *this specific module*.
- Avoid conversational language. Keep it concise (3-6 keywords/terms total).

### 2. Module-Specific Focus
Target resources specifically relevant to {module_title}, addressing its core concepts (from {module_description}) and learning objectives.

### 3. Implied Quality and Authority
Use keywords suggesting quality ('guide', 'documentation', 'official') where appropriate, without overly restricting results.

### 4. Educational Value
Keywords must emphasize finding **learning resources** relevant to this module.

## OUTPUT REQUIREMENTS
Provide:
1. A single, powerful search engine query string optimized to find **relevant, high-quality external learning resources** for this module.
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
- For the search query, use {search_language} (often English) to maximize information quality, especially for technical topics.

## SEARCH QUERY REQUIREMENTS

### 1. Keyword-Focused Format for Finding Specific Resources
Your query MUST be optimized for a search engine API to find **specific, high-quality learning materials** for this submodule:
- Combine very specific technical terms from "{submodule_title}" and its description with terms indicating resource types or actions.
- **Include terms related to application/problems:** 'implement {submodule_title}', 'apply {submodule_title}', 'debug {submodule_title}', '{submodule_title} common issues', 'practical example {submodule_title}', 'how to use {submodule_title}'.
- **MAXIMUM CAUTION WITH QUOTES "":** If there's ONE critical multi-word technical term defining this submodule (e.g., a specific API name, algorithm), consider quoting ONLY that term (e.g., 'tutorial "useState Hook"'). Otherwise, AVOID quotes and rely on specific keyword combinations.
- Focus on keywords likely to yield targeted and authoritative educational content (tutorials, code examples, docs, articles, videos).
- Avoid conversational language. Select only the 3-5 most essential terms.

### 2. Laser-Focused Targeting
Target resources addressing the exact concepts and skills covered in **this submodule**.

### 3. Quality and Diversity
Aim for a mix of high-quality external resources like specific tutorials, code examples, documentation pages, explanatory articles, or videos.

### 4. Contextual Relevance
Keywords should reflect the specific focus of this submodule ({submodule_description}) and its need for **targeted external learning materials**.

### 5. Search Engine Optimization - GETTING RESULTS IS KEY
- **ABSOLUTELY CRITICAL:** It's infinitely better to generate a query that is slightly less specific but returns *useful and relevant* resources for "{submodule_title}" than a 'perfectly' specific query returning ZERO results. **Optimize for finding useful learning material.**

## OUTPUT REQUIREMENTS
Provide:
1. A single, powerful search engine query string optimized to find **specific, high-quality external learning resources** for this submodule.
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
# EXPERT SUBMODULE ASSISTANT INSTRUCTIONS

You are a helpful AI assistant embedded within a specific learning module. Your primary goal is to answer the user's questions EXCLUSIVELY about the content provided below for the submodule titled "{submodule_title}".

## YOUR CURRENT CONTEXT
Learning Path Topic: "{user_topic}"
Current Module: "{module_title}" (Module {module_order} of {module_count})
Current Submodule: "{submodule_title}" (Submodule {submodule_order} of {submodule_count})
Submodule Description: {submodule_description}

## FULL LEARNING PATH STRUCTURE (FOR CONTEXT)
{learning_path_structure}

## *** SUBMODULE CONTENT (YOUR KNOWLEDGE BASE) ***
You MUST base your answers ONLY on the following content for "{submodule_title}":
--- START SUBMODULE CONTENT ---
{submodule_content}
--- END SUBMODULE CONTENT ---

## RESPONSE GUIDELINES
1.  **Answer Accurately:** Provide clear, concise, and accurate answers based ONLY on the SUBMODULE CONTENT provided above.
2.  **Stay Focused:** If the user asks about topics clearly outside this specific submodule's content, politely state that your knowledge is limited to "{submodule_title}" and suggest they refer to the relevant module/submodule in the Learning Path Structure if applicable. Do NOT answer questions outside your scope.
3.  **Be Conversational:** Maintain a helpful and encouraging tone.
4.  **No External Knowledge:** Do not use any information beyond the provided SUBMODULE CONTENT and LEARNING PATH STRUCTURE.
5.  **Language Flexibility:** By default, respond in {language}. However, if the user is clearly communicating in a different language, adapt and respond in that same language to provide the best user experience. Always prioritize the language the user is actively using, even if it differs from the learning path's configured language.
6.  **Clarity:** If a question is ambiguous, ask for clarification before answering.
7.  **Completeness:** Answer the user's query fully based on the provided content. If the content doesn't cover it, state that.
"""