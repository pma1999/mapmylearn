/**
 * Utilities for parsing markdown content and extracting headers for table of contents
 * functionality. Provides efficient header extraction without full markdown rendering.
 */

/**
 * Generates a URL-safe ID from header text
 * @param {string} text - The header text
 * @param {Set} usedIds - Set of already used IDs to ensure uniqueness
 * @returns {string} - Unique URL-safe ID
 */
export const generateHeaderId = (text, usedIds = new Set()) => {
  if (!text || typeof text !== 'string') return 'heading';
  
  const strippedText = stripMarkdownFormatting(text);

  // Convert to lowercase, replace spaces and special chars with hyphens
  let baseId = strippedText
    .toLowerCase()
    .trim()
    // Normalize Unicode characters (e.g., converts accented characters to base form)
    .normalize('NFD')
    // Remove diacritical marks but preserve letters
    .replace(/[\u0300-\u036f]/g, '')
    // Keep Unicode letters, digits, spaces, and hyphens only
    .replace(/[^\p{L}\p{N}\s-]/gu, '')
    .replace(/\s+/g, '-') // Replace spaces with hyphens
    .replace(/-+/g, '-') // Replace multiple hyphens with single
    .replace(/^-|-$/g, ''); // Remove leading/trailing hyphens
  
  // Ensure it starts with a letter (HTML ID requirement)
  if (!/^[a-z\p{L}]/u.test(baseId)) {
    baseId = `heading-${baseId}`;
  }
  
  // Handle empty or invalid IDs
  if (!baseId) {
    baseId = 'heading';
  }
  
  // Ensure uniqueness
  let finalId = baseId;
  let counter = 1;
  while (usedIds.has(finalId)) {
    finalId = `${baseId}-${counter}`;
    counter++;
  }
  
  usedIds.add(finalId);
  return finalId;
};

/**
 * Strips markdown formatting characters from text while preserving readability
 * @param {string} text - Text that may contain markdown formatting
 * @returns {string} Clean text without markdown formatting characters
 */
export const stripMarkdownFormatting = (text) => {
  if (!text || typeof text !== 'string') {
    return '';
  }

  return text
    // Remove inline code formatting (`text`)
    .replace(/`([^`]+)`/g, '$1')
    // Images: ![alt](url) -> alt
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
    // Links: [text](url) -> text
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    // Remove HTML tags
    .replace(/<[^>]+>/g, '')
    // Remove bold and italic (***text*** or ___text___)
    .replace(/(\*\*\*|___)(.+?)\1/g, '$2')
    // Remove bold (**text** or __text__)
    .replace(/(\*\*|__)(.+?)\1/g, '$2')
    // Remove italic (*text* or _text_)
    .replace(/(\*|_)(.+?)\1/g, '$2')
    // Remove strikethrough (~~text~~)
    .replace(/~~(.+?)~~/g, '$1')
    // Unescape escaped markdown characters (e.g., \* \_ \#)
    .replace(/\\([\\`*_{}\[\]()#+\-.!])/g, '$1')
    // Collapse whitespace
    .replace(/\s+/g, ' ')
    // Clean up any remaining whitespace
    .trim();
};

/**
 * Extracts headers from markdown content
 * @param {string} markdownContent - Raw markdown content
 * @returns {Array} - Array of header objects with id, level, title, and position
 */
export const parseMarkdownHeaders = (markdownContent) => {
  if (!markdownContent || typeof markdownContent !== 'string') {
    return [];
  }
  
  const headers = [];
  const usedIds = new Set();
  
  // Regex to match markdown headers (# ## ### etc.)
  // Matches: start of line, 1-6 hashes, space, then text until end of line
  const headerRegex = /^(#{1,6})\s+(.+)$/gm;
  let match;
  
  while ((match = headerRegex.exec(markdownContent)) !== null) {
    const level = match[1].length; // Number of # characters
    const rawTitle = match[2].trim();
    const title = stripMarkdownFormatting(rawTitle);
    const position = match.index;
    
    // Skip empty titles
    if (!title) continue;
    
    // Generate unique ID
    const id = generateHeaderId(rawTitle, usedIds);
    
    headers.push({
      id,
      level,
      title,
      originalText: match[0], // Full matched text
      position
    });
  }
  
  return headers;
};

/**
 * Creates a nested structure from flat headers array (for future hierarchical TOC)
 * @param {Array} headers - Flat array of header objects
 * @returns {Array} - Nested array of header objects with children
 */
export const createNestedHeaderStructure = (headers) => {
  if (!Array.isArray(headers) || headers.length === 0) {
    return [];
  }
  
  const nested = [];
  const stack = []; // Stack to track parent headers
  
  headers.forEach(header => {
    const newHeader = { ...header, children: [] };
    
    // Find the appropriate parent level
    while (stack.length > 0 && stack[stack.length - 1].level >= header.level) {
      stack.pop();
    }
    
    if (stack.length === 0) {
      // Top level header
      nested.push(newHeader);
    } else {
      // Child header
      stack[stack.length - 1].children.push(newHeader);
    }
    
    stack.push(newHeader);
  });
  
  return nested;
};

/**
 * Validates if markdown content has any headers
 * @param {string} markdownContent - Raw markdown content
 * @returns {boolean} - True if content has headers, false otherwise
 */
export const hasMarkdownHeaders = (markdownContent) => {
  if (!markdownContent || typeof markdownContent !== 'string') {
    return false;
  }
  
  const headerRegex = /^#{1,6}\s+.+$/m;
  return headerRegex.test(markdownContent);
};

/**
 * Finds the closest header to a given scroll position
 * @param {Array} headers - Array of header objects with position data
 * @param {number} scrollPosition - Current scroll position in characters
 * @returns {string|null} - ID of the closest header, or null if none found
 */
export const findClosestHeader = (headers, scrollPosition) => {
  if (!Array.isArray(headers) || headers.length === 0) {
    return null;
  }
  
  // Find the last header that comes before or at the current position
  let closestHeader = null;
  
  for (const header of headers) {
    if (header.position <= scrollPosition) {
      closestHeader = header;
    } else {
      break; // Headers are ordered by position
    }
  }
  
  return closestHeader?.id || headers[0]?.id || null;
};
