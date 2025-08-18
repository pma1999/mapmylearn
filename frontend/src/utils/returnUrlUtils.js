/**
 * Return URL Utilities
 * Provides secure URL validation, sanitization, and handling for authentication redirects
 */

// Whitelist of allowed internal routes for return URLs
const ALLOWED_RETURN_PATHS = [
  '/generate',
  '/generator',
  '/history',
  '/admin',
  '/courses',
  '/course',
  '/learning-path',
  '/learning-paths',
  '/profile',
  '/settings',
  '/chat',
  '/chatbot'
];

/**
 * Validates if a pathname is in the allowed internal routes whitelist
 * @param {string} pathname - The pathname to check
 * @returns {boolean} True if the pathname is allowed
 */
export const isAllowedReturnUrl = (pathname) => {
  if (!pathname || typeof pathname !== 'string') {
    return false;
  }

  // Remove leading slash for consistent comparison
  const normalizedPath = pathname.startsWith('/') ? pathname : `/${pathname}`;
  
  // Security check: reject paths with suspicious patterns
  if (normalizedPath.includes('..') || 
      normalizedPath.includes('<') || 
      normalizedPath.includes('>') || 
      normalizedPath.includes('script') ||
      normalizedPath.includes('javascript:') ||
      normalizedPath.includes('data:') ||
      normalizedPath.includes('vbscript:')) {
    return false;
  }
  
  // Check exact matches and path prefixes
  return ALLOWED_RETURN_PATHS.some(allowedPath => {
    // Exact match
    if (normalizedPath === allowedPath) return true;
    
    // Prefix match (e.g., '/course/123' matches '/course')
    if (normalizedPath.startsWith(allowedPath + '/')) return true;
    
    return false;
  });
};

/**
 * Validates and sanitizes return URLs to prevent open redirects and security vulnerabilities
 * @param {string} url - The return URL to validate
 * @returns {Object} Validation result with isValid, sanitizedUrl, and optional reason
 */
export const validateReturnUrl = (url) => {
  if (!url || typeof url !== 'string') {
    return {
      isValid: false,
      sanitizedUrl: '/generate',
      reason: 'Invalid or missing URL'
    };
  }

  // Security check: reject dangerous protocols and patterns
  const dangerousPatterns = [
    'javascript:',
    'data:',
    'vbscript:',
    '<script',
    '</script',
    'onerror=',
    'onload=',
    '%3Cscript',
    '%3C/script'
  ];
  
  const lowerUrl = url.toLowerCase();
  if (dangerousPatterns.some(pattern => lowerUrl.includes(pattern))) {
    return {
      isValid: false,
      sanitizedUrl: '/generate',
      reason: 'Dangerous content detected'
    };
  }

  try {
    // Handle relative URLs
    if (url.startsWith('/')) {
      const pathname = url.split('?')[0]; // Remove query parameters for validation
      
      if (isAllowedReturnUrl(pathname)) {
        return {
          isValid: true,
          sanitizedUrl: url
        };
      } else {
        return {
          isValid: false,
          sanitizedUrl: '/generate',
          reason: 'Path not in allowed routes'
        };
      }
    }

    // Handle absolute URLs - check if they're internal
    const urlObj = new URL(url);
    const currentOrigin = window.location.origin;
    
    // Only allow URLs from the same origin
    if (urlObj.origin !== currentOrigin) {
      return {
        isValid: false,
        sanitizedUrl: '/generate',
        reason: 'External URL not allowed'
      };
    }

    // Check if the pathname is allowed
    if (isAllowedReturnUrl(urlObj.pathname)) {
      // Return only the pathname + search + hash (remove origin)
      const sanitizedUrl = urlObj.pathname + urlObj.search + urlObj.hash;
      return {
        isValid: true,
        sanitizedUrl: sanitizedUrl
      };
    } else {
      return {
        isValid: false,
        sanitizedUrl: '/generate',
        reason: 'Path not in allowed routes'
      };
    }
  } catch (error) {
    return {
      isValid: false,
      sanitizedUrl: '/generate',
      reason: 'Malformed URL'
    };
  }
};

/**
 * Extracts return URL from React Router location state or URL parameters
 * @param {Object} location - React Router location object
 * @returns {string|null} The return URL if found and valid, null otherwise
 */
export const getReturnUrlFromLocation = (location) => {
  if (!location) return null;

  // First, try to get from location state (preferred method)
  if (location.state && location.state.from) {
    const fromUrl = typeof location.state.from === 'string' 
      ? location.state.from 
      : location.state.from.pathname + (location.state.from.search || '');
    
    const validation = validateReturnUrl(fromUrl);
    return validation.isValid ? validation.sanitizedUrl : null;
  }

  // Fallback: try to get from URL search parameters
  if (location.search) {
    const searchParams = new URLSearchParams(location.search);
    const returnUrl = searchParams.get('returnUrl') || searchParams.get('redirect');
    
    if (returnUrl) {
      const validation = validateReturnUrl(decodeURIComponent(returnUrl));
      return validation.isValid ? validation.sanitizedUrl : null;
    }
  }

  return null;
};

/**
 * Creates URL parameters for return URL with fallback mechanisms
 * @param {string} returnUrl - The return URL to encode
 * @returns {string} URL search parameters string
 */
export const createReturnUrlParams = (returnUrl) => {
  if (!returnUrl) return '';
  
  const validation = validateReturnUrl(returnUrl);
  if (!validation.isValid) return '';
  
  const params = new URLSearchParams();
  params.set('returnUrl', validation.sanitizedUrl);
  
  return `?${params.toString()}`;
};

/**
 * Gets the default fallback URL for when no valid return URL is available
 * @returns {string} Default fallback URL
 */
export const getDefaultReturnUrl = () => '/generate';

/**
 * Safely navigates to a return URL after validation
 * @param {Function} navigate - React Router navigate function
 * @param {string} returnUrl - The return URL to navigate to
 * @param {Object} options - Navigation options
 */
export const navigateToReturnUrl = (navigate, returnUrl, options = {}) => {
  const validation = validateReturnUrl(returnUrl);
  const targetUrl = validation.isValid ? validation.sanitizedUrl : getDefaultReturnUrl();
  
  // Always use replace: true for security, but allow other options to be overridden
  navigate(targetUrl, { ...options, replace: true });
};
