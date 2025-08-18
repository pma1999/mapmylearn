/**
 * Test suite for return URL utilities
 * Comprehensive security and functionality testing
 */

import {
  validateReturnUrl,
  isAllowedReturnUrl,
  getReturnUrlFromLocation,
  createReturnUrlParams,
  getDefaultReturnUrl,
  navigateToReturnUrl
} from '../returnUrlUtils';

describe('Return URL Utilities', () => {
  // Mock window.location for testing
  const originalLocation = window.location;
  
  beforeAll(() => {
    delete window.location;
    window.location = { origin: 'https://mapmylearn.com' };
  });

  afterAll(() => {
    window.location = originalLocation;
  });

  describe('isAllowedReturnUrl', () => {
    test('should allow valid internal routes', () => {
      const validPaths = [
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

      validPaths.forEach(path => {
        expect(isAllowedReturnUrl(path)).toBe(true);
      });
    });

    test('should allow paths with parameters', () => {
      const validPathsWithParams = [
        '/course/123',
        '/learning-path/abc-def',
        '/learning-paths/category/science',
        '/admin/users',
        '/history/recent'
      ];

      validPathsWithParams.forEach(path => {
        expect(isAllowedReturnUrl(path)).toBe(true);
      });
    });

    test('should reject invalid paths', () => {
      const invalidPaths = [
        '/invalid',
        '/malicious',
        '/external',
        '/api/users',
        '/login',
        '/register',
        '/../etc/passwd',
        '/generate/../admin'
      ];

      invalidPaths.forEach(path => {
        expect(isAllowedReturnUrl(path)).toBe(false);
      });
    });

    test('should handle edge cases', () => {
      expect(isAllowedReturnUrl(null)).toBe(false);
      expect(isAllowedReturnUrl(undefined)).toBe(false);
      expect(isAllowedReturnUrl('')).toBe(false);
      expect(isAllowedReturnUrl(123)).toBe(false);
    });

    test('should normalize paths with or without leading slash', () => {
      expect(isAllowedReturnUrl('generate')).toBe(true);
      expect(isAllowedReturnUrl('/generate')).toBe(true);
    });
  });

  describe('validateReturnUrl', () => {
    test('should validate relative URLs correctly', () => {
      const result = validateReturnUrl('/courses/123');
      expect(result.isValid).toBe(true);
      expect(result.sanitizedUrl).toBe('/courses/123');
    });

    test('should validate relative URLs with query parameters', () => {
      const result = validateReturnUrl('/history?page=2&filter=recent');
      expect(result.isValid).toBe(true);
      expect(result.sanitizedUrl).toBe('/history?page=2&filter=recent');
    });

    test('should reject external URLs', () => {
      const externalUrls = [
        'https://evil.com/steal-data',
        'http://malicious.site.com/phishing',
        'https://external-domain.com/courses',
        'ftp://file-server.com/files'
      ];

      externalUrls.forEach(url => {
        const result = validateReturnUrl(url);
        expect(result.isValid).toBe(false);
        expect(result.sanitizedUrl).toBe('/generate');
        expect(result.reason).toBe('External URL not allowed');
      });
    });

    test('should handle same-origin URLs', () => {
      const result = validateReturnUrl('https://mapmylearn.com/courses/123');
      expect(result.isValid).toBe(true);
      expect(result.sanitizedUrl).toBe('/courses/123');
    });

    test('should reject invalid paths on same origin', () => {
      const result = validateReturnUrl('https://mapmylearn.com/malicious-path');
      expect(result.isValid).toBe(false);
      expect(result.sanitizedUrl).toBe('/generate');
      expect(result.reason).toBe('Path not in allowed routes');
    });

    test('should handle malformed URLs', () => {
      const malformedUrls = [
        'not-a-url',
        '://invalid',
        'javascript:alert("xss")',
        'data:text/html,<script>alert("xss")</script>',
        'vbscript:msgbox("xss")'
      ];

      malformedUrls.forEach(url => {
        const result = validateReturnUrl(url);
        expect(result.isValid).toBe(false);
        expect(result.sanitizedUrl).toBe('/generate');
      });
    });

    test('should handle null/undefined inputs', () => {
      const nullResult = validateReturnUrl(null);
      expect(nullResult.isValid).toBe(false);
      expect(nullResult.sanitizedUrl).toBe('/generate');
      expect(nullResult.reason).toBe('Invalid or missing URL');

      const undefinedResult = validateReturnUrl(undefined);
      expect(undefinedResult.isValid).toBe(false);
      expect(undefinedResult.sanitizedUrl).toBe('/generate');
      expect(undefinedResult.reason).toBe('Invalid or missing URL');
    });

    test('should preserve hash and search parameters for valid URLs', () => {
      const result = validateReturnUrl('https://mapmylearn.com/courses/123?tab=overview#section-1');
      expect(result.isValid).toBe(true);
      expect(result.sanitizedUrl).toBe('/courses/123?tab=overview#section-1');
    });

    // Security-focused tests
    test('should prevent XSS attacks in URLs', () => {
      const xssAttempts = [
        '/courses/<script>alert("xss")</script>',
        '/history?search=<img src=x onerror=alert("xss")>',
        '/admin#<svg onload=alert("xss")>',
        'javascript:void(0);alert("xss")'
      ];

      xssAttempts.forEach(url => {
        const result = validateReturnUrl(url);
        // Even if path matches allowed pattern, malicious content should be rejected
        expect(result.isValid).toBe(false);
      });
    });

    test('should prevent path traversal attacks', () => {
      const pathTraversalAttempts = [
        '/courses/../../../etc/passwd',
        '/history/../admin/users',
        '/generate/../../login',
        '/../courses/123'
      ];

      pathTraversalAttempts.forEach(url => {
        const result = validateReturnUrl(url);
        expect(result.isValid).toBe(false);
      });
    });
  });

  describe('getReturnUrlFromLocation', () => {
    test('should extract URL from location state', () => {
      const location = {
        state: {
          from: '/courses/123'
        }
      };

      const result = getReturnUrlFromLocation(location);
      expect(result).toBe('/courses/123');
    });

    test('should extract URL from location state object', () => {
      const location = {
        state: {
          from: {
            pathname: '/history',
            search: '?page=2'
          }
        }
      };

      const result = getReturnUrlFromLocation(location);
      expect(result).toBe('/history?page=2');
    });

    test('should extract URL from search parameters', () => {
      const location = {
        search: '?returnUrl=%2Fcourses%2F123'
      };

      const result = getReturnUrlFromLocation(location);
      expect(result).toBe('/courses/123');
    });

    test('should prioritize state over search params', () => {
      const location = {
        state: {
          from: '/courses/456'
        },
        search: '?returnUrl=%2Fcourses%2F123'
      };

      const result = getReturnUrlFromLocation(location);
      expect(result).toBe('/courses/456');
    });

    test('should return null for invalid URLs', () => {
      const location = {
        state: {
          from: '/invalid-path'
        }
      };

      const result = getReturnUrlFromLocation(location);
      expect(result).toBeNull();
    });

    test('should handle missing location', () => {
      expect(getReturnUrlFromLocation(null)).toBeNull();
      expect(getReturnUrlFromLocation(undefined)).toBeNull();
    });
  });

  describe('createReturnUrlParams', () => {
    test('should create URL parameters for valid return URL', () => {
      const result = createReturnUrlParams('/courses/123');
      expect(result).toBe('?returnUrl=%2Fcourses%2F123');
    });

    test('should return empty string for invalid URLs', () => {
      expect(createReturnUrlParams('/invalid-path')).toBe('');
      expect(createReturnUrlParams(null)).toBe('');
      expect(createReturnUrlParams(undefined)).toBe('');
    });

    test('should properly encode complex URLs', () => {
      const complexUrl = '/courses/123?filter=science&sort=date#section-2';
      const result = createReturnUrlParams(complexUrl);
      expect(result).toContain('returnUrl=');
      expect(decodeURIComponent(result.split('returnUrl=')[1])).toBe(complexUrl);
    });
  });

  describe('getDefaultReturnUrl', () => {
    test('should return default URL', () => {
      expect(getDefaultReturnUrl()).toBe('/generate');
    });
  });

  describe('navigateToReturnUrl', () => {
    test('should navigate to valid return URL', () => {
      const mockNavigate = jest.fn();
      navigateToReturnUrl(mockNavigate, '/courses/123');
      
      expect(mockNavigate).toHaveBeenCalledWith('/courses/123', { replace: true });
    });

    test('should navigate to default URL for invalid return URL', () => {
      const mockNavigate = jest.fn();
      navigateToReturnUrl(mockNavigate, '/invalid-path');
      
      expect(mockNavigate).toHaveBeenCalledWith('/generate', { replace: true });
    });

    test('should pass through navigation options', () => {
      const mockNavigate = jest.fn();
      const options = { replace: false, state: { from: 'test' } };
      navigateToReturnUrl(mockNavigate, '/courses/123', options);
      
      expect(mockNavigate).toHaveBeenCalledWith('/courses/123', { replace: true, state: { from: 'test' } });
    });
  });

  // Integration security tests
  describe('Security Integration Tests', () => {
    test('should prevent open redirect attack via multiple vectors', () => {
      const maliciousUrls = [
        'https://evil.com',
        '//evil.com',
        '/\\evil.com',
        'https:evil.com',
        'https://mapmylearn.com.evil.com'
      ];

      maliciousUrls.forEach(url => {
        const result = validateReturnUrl(url);
        expect(result.isValid).toBe(false);
        expect(result.sanitizedUrl).toBe('/generate');
      });
    });

    test('should handle URL encoding bypass attempts', () => {
      const encodingBypassAttempts = [
        '%2F%2Fevil.com',
        '%5c%5cevil.com', 
        '%68%74%74%70%73%3a%2f%2fexample.com',
        decodeURIComponent('%252F%252Fevil.com')
      ];

      encodingBypassAttempts.forEach(url => {
        const result = validateReturnUrl(url);
        expect(result.isValid).toBe(false);
      });
    });

    test('should be resistant to protocol confusion', () => {
      const protocolConfusionAttempts = [
        'javascript://valid.path%0Aalert(1)',
        'data://valid.path,<script>alert(1)</script>',
        'vbscript://valid.path%0Amsgbox("xss")'
      ];

      protocolConfusionAttempts.forEach(url => {
        const result = validateReturnUrl(url);
        expect(result.isValid).toBe(false);
      });
    });
  });
});
