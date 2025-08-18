# Implementation Plan

[Overview]
Implement a comprehensive return URL mechanism to redirect users to their intended destination after authentication, replacing the current hardcoded redirect to the course generation page.

This implementation addresses the user experience issue where users who are logged out due to session expiration are always redirected to `/generate` after re-authentication, regardless of which page they were originally trying to access. The solution provides a secure, robust return URL system that preserves the user's intended destination while preventing security vulnerabilities like open redirects.

[Types]
Create utility functions and validation logic for URL handling and security checks.

```typescript
// URL validation and security utilities
interface ReturnUrlValidation {
  isValid: boolean;
  sanitizedUrl: string;
  reason?: string;
}

// Return URL utility functions
type ValidateReturnUrl = (url: string) => ReturnUrlValidation;
type GetReturnUrl = (location: Location) => string | null;
type SetReturnUrl = (returnUrl: string) => string;
```

[Files]
Create one new utility file and modify two existing components to implement the return URL functionality.

**New files to create:**
- `frontend/src/utils/returnUrlUtils.js` - Utility functions for return URL validation, sanitization, and security checks

**Existing files to modify:**
- `frontend/src/components/ProtectedRoute.js` - Update redirect logic to properly encode and pass return URL
- `frontend/src/pages/LoginPage.js` - Enhanced return URL extraction, validation, and post-login redirection logic

[Functions]
Add URL validation utilities and enhance existing authentication flow functions.

**New functions in `frontend/src/utils/returnUrlUtils.js`:**
- `validateReturnUrl(url)` - Validates and sanitizes return URLs to prevent open redirects
- `getReturnUrlFromLocation(location)` - Extracts return URL from React Router state or URL parameters  
- `createReturnUrlParams(returnUrl)` - Creates URL parameters for return URL with fallback mechanisms
- `isAllowedReturnUrl(pathname)` - Checks if a pathname is in the allowed internal routes whitelist

**Modified functions in `frontend/src/components/ProtectedRoute.js`:**
- Update redirect logic in main component body to encode current location as return URL parameter

**Modified functions in `frontend/src/pages/LoginPage.js`:**
- Enhance return URL extraction logic in component setup
- Add URL validation before navigation in `useEffect` dependency
- Update error handling for invalid return URLs

[Classes]
No new classes required - implementation uses functional components and utility functions.

All existing React functional components (`ProtectedRoute` and `LoginPage`) will be enhanced with additional logic but retain their current structure and component patterns.

[Dependencies]
No new external dependencies required - implementation uses existing React Router and browser APIs.

The implementation leverages:
- `react-router` - Already available for location and navigation handling
- Native browser `URLSearchParams` and `URL` APIs for URL manipulation and validation
- Existing project utilities and patterns

[Testing]
Create comprehensive test coverage for URL validation and authentication flow scenarios.

**Test files to create/update:**
- `frontend/src/utils/__tests__/returnUrlUtils.test.js` - Unit tests for URL validation utilities
- Add test cases to existing component tests for `ProtectedRoute` and `LoginPage`

**Test scenarios to cover:**
- Valid internal return URLs (courses, history, admin pages)
- Invalid return URLs (external sites, malicious payloads)
- Edge cases (missing return URLs, malformed URLs, special characters)
- Authentication flow with various return URL scenarios
- Security validation (XSS prevention, open redirect prevention)

[Implementation Order]
Sequential implementation to ensure stable functionality and proper testing at each stage.

1. **Create URL utilities** - Implement `frontend/src/utils/returnUrlUtils.js` with validation and security functions
2. **Update ProtectedRoute** - Modify `frontend/src/components/ProtectedRoute.js` to capture and encode return URLs
3. **Update LoginPage** - Enhance `frontend/src/pages/LoginPage.js` with improved return URL handling
4. **Add comprehensive testing** - Create test suites for utilities and component functionality  
5. **Security validation** - Review and test security measures against common attack vectors
6. **Integration testing** - Test complete authentication flow with various scenarios
7. **Documentation** - Document the new return URL system for future maintenance
