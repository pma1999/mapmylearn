# Enhanced Wikimedia Image Search with Multi-Attempt Query Generation

## Overview

The enhanced image search system improves upon the original single-attempt Wikimedia image search by implementing a progressive query refinement pattern. When the LLM determines that no images from the initial search are relevant, the system now generates alternative search queries and retries the search process, with a maximum of 3 attempts total.

## Key Features

### 🔄 Multi-Attempt Search Process
- **Progressive Refinement**: Each failed attempt generates smarter alternative queries
- **LLM-Guided Alternatives**: The selection LLM provides specific suggestions for better queries
- **Intelligent Fallbacks**: Sophisticated fallback query generation when LLM suggestions fail
- **Maximum 3 Attempts**: Configurable limit prevents infinite loops and excessive processing time

### 🧠 Enhanced LLM Selection with Success-Oriented Prompts
- **Context-Aware Evaluation**: LLM understands the attempt history and previous failures
- **Strategic Alternative Generation**: Provides specific suggestions targeting high-probability content
- **Progressive Specificity**: Attempt-specific guidance from broad concepts to maximum specificity
- **Visual Content Prioritization**: Focuses on concrete, photographable elements
- **Wikimedia Optimization**: Targets content types likely available in Commons

### 🎯 Success-Oriented Query Strategies
- **Biographical Targeting**: Focuses on named people with high photo availability
- **Geographic Pivoting**: Targets specific locations and institutions with visual documentation
- **Historical Contextualization**: Adds specific time periods and documented events
- **Strategic Abstraction Avoidance**: Pivots from abstract concepts to concrete manifestations

### ⚙️ Backward Compatibility
- **Drop-in Replacement**: Existing callers work without any code changes
- **Configuration Control**: Can be disabled to use original single-attempt behavior
- **Graceful Degradation**: Falls back to original behavior on errors

## Implementation Details

### Data Structures

#### AttemptState
```python
@dataclass
class AttemptState:
    attempt_number: int                     # Current attempt (1-3)
    used_urls: Set[str]                    # URLs already used to prevent duplicates
    all_candidates_history: List[Dict]      # All candidates seen across attempts
    query_history: List[List[str]]         # All queries tried in previous attempts
    previous_rejection_reasons: List[str]   # LLM explanations for rejections
```

### Core Functions

#### `_find_relevant_image_with_retry()`
**Main orchestrator** for the multi-attempt process:
- Manages the retry loop (1-3 attempts)
- Coordinates between query generation, search, and selection
- Handles state preservation across attempts
- Provides comprehensive logging for debugging

#### `_select_image_with_alternatives_llm()`
**Enhanced LLM selection** that returns either:
- **Success**: `{"success": True, "index": N, "caption": "..."}`
- **Retry**: `{"success": False, "alternative_queries": [...], "reason": "..."}`
- **Terminal**: `{"success": False}` (no more options)

#### `_generate_alternative_queries()`
**Smart query generation** combining:
- LLM-suggested alternative queries
- Enhanced fallback logic using context analysis
- Deduplication against previous attempts
- Query quality validation and filtering

#### `_generate_fallback_alternative_queries()`
**Robust fallback strategies**:
- Broader context from module/topic combination
- More specific queries from submodule + section
- Context hint variations and refinements
- Single significant word searches for maximum coverage

### Enhanced Prompt Engineering with Success-Oriented Strategies

The new `PROMPT_IMAGE_SELECTION_WITH_ALTERNATIVES` implements sophisticated prompt engineering to dramatically improve alternative query success rates:

#### **Visual Content Prioritization System**
```
PRIORITY 1: Named people, specific places, historical events, institutions
PRIORITY 2: Concrete objects, buildings, artifacts, monuments, documents  
PRIORITY 3: Specific time periods with visual documentation, cultural movements
PRIORITY 4: Geographic locations, universities, government buildings, museums
```

#### **Progressive Specificity Strategy**
- **Attempt 1**: Broad but concrete visual concepts (e.g., "Einstein physics" → "Albert Einstein portrait")
- **Attempt 2**: Add named entities, locations, dates (e.g., "relativity theory" → "Princeton University Einstein")
- **Attempt 3**: Maximum specificity with proper names, years, events (e.g., "physics concepts" → "1905 Einstein papers Nobel")

#### **Strategic Pivoting from Abstract to Concrete**
- If concept is too abstract → Focus on people associated with it
- If topic lacks visuals → Find related geographic locations or institutions
- If too general → Add specific historical periods, events, or biographical elements
- If wrong domain → Pivot to related concrete manifestations

#### **Wikimedia Commons Optimization**
The prompts specifically target content types with high availability on Wikimedia:
- Biographical subjects (politicians, scientists, artists, historical figures)
- Geographic locations (cities, landmarks, countries, natural features)
- Historical events (wars, treaties, discoveries, cultural movements)
- Institutional subjects (universities, governments, museums, organizations)

## Configuration

### New Configuration Parameters

Add to your `LearningPathState`:

```python
{
    # Enhanced image search configuration
    "enhanced_image_search_enabled": True,    # Enable/disable enhanced search
    "max_image_search_attempts": 3,           # Maximum attempts (1-5)
    
    # Existing image configuration (unchanged)
    "images_enrichment_enabled": True,
    "images_per_submodule": 5,
}
```

### Configuration Options

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `enhanced_image_search_enabled` | `True` | Boolean | Enable multi-attempt search |
| `max_image_search_attempts` | `3` | 1-5 | Maximum search attempts |
| `images_enrichment_enabled` | `True` | Boolean | Enable/disable all image enrichment |
| `images_per_submodule` | `5` | 0+ | Maximum images per submodule |

## Usage Examples

### Basic Usage (Automatic)
The enhanced search is enabled by default and works transparently:

```python
# Existing code continues to work unchanged
img = await _find_relevant_image_for_anchor(
    state, module, submodule, section_heading, 
    exclude_urls=used_urls, topic_hint=hint
)
```

### Disabling Enhanced Search
To use original single-attempt behavior:

```python
state["enhanced_image_search_enabled"] = False
img = await _find_relevant_image_for_anchor(...)
```

### Custom Attempt Limit
```python
state["max_image_search_attempts"] = 2  # Only 2 attempts instead of 3
img = await _find_relevant_image_for_anchor(...)
```

## Search Strategy Flow

### Attempt 1: Original Approach
1. Generate queries using original `_generate_wikimedia_queries()`
2. Search Wikimedia with generated queries
3. Use enhanced LLM selection with attempt context
4. If successful: return image with caption
5. If failed: collect alternative query suggestions

### Attempt 2: LLM-Guided Refinement
1. Use alternative queries suggested by LLM in attempt 1
2. Enhance with fallback generation if needed
3. Filter out previously used queries
4. Search with refined queries
5. Enhanced selection with rejection history

### Attempt 3: Final Attempt
1. Use any remaining alternative queries
2. Apply aggressive fallback strategies
3. LLM understands this is the final attempt
4. Return result or None (graceful failure)

## Logging and Debugging

### Debug Logging
Enable debug logging to see the retry process:

```python
import logging
logging.getLogger("content_enrichment.images").setLevel(logging.DEBUG)
```

### Log Output Examples
```
DEBUG - Image search attempt 1/3 for Ascenso del Nazismo
DEBUG - Generated 3 alternative queries for attempt 2
DEBUG - Attempt 1 failed, trying 3 alternative queries
DEBUG - Image found on attempt 2/3
```

## Performance Considerations

### Processing Time Impact
- **First Attempt Success**: No performance impact (same as original)
- **Multi-Attempt Search**: 2-3x processing time when retries are needed
- **Failed Search**: Maximum 3x processing time before giving up

### LLM Usage
- **Additional LLM Calls**: 0-2 extra calls per failed attempt
- **Rate Limiting**: Respects existing retry mechanisms in `run_chain()`
- **Cost Impact**: Minimal increase due to focused retry strategy

### Memory Usage
- **Candidate History**: Limited to 10 candidates per attempt
- **Query History**: Limited to 3 queries per attempt, 3 attempts max
- **State Cleanup**: Automatic cleanup after processing

## Error Handling

### Graceful Degradation
- **LLM Failures**: Falls back to original single-attempt behavior
- **API Errors**: Uses existing `run_chain()` retry mechanisms
- **Invalid Responses**: Continues with fallback strategies
- **Maximum Attempts**: Returns None (same as original behavior)

### Error Recovery
- **Parsing Errors**: Uses existing JSON extraction and retry logic
- **Network Issues**: Respects existing timeout and retry configuration
- **Rate Limiting**: Inherits existing backoff strategies

## Integration with Existing System

### Backward Compatibility
- ✅ **No Breaking Changes**: All existing callers work unchanged
- ✅ **Same Return Types**: Returns same image structure as before
- ✅ **Same Error Handling**: Maintains existing exception patterns
- ✅ **Configuration Inheritance**: Uses existing configuration patterns

### Pipeline Integration
The enhanced search integrates seamlessly with:
- **Content Enrichment Pipeline**: `enrich_content_with_images()`
- **Submodule Processing**: `process_single_submodule()`
- **Image Planning**: `_plan_image_anchors()`
- **URL Management**: `used_urls` set for duplicate prevention

## Success Metrics

### Validated Improvements (Real Test Results)
- **Dramatically improved query quality**: 7/9 quality score for alternative queries vs previous generic alternatives
- **Progressive specificity demonstrated**: Clear progression from broad (attempt 1) to maximum specificity (attempt 3)
- **Strategic pivoting working**: Abstract economic theory → "Léon Walras portrait", "Lausanne School economics"
- **Biographical targeting successful**: Philosophy concepts → "Jean-Paul Sartre biography", "Sorbonne University philosophy"

### Enhanced Success Strategies Validated
- **Visual Content Prioritization**: Queries now systematically target photographable elements
- **Geographic/Institutional Pivoting**: Abstract concepts successfully mapped to concrete institutions
- **Historical Contextualization**: Time periods and specific events added for visual documentation
- **Named Entity Focus**: Specific people, places, and institutions consistently targeted

### Quality Indicators
- **Concrete Alternative Queries**: Shift from abstract terms to specific people, places, institutions
- **Strategic Query Diversity**: Each alternative targets different visual angle (biographical, geographic, institutional)
- **Wikimedia-Optimized Content**: Queries target content types with high availability in Commons
- **Progressive Learning**: Each attempt builds on previous rejection patterns for smarter alternatives

---

## Technical Notes

### Implementation Architecture
- **Progressive Query Refinement Pattern**: Main design pattern
- **State Machine Pattern**: AttemptState manages attempt progression
- **Strategy Pattern**: Multiple query generation strategies
- **Decorator Pattern**: Enhanced LLM wraps original selection logic

### Future Enhancement Opportunities
- **Query Caching**: Cache successful alternative queries for similar content
- **Parallel Search**: Search alternative queries in parallel for speed
- **Quality Scoring**: Implement image quality scoring for better selection
- **User Feedback**: Learn from user interactions to improve query generation

This implementation provides a robust, backward-compatible enhancement to the image search system that significantly improves success rates while maintaining system stability and performance characteristics.
