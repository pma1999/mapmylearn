/**
 * Custom DOMPurify configuration and utilities to prevent DOM Clobbering attacks,
 * particularly targeting the PrismJS vulnerability (CVE related to document.currentScript)
 */
import DOMPurify from 'dompurify';

/**
 * Configure DOMPurify globally to prevent DOM Clobbering attacks
 * This is specifically designed to mitigate the PrismJS vulnerability 
 * where document.currentScript lookup can be shadowed by attacker-injected HTML
 */
export function configureDOMPurify() {
  // Prevent DOM clobbering for common properties that could be abused
  const CLOBBERING_ELEMENTS = ['script', 'object', 'embed', 'form', 'input'];
  
  // Hook into DOMPurify's configuration
  DOMPurify.addHook('beforeSanitizeElements', (node) => {
    // Specifically check for elements that could clobber document.currentScript
    if (node.nodeName && node.nodeName.toLowerCase() === 'script') {
      // Add a custom attribute to real scripts to distinguish them
      node.setAttribute('data-sanitized', 'true');
    }
    
    // Check for DOM clobbering attempts where element's id/name matches currentScript
    if (node.hasAttribute && (
      node.hasAttribute('id') && node.getAttribute('id') === 'currentScript' ||
      node.hasAttribute('name') && node.getAttribute('name') === 'currentScript'
    )) {
      // Either remove the attribute or change it to something harmless
      node.removeAttribute('id');
      node.removeAttribute('name');
    }
    
    return node;
  });
  
  // Set the default configuration for all DOMPurify calls
  DOMPurify.setConfig({
    FORBID_TAGS: CLOBBERING_ELEMENTS,
    FORBID_ATTR: ['id', 'name', 'class', 'style', 'srcset', 'rel'],
    ADD_ATTR: ['target'],
    ALLOW_DATA_ATTR: false,
    USE_PROFILES: { html: true }
  });
}

/**
 * Sanitize HTML content, specifically configured to prevent DOM Clobbering attacks
 * targeting PrismJS vulnerabilities
 * 
 * @param {string} content - The HTML content to sanitize
 * @param {Object} options - Additional DOMPurify options (optional)
 * @returns {string} - Sanitized HTML content
 */
export function sanitizeContent(content, options = {}) {
  if (!content) return '';
  
  // Ensure DOMPurify is configured
  if (!DOMPurify.isConfigured) {
    configureDOMPurify();
  }
  
  // Combine default options with any custom options
  const sanitizeOptions = {
    ...options
  };
  
  // Return sanitized content
  return DOMPurify.sanitize(String(content), sanitizeOptions);
}

/**
 * Initialize sanitization on application startup
 * Call this function in your application's entry point
 */
export function initializeSanitizer() {
  configureDOMPurify();
  console.debug('DOM Sanitization initialized with PrismJS vulnerability protection');
}

export default {
  sanitizeContent,
  configureDOMPurify,
  initializeSanitizer
}; 