import axios from 'axios';

// Use local API when in development mode, Railway API in production
export const API_URL = process.env.NODE_ENV === 'development'
  ? 'http://localhost:8000' 
  : 'https://web-production-62f88.up.railway.app';
console.log('Using API URL:', API_URL);

// Create axios instance with base URL
export const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor to handle standardized error format
api.interceptors.response.use(
  response => response, // Return successful responses as-is
  error => {
    const originalRequest = error.config;
    
    // Check if the error is 401 and needs token refresh
    if (error.response && error.response.status === 401) {
      console.log(`Received 401 for ${originalRequest.url}`);
      
      // IMPORTANT: Check if the original request was NOT to /login or /refresh
      const isLoginOrRefresh = originalRequest.url.includes('/auth/login') || originalRequest.url.includes('/auth/refresh');
      
      // Only attempt refresh if it's not a login/refresh failure and not already retrying
      if (!isLoginOrRefresh && !originalRequest._retry) {
        originalRequest._retry = true;
        console.log('Attempting to refresh token and retry request...');
        
        // Return promise for token refresh and retry logic
        return refreshAuthToken() 
          .then(response => {
            // Token refreshed successfully
            console.log('Token refreshed successfully via interceptor.');
            const { access_token, expires_in, user: userData } = response; 
            // Note: Your refreshAuthToken might need to return the user data too
            // If not, you might need another way to update the user state
            
            // Save new token and user data (this should ideally be handled by authContext)
            // Let's call a function (you might need to import/pass it) or rely on authContext
            // For now, just update the header and retry
            api.setAuthToken(access_token); // Update the header in the api instance
            originalRequest.headers['Authorization'] = `Bearer ${access_token}`;

            // Ideally, update context/localStorage here too
            // updateLocalStorageAndContext(access_token, expires_in, userData); 
            
            return api(originalRequest); // Retry with the original config + new token
          })
          .catch(refreshError => {
            console.error('Token refresh failed during interceptor:', refreshError);
            // Clear potentially invalid auth data and redirect
            clearAuthToken();
            localStorage.removeItem('auth');
            if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
              window.location.href = '/login?session_expired=true';
            }
            return Promise.reject(error); // Reject with the original error after cleanup
          });
      } else if (isLoginOrRefresh) {
        console.log('401 received for login/refresh request, skipping token refresh attempt.');
        // Do not attempt refresh for login/refresh failures
      }
    }
    
    // Format error consistently based on our new API error format
    if (error.response && error.response.data) {
      // Extract the error details from the standardized format
      const errorData = error.response.data;
      let errorMessage = "An unexpected error occurred";
      
      // Check if the error follows our new format with the error object
      if (errorData.error && errorData.error.message) {
        errorMessage = errorData.error.message;
        
        // Attach additional error details if available
        if (errorData.error.details) {
          error.details = errorData.error.details;
        }
        
        if (errorData.error.type) {
          error.type = errorData.error.type;
        }
        
        if (errorData.error.error_id) {
          error.errorId = errorData.error.error_id;
          errorMessage += ` (Error ID: ${error.errorId})`;
        }
      } else if (typeof errorData === 'string') {
        errorMessage = errorData;
      }
      
      // Create a new error with the formatted message
      const formattedError = new Error(errorMessage);
      formattedError.response = error.response;
      formattedError.status = error.response.status;
      formattedError.details = error.details;
      formattedError.type = error.type;
      formattedError.errorId = error.errorId;
      
      return Promise.reject(formattedError);
    }
    
    // If error doesn't match our format, return it as-is
    return Promise.reject(error);
  }
);

// Auth token handling
let authToken = null;
let isRefreshingToken = false;
let refreshSubscribers = [];

// Function to subscribe to token refresh
const subscribeTokenRefresh = (callback) => {
  refreshSubscribers.push(callback);
};

// Function to notify subscribers that token is refreshed
const onTokenRefreshed = (token) => {
  refreshSubscribers.forEach(callback => callback(token));
  refreshSubscribers = [];
};

// Set auth token for API requests
export const setAuthToken = (token) => {
  authToken = token;
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common['Authorization'];
  }
};

// Clear auth token
export const clearAuthToken = () => {
  authToken = null;
  delete api.defaults.headers.common['Authorization'];
};

// Check if token exists in storage and set it
export const initAuthFromStorage = () => {
  try {
    const authData = localStorage.getItem('auth');
    if (authData) {
      const { accessToken } = JSON.parse(authData);
      if (accessToken) {
        setAuthToken(accessToken);
        return true;
      }
    }
  } catch (error) {
    console.error('Error initializing auth token:', error);
    
    // Clear any invalid token data
    localStorage.removeItem('auth');
  }
  return false;
};

// Enhanced function to check auth status
export const checkAuthStatus = async () => {
  try {
    if (!authToken) {
      return { isAuthenticated: false };
    }
    
    // Make a lightweight request to validate the token
    const response = await api.get('/auth/status');
    return { isAuthenticated: true, user: response.data };
  } catch (error) {
    console.error('Auth status check failed:', error);
    
    // If unauthorized, try to refresh the token once
    if (error.response && error.response.status === 401) {
      try {
        // Attempt to refresh the token
        const refreshResponse = await refreshAuthToken();
        if (refreshResponse && refreshResponse.access_token) {
          // Token refreshed successfully, try status check again
          const newResponse = await api.get('/auth/status');
          return { isAuthenticated: true, user: newResponse.data };
        }
      } catch (refreshError) {
        console.error('Token refresh during status check failed:', refreshError);
        // Clear auth data on refresh failure
        clearAuthToken();
        localStorage.removeItem('auth');
      }
    }
    
    return { isAuthenticated: false, error };
  }
};

// Initialize auth token from storage on import
initAuthFromStorage();

// Delete a course task
export const deleteLearningPath = async (taskId) => {
  try {
    const response = await api.delete(`/learning-path/${taskId}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting course:', error);
    throw new Error(error.message || 'Failed to delete course. Please try again.');
  }
};

// Session storage keys for API keys
const GOOGLE_KEY_TOKEN_STORAGE = 'learning_path_google_key_token';
const PPLX_KEY_TOKEN_STORAGE = 'learning_path_pplx_key_token';
const REMEMBER_TOKENS_STORAGE = 'learning_path_remember_tokens';

// API token management functions
export const saveApiTokens = (googleKeyToken, pplxKeyToken, remember = false) => {
  // Only save if remember is true
  if (remember) {
    try {
      // Use sessionStorage for temporary storage during the browser session
      sessionStorage.setItem(GOOGLE_KEY_TOKEN_STORAGE, googleKeyToken || '');
      sessionStorage.setItem(PPLX_KEY_TOKEN_STORAGE, pplxKeyToken || '');
      sessionStorage.setItem(REMEMBER_TOKENS_STORAGE, 'true');
    } catch (error) {
      console.error('Error saving API tokens to session storage:', error);
    }
  } else {
    clearSavedApiTokens();
  }
  
  return { googleKeyToken, pplxKeyToken, remember };
};

export const getSavedApiTokens = () => {
  try {
    const remember = sessionStorage.getItem(REMEMBER_TOKENS_STORAGE) === 'true';
    if (remember) {
      return {
        googleKeyToken: sessionStorage.getItem(GOOGLE_KEY_TOKEN_STORAGE) || null,
        pplxKeyToken: sessionStorage.getItem(PPLX_KEY_TOKEN_STORAGE) || null,
        remember,
      };
    }
  } catch (error) {
    console.error('Error retrieving API tokens from session storage:', error);
  }
  
  return { googleKeyToken: null, pplxKeyToken: null, remember: false };
};

export const clearSavedApiTokens = () => {
  try {
    sessionStorage.removeItem(GOOGLE_KEY_TOKEN_STORAGE);
    sessionStorage.removeItem(PPLX_KEY_TOKEN_STORAGE);
    sessionStorage.removeItem(REMEMBER_TOKENS_STORAGE);
  } catch (error) {
    console.error('Error clearing API tokens from session storage:', error);
  }
};

// Register user (now expects message, not token)
export const register = async (email, password, fullName) => {
  try {
    const response = await api.post('/auth/register', {
      email,
      password,
      full_name: fullName,
    });
    // Return the success message from backend
    return { success: true, message: response.data.message };
  } catch (error) {
    console.error('Registration failed:', error);
    // Return the formatted error message
    return { success: false, message: error.message || 'Registration failed' };
  }
};

export const login = async (email, password, rememberMe = false) => {
  try {
    const response = await api.post('/auth/login', {
      email,
      password,
      remember_me: rememberMe
    });
    return response.data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

// Enhanced refresh auth token function with concurrency control
export const refreshAuthToken = async () => {
  // If already refreshing token, wait for that to complete instead of making multiple calls
  if (isRefreshingToken) {
    return new Promise((resolve, reject) => {
      subscribeTokenRefresh(token => {
        if (token) {
          resolve({ access_token: token });
        } else {
          reject(new Error('Token refresh failed'));
        }
      });
    });
  }
  
  try {
    isRefreshingToken = true;
    const response = await api.post('/auth/refresh');
    
    // Update token in API instance and localStorage
    const { access_token } = response.data;
    setAuthToken(access_token);
    
    // Update auth data in localStorage if it exists
    const authData = localStorage.getItem('auth');
    if (authData) {
      const parsedAuth = JSON.parse(authData);
      parsedAuth.accessToken = access_token;
      parsedAuth.expiresIn = response.data.expires_in;
      parsedAuth.tokenExpiry = Math.floor(Date.now() / 1000) + response.data.expires_in;
      
      // Update user data if provided
      if (response.data.user) {
        parsedAuth.user = response.data.user;
      }
      
      localStorage.setItem('auth', JSON.stringify(parsedAuth));
    }
    
    // Notify subscribers that token has been refreshed
    onTokenRefreshed(access_token);
    
    return response.data;
  } catch (error) {
    console.error('Token refresh error:', error);
    
    // Notify subscribers of failure
    onTokenRefreshed(null);
    
    throw error;
  } finally {
    isRefreshingToken = false;
  }
};

export const logout = async () => {
  try {
    await api.post('/auth/logout');
    return true;
  } catch (error) {
    console.error('Logout error:', error);
    throw error;
  }
};

// Learn path migration function
export const migrateLearningPaths = async (learningPaths) => {
  try {
    // If courses weren't provided directly, get them from local storage
    if (!learningPaths || !Array.isArray(learningPaths)) {
      // *** This part will require localHistoryService temporarily during migration phase ***
      // We need to get localHistoryService back temporarily or adjust this logic later.
      // For now, let's assume learningPaths are always provided by the caller (AuthContext)
      // const localHistory = localHistoryService.getLocalHistory();
      // learningPaths = localHistory.entries || [];
      if (!learningPaths) {
         console.warn("migrateLearningPaths called without explicit learningPaths array.");
         return { success: true, migrated_count: 0, errors: ["No paths provided for migration."] };
      }
    }
    
    // Process the courses to ensure they're in the right format for migration
    const processedPaths = learningPaths.map(path => {
      // Create a new object to avoid modifying the original
      const processedPath = { ...path };
      
      // Ensure path_id exists (use UUID format which is what the backend expects)
      if (!processedPath.path_id) {
        // If an id exists, use it as path_id (but ensure it's UUID-like)
        if (processedPath.id) {
          // If id already looks like a UUID (contains hyphens), use it directly
          if (String(processedPath.id).includes('-')) {
            processedPath.path_id = String(processedPath.id);
          } else {
            // Otherwise, generate a UUID-like ID that incorporates the original id
            const timestamp = Date.now();
            const randomPart = Math.random().toString(36).substring(2, 10);
            processedPath.path_id = `${timestamp}-${randomPart}-${String(processedPath.id)}`;
          }
        } else {
          // No id at all, generate a completely new UUID-like string
          const timestamp = Date.now();
          const randomPart1 = Math.random().toString(36).substring(2, 10);
          const randomPart2 = Math.random().toString(36).substring(2, 10);
          processedPath.path_id = `${timestamp}-${randomPart1}-${randomPart2}`;
        }
      }
      
      // Make sure topic exists
      if (!processedPath.topic && processedPath.path_data && processedPath.path_data.topic) {
        processedPath.topic = processedPath.path_data.topic;
      } else if (!processedPath.topic) {
        processedPath.topic = "Untitled Path";
      }
      
      // Make sure path_data exists
      if (!processedPath.path_data) {
        // If it's not there, use the entry itself as path_data
        // This handles the case where the entire entry is actually the path data
        processedPath.path_data = { ...path };
      }
      
      // Make sure tags array exists
      if (!processedPath.tags || !Array.isArray(processedPath.tags)) {
        processedPath.tags = [];
      }
      
      // Make sure source is set
      if (!processedPath.source) {
        processedPath.source = 'imported';
      }
      
      return processedPath;
    });
    
    console.log("Migrating courses:", processedPaths);
    
    const response = await api.post('/learning-paths/migrate', {
      learning_paths: processedPaths
    });
    
    return response.data;
  } catch (error) {
    console.error('Learning path migration error:', error);
    throw error;
  }
};

// Get tokens for API keys (either authenticate and get new tokens or use stored ones)
export const authenticateApiKeys = async (googleKey, pplxKey, remember = false) => {
  try {
    // Call the new authentication endpoint to get tokens
    const response = await api.post('/auth/api-keys', {
      google_api_key: googleKey,
      pplx_api_key: pplxKey,
    });
    
    const { 
      google_key_token, 
      pplx_key_token, 
      google_key_valid, 
      pplx_key_valid,
      google_key_error,
      pplx_key_error
    } = response.data;
    
    // Save tokens if remember option is checked
    if (remember && (google_key_token || pplx_key_token)) {
      saveApiTokens(google_key_token, pplx_key_token, true);
    }
    
    return {
      googleKeyToken: google_key_token,
      pplxKeyToken: pplx_key_token,
      googleKeyValid: google_key_valid,
      pplxKeyValid: pplx_key_valid,
      googleKeyError: google_key_error,
      pplxKeyError: pplx_key_error
    };
  } catch (error) {
    console.error('Error authenticating API keys:', error);
    // Use the error message from our interceptor
    throw new Error(error.message || 'Failed to authenticate API keys. Please try again.');
  }
};

// Validate API keys
export const validateApiKeys = async (googleKey, pplxKey) => {
  try {
    const response = await api.post('/validate-api-keys', {
      google_api_key: googleKey,
      pplx_api_key: pplxKey,
    });
    return response.data;
  } catch (error) {
    console.error('Error validating API keys:', error);
    // Use the error message from our interceptor
    throw new Error(error.message || 'Failed to validate API keys. Please try again.');
  }
};

// Generate course with tokens
export const generateLearningPath = async (topic, options = {}) => {
  const { 
    parallelCount = 2, 
    searchParallelCount = 3, 
    submoduleParallelCount = 2,
    desiredModuleCount = null,
    desiredSubmoduleCount = null,
    googleKeyToken = null,
    pplxKeyToken = null,
    rememberTokens = false,
    language = 'en',  // Language parameter with English as default
    explanationStyle = 'standard' // Added explanation style with default
  } = options;
  
  try {
    console.log("Generating course with server-provided API keys");
    
    // Prepare request data
    const requestData = {
      topic,
      parallel_count: parallelCount,
      search_parallel_count: searchParallelCount,
      submodule_parallel_count: submoduleParallelCount,
      language, // Include the language parameter
      explanation_style: explanationStyle // Added explanation style
    };
    
    // Add desired module count if specified
    if (desiredModuleCount !== null) {
      requestData.desired_module_count = desiredModuleCount;
    }
    
    // Add desired submodule count if specified
    if (desiredSubmoduleCount !== null) {
      requestData.desired_submodule_count = desiredSubmoduleCount;
    }
    
    // For backward compatibility, include API key tokens if available
    if (googleKeyToken) requestData.google_key_token = googleKeyToken;
    if (pplxKeyToken) requestData.pplx_key_token = pplxKeyToken;
    
    const response = await api.post('/generate-learning-path', requestData);
    return response.data;
  } catch (error) {
    console.error('Error generating course:', error);
    throw new Error(error.message || 'Failed to start course generation. Please try again.');
  }
};

// Get course by task ID
export const getLearningPath = async (taskId) => {
  try {
    const response = await api.get(`/learning-path/${taskId}`);
    
    // Check for error field in completed tasks
    if (response.data.status === 'failed' && response.data.error) {
      const error = new Error(
        response.data.error.message || 
        'The course generation failed. Please try again.'
      );
      
      // Add additional details if available
      if (response.data.error.details) {
        error.details = response.data.error.details;
      }
      
      if (response.data.error.type) {
        error.type = response.data.error.type;
      }
      
      throw error;
    }
    
    // Handle different API response formats - some endpoints use 'result', others use 'learning_path'
    if (response.data.status === 'completed') {
      // Normalize the response to always have 'result' field
      if (response.data.learning_path && !response.data.result) {
        response.data.result = response.data.learning_path;
      }
    }
    
    return response.data;
  } catch (error) {
    console.error('Error fetching course:', error);
    throw error;
  }
};

// History API functions (Refactored to use ONLY server-side API)
export const getHistoryPreview = async (sortBy = 'creation_date', filterSource = null, searchTerm = null, page = 1, perPage = 10) => {
  // Ensure user is authenticated
  if (!authToken) {
    console.error('getHistoryPreview Error: Authentication required.');
    // Return structure expected by hooks on auth error, preventing fallback
    return { entries: [], total: 0, page: 1, per_page: perPage }; 
  }
  
  try {
    // Prepare request with optimized parameters
    const params = new URLSearchParams();
    params.append('sort_by', sortBy);
    params.append('include_full_data', 'false'); // Use lightweight endpoint
    params.append('page', page.toString());
    params.append('per_page', perPage.toString());
    if (filterSource) params.append('source', filterSource);
    if (searchTerm) params.append('search', searchTerm);
    
    console.time('History API Request');
    // Add /v1 prefix
    const response = await api.get(`/v1/learning-paths?${params.toString()}`); 
    console.timeEnd('History API Request');
    
    if (response.data?.request_time_ms) {
      console.log(`Server processing time: ${response.data.request_time_ms}ms`);
    }
    
    // Ensure response.data has valid entries property
    if (!response.data || !response.data.entries || !Array.isArray(response.data.entries)) {
      console.warn('API response missing or invalid entries property, returning empty array.');
      return { entries: [], total: response.data?.total || 0, page: response.data?.page || page, per_page: response.data?.per_page || perPage };
    }
    
    // Map backend response (path_id) to frontend expectation (id) if needed by hooks/UI
    // The backend LearningPathList already contains LearningPathResponse which has path_id
    // Let's ensure the hooks handle 'path_id' correctly instead of transforming here.
    
    return response.data; // Returns { entries: [], total: 0, page: 1, per_page: 10 }

  } catch (error) {
    console.error('Server error fetching history preview:', error);
    // Re-throw the error for the hook to handle (display message, etc.)
    // No fallback to local storage
    throw error; 
  }
};

export const getHistoryEntry = async (pathId) => {
  // Ensure user is authenticated
  if (!authToken) {
    console.error('getHistoryEntry Error: Authentication required.');
    throw new Error('Authentication required to view course details.');
  }
  
  try {
    console.log('Fetching course with path_id:', pathId);
    // Add /v1 prefix
    const response = await api.get(`/v1/learning-paths/${pathId}`); 
    // The response.data should now contain { ..., progress_map: {}, last_visited_module_idx: N, last_visited_submodule_idx: M }
    return { entry: response.data }; 
  } catch (error) {
    console.error('Server error fetching history entry:', error);
     // Re-throw the error for the hook to handle
    throw error;
  }
};

/**
 * Saves a course (potentially temporary) to the user's history.
 * @param {Object} learningPathData The complete course data object to save.
 * @param {string} [source='generated'] The source of the course ('generated', 'imported').
 * @param {string} [taskId=null] The optional task ID if saving from a generation result.
 * @returns {Promise<Object>} Response data including the saved entry.
 * @throws {Error} If the save operation fails.
 */
export const saveToHistory = async (learningPathData, source = 'generated', taskId = null) => {
  if (!learningPathData) {
    console.error('saveToHistory Error: Invalid course data.');
    throw new Error('Invalid course data.');
  }
  
  try {
    console.log('Saving course to server database:', learningPathData.topic);
    
    // Prepare payload according to LearningPathCreate schema
    const payload = {
      topic: learningPathData.topic || 'Untitled',
      path_data: learningPathData, // Send the full object as path_data
      favorite: learningPathData.favorite || false,
      tags: learningPathData.tags || [],
      source: source || 'generated', // Default source if not provided
      task_id: taskId, // Include the task ID if provided
      language: learningPathData.language || 'en' // Use provided language or default
    };
    
    // Add /v1 prefix
    const response = await api.post('/v1/learning-paths', payload);
    
    console.log('Learning path saved with path_id:', response.data.path_id);
    
    // Return the path_id (as entry_id for compatibility with hooks if needed)
    return { 
      success: true, 
      entry_id: response.data.path_id, // Use path_id from response
      path_id: response.data.path_id // Also include path_id explicitly
    };

  } catch (error) {
    console.error('Error saving course via API:', error);
     // Re-throw the error for the hook to handle
    throw error;
  }
};

export const updateHistoryEntry = async (pathId, data) => {
  // Ensure user is authenticated
  if (!authToken) {
    console.error('updateHistoryEntry Error: Authentication required.');
    throw new Error('Authentication required to update courses.');
  }

  // Validate data contains only allowed fields (favorite, tags)
  const updateData = {};
  if (data.favorite !== undefined) updateData.favorite = data.favorite;
  if (data.tags !== undefined) updateData.tags = data.tags;

  if (Object.keys(updateData).length === 0) {
      console.warn("updateHistoryEntry called with no valid fields to update.");
      return { success: true }; // Nothing to update
  }

  try {
    console.log('Updating course with path_id:', pathId);
    // Add /v1 prefix
    await api.put(`/v1/learning-paths/${pathId}`, updateData); 
    return { success: true };
  } catch (error) {
    console.error('Error updating history entry via API:', error);
     // Re-throw the error for the hook to handle
    throw error;
  }
};

export const deleteHistoryEntry = async (pathId) => {
  // Ensure user is authenticated
  if (!authToken) {
    console.error('deleteHistoryEntry Error: Authentication required.');
    throw new Error('Authentication required to delete courses.');
  }

  try {
    console.log('Deleting course with path_id:', pathId);
    // Add /v1 prefix
    await api.delete(`/v1/learning-paths/${pathId}`);
    return { success: true };
  } catch (error) {
    console.error('Error deleting history entry via API:', error);
     // Re-throw the error for the hook to handle
    throw error;
  }
};

// Rename and modify: POST -> PUT, add 'completed' parameter
export const updateSubmoduleProgress = async (entryId, moduleIndex, submoduleIndex, completed) => {
  try {
    const response = await api.put(`/v1/learning-paths/${entryId}/progress`, { // Use PUT
      module_index: moduleIndex,
      submodule_index: submoduleIndex,
      completed: completed // Send completion status
    });
    // Returns { message: "..." } on success (200)
    return response.data;
  } catch (error) {
    console.error('API Error: Failed to update submodule progress:', error);
    // Re-throw the formatted error from the interceptor
    throw error; 
  }
};

// Add new function to update last visited position
export const updateLastVisited = async (entryId, moduleIndex, submoduleIndex) => {
  try {
    await api.put(`/v1/learning-paths/${entryId}/last-visited`, {
      module_index: moduleIndex,
      submodule_index: submoduleIndex,
    });
    // PUT request, usually no content or just a success message, 
    // which we don't necessarily need to return here.
    console.debug(`Updated last visited to M:${moduleIndex}, S:${submoduleIndex} for path ${entryId}`);
    return { success: true };
  } catch (error) {
    // Don't necessarily throw, as this is a non-critical UX enhancement
    console.warn('API Warning: Failed to update last visited position:', error);
    // Return failure indicator if needed by caller, but don't block other UI updates
    return { success: false, error: error }; 
  }
};

// --- Placeholders for Required Backend API Functions ---

/**
 * Exports all history entries via the backend API.
 * NOTE: Backend endpoint GET /api/learning-paths/export needs implementation.
 * @returns {Promise<Array>} Array of history entries.
 */
export const exportAllHistoryAPI = async () => {
  console.warn("Export All functionality pending backend endpoint (GET /api/learning-paths/export).");
  // TODO: Implement actual API call to GET /api/learning-paths/export once backend is ready.
  // Example: const response = await api.get('/learning-paths/export'); return response.data;
  // throw new Error("Export All functionality is not yet available."); 
  // Return []; // Or return empty array temporarily? Throwing error is clearer.
  try {
    // Add /v1 prefix
    const response = await api.get('/v1/learning-paths/export'); 
    return response.data; 
  } catch (error) {
    console.error('API Error exporting all history:', error);
    // Re-throw the formatted error from the interceptor
    throw error; 
  }
};

/**
 * Clears all history entries for the user via the backend API.
 * NOTE: Backend endpoint DELETE /api/learning-paths/clear-all needs implementation.
 * @returns {Promise<Object>} Result object { success: boolean }
 */
export const clearAllHistoryAPI = async () => {
  console.warn("Clear All functionality pending backend endpoint (DELETE /api/learning-paths/clear-all).");
  // TODO: Implement actual API call to DELETE /api/learning-paths/clear-all once backend is ready.
  // Example: await api.delete('/learning-paths/clear-all'); return { success: true };
  // throw new Error("Clear All functionality is not yet available.");
  // return { success: false }; // Or return failure temporarily? Throwing error is clearer.
  try {
    // Add /v1 prefix
    await api.delete('/v1/learning-paths/clear-all'); 
    // DELETE requests usually return 204 No Content on success, 
    // so we just return a success indicator for the frontend handler.
    return { success: true }; 
  } catch (error) {
     console.error('API Error clearing all history:', error);
    // Re-throw the formatted error from the interceptor
    throw error;
  }
};

// --- End Placeholders ---

/**
 * Downloads a course as PDF
 * @param {string} pathId - ID of the course to download
 * @returns {Promise<Blob>} - PDF data as a Blob
 */
export const downloadLearningPathPDF = async (pathId) => {
  try {
    // Add /v1 prefix
    const response = await api.get(
      `/v1/learning-paths/${pathId}/pdf`, 
      { 
        responseType: 'blob',
        headers: {
          'Accept': 'application/pdf'
        }
      }
    );
    
    return response.data;
  } catch (error) {
    console.error('Error downloading PDF:', error);
    throw new Error(error.message || 'Failed to download PDF');
  }
};

// Get user credits
export const getUserCredits = async () => {
  try {
    if (!authToken) {
      return { credits: 0 };
    }
    
    const response = await api.get('/auth/credits');
    return response.data;
  } catch (error) {
    console.error('Error fetching user credits:', error);
    
    // If unauthorized, clear the invalid token
    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
      console.warn('Token validation failed during credits fetch, clearing auth data');
      clearAuthToken();
      localStorage.removeItem('auth');
    }
    
    return { credits: 0 };
  }
};

// Admin API functions

// Get users with pagination and filtering
export const getUsers = async (page = 1, perPage = 10, search = '', isAdmin = null, isActive = null, hasCredits = null) => {
  try {
    const params = { page, per_page: perPage };
    
    if (search) params.search = search;
    if (isAdmin !== null) params.is_admin = isAdmin;
    if (isActive !== null) params.is_active = isActive;
    if (hasCredits !== null) params.has_credits = hasCredits;
    
    const response = await api.get('/admin/users', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching users:', error);
    throw error;
  }
};

// Get a specific user by ID
export const getUser = async (userId) => {
  try {
    const response = await api.get(`/admin/users/${userId}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching user ${userId}:`, error);
    throw error;
  }
};

// Update a user's details
export const updateUser = async (userId, userData) => {
  try {
    const response = await api.patch(`/admin/users/${userId}`, userData);
    return response.data;
  } catch (error) {
    console.error(`Error updating user ${userId}:`, error);
    throw error;
  }
};

// Add credits to a user
export const addCredits = async (userId, amount, notes = '') => {
  try {
    const response = await api.post('/admin/credits/add', {
      user_id: userId,
      amount,
      notes
    });
    return response.data;
  } catch (error) {
    console.error(`Error adding credits to user ${userId}:`, error);
    throw error;
  }
};

// Get credit transactions with pagination and filtering
export const getCreditTransactions = async (
  page = 1,
  perPage = 20,
  actionType = '',
  fromDate = null,
  toDate = null,
  userId = '',
  adminId = ''
) => {
  try {
    const params = { page, per_page: perPage };
    
    if (actionType) params.action_type = actionType;
    if (fromDate) params.from_date = fromDate.toISOString();
    if (toDate) params.to_date = toDate.toISOString();
    if (userId) params.user_id = userId;
    if (adminId) params.admin_id = adminId;
    
    const response = await api.get('/admin/credits/transactions', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching credit transactions:', error);
    throw error;
  }
};

// Get credit transactions for a specific user
export const getUserCreditTransactions = async (userId, page = 1, perPage = 20) => {
  try {
    const params = { page, per_page: perPage };
    
    const response = await api.get(`/admin/credits/transactions/${userId}`, { params });
    return response.data;
  } catch (error) {
    console.error(`Error fetching credit transactions for user ${userId}:`, error);
    throw error;
  }
};

// Get admin dashboard statistics
export const getAdminStats = async () => {
  try {
    const response = await api.get('/admin/stats');
    return response.data;
  } catch (error) {
    console.error('Error fetching admin stats:', error);
    throw error;
  }
};

// Verify email address using token
export const verifyEmail = async (token) => {
  try {
    const response = await api.get(`/auth/verify-email?token=${token}`);
    return { success: true, message: response.data.message };
  } catch (error) {
    console.error('Email verification failed:', error);
    return { success: false, message: error.message || 'Email verification failed' };
  }
};

// Resend verification email
export const resendVerificationEmail = async (email) => {
  try {
    const response = await api.post('/auth/resend-verification', { email });
    return { success: true, message: response.data.message };
  } catch (error) {
    console.error('Resend verification email failed:', error);
    // Return generic message even on specific errors for security
    return { success: false, message: 'Failed to resend verification email. Please try again later.' };
  }
};

// --- Password Reset --- 

export const forgotPassword = async (email) => {
  const response = await api.post('/auth/forgot-password', { email });
  return response.data; // Returns { message: "..." }
};

export const resetPassword = async (token, new_password) => {
  const response = await api.post('/auth/reset-password', { token, new_password });
  return response.data; // Returns { message: "..." }
};

// --------------------------------------------------------------------------------
// Chatbot API Calls
// --------------------------------------------------------------------------------

/**
 * Sends a message to the submodule chatbot.
 * @param {object} data - The chat request data.
 * @param {string} data.path_id - The ID of the course.
 * @param {number} data.module_index - The index of the current module.
 * @param {number} data.submodule_index - The index of the current submodule.
 * @param {string} data.user_message - The user's message.
 * @param {string} data.thread_id - The unique conversation thread ID.
 * @returns {Promise<object>} The API response containing the AI's response.
 */
export const sendMessage = async (data) => {
  try {
    console.log('Sending chat message:', data);
    // Ensure auth token is set before making the request
    if (!authToken) {
      // Attempt to initialize from storage if token is missing
      if (!initAuthFromStorage()) {
          console.error('sendMessage Error: No auth token available.');
          throw new Error('Authentication required. Please log in.');
      }
    }
    const response = await api.post('/chatbot/chat', data);
    console.log('Chat response received:', response.data);
    return response.data; // Should contain { ai_response: string, thread_id: string }
  } catch (error) {
    console.error('Error sending chat message:', error);
    // The interceptor should have already formatted the error
    throw error;
  }
};

/**
 * Clears the chat history for a specific thread on the backend.
 * Note: With MemorySaver, this might be a no-op on the backend,
 * but it's included for potential future use with persistent storage.
 * @param {object} data - The clear chat request data.
 * @param {string} data.thread_id - The unique conversation thread ID.
 * @returns {Promise<void>} A promise that resolves on success.
 */
export const clearChatHistory = async (data) => {
  try {
    console.log('Clearing chat history for thread:', data.thread_id);
    // Ensure auth token is set
    if (!authToken) {
      if (!initAuthFromStorage()) {
        console.error('clearChatHistory Error: No auth token available.');
        throw new Error('Authentication required.');
      }
    }
    await api.post('/chatbot/clear', data);
    console.log('Chat history clear request successful for thread:', data.thread_id);
  } catch (error) {
    console.error('Error clearing chat history:', error);
    throw error;
  }
};

/**
 * Purchases additional chat allowance for the current user.
 * @returns {Promise<object>} The API response, likely including a success message.
 */
export const purchaseChatAllowance = async () => {
  try {
    // Ensure auth token is set
    if (!authToken) {
      if (!initAuthFromStorage()) {
        console.error('purchaseChatAllowance Error: No auth token available.');
        throw new Error('Authentication required.');
      }
    }
    const response = await api.post('/chatbot/purchase-allowance');
    console.log('Chat allowance purchase successful:', response.data);
    return response.data; // Should contain { message: string, new_allowance_today: number }
  } catch (error) {
    console.error('Error purchasing chat allowance:', error);
    // The interceptor should have already formatted the error
    throw error;
  }
};

// Create a Stripe Checkout session
export const createCheckoutSession = async (quantity) => {
  try {
    const response = await api.post('/payments/checkout-sessions', { quantity });
    return response.data;
  } catch (error) {
    console.error('Error creating checkout session:', error);
    throw error;
  }
};

// Get details of a Checkout session
export const getCheckoutSession = async (sessionId) => {
  try {
    const response = await api.get(`/payments/session/${sessionId}`);
    return response.data;
  } catch (error) {
    console.error('Error getting checkout session:', error);
    throw error;
  }
};

// Fetch active (PENDING or RUNNING) generations for the current user
export const getActiveGenerations = async () => {
  try {
    const response = await api.get('/v1/learning-paths/generations/active');
    return response.data;
  } catch (error) {
    console.error('Error fetching active generations:', error);
    throw error; // Re-throw to be handled by calling component/hook
  }
};

// --- NEW: Update course publicity ---
export const updateLearningPathPublicity = async (pathId, isPublic) => {
  try {
    const response = await api.patch(`/v1/learning-paths/${pathId}/publicity`, {
      is_public: isPublic,
    });
    // Return the updated course data (including share_id if generated)
    return response.data; 
  } catch (error) {
    console.error('API Error updating course publicity:', error);
    throw error; // Re-throw the formatted error
  }
};

// --- NEW: Get public course ---
export const getPublicLearningPath = async (shareId) => {
  try {
    // Note: This uses the base API URL, not the prefixed one, assuming /public is at the root
    // Adjust if /public is under /api
    // const publicApi = axios.create({ baseURL: API_URL }); // Use root URL
    // const response = await publicApi.get(`/public/${shareId}`);
    
    // Assuming /public is under /api for consistency with other routes
    const response = await api.get(`/public/${shareId}`);
    
    return response.data; // Returns the LearningPathResponse
  } catch (error) {
    console.error('API Error fetching public course:', error);
    throw error; // Re-throw the formatted error
  }
};

// --- NEW: Function to copy a public course ---
export const copyPublicPath = async (shareId) => {
  try {
    // Ensure auth token exists
    if (!authToken) {
        if (!initAuthFromStorage()) {
            console.error('copyPublicPath Error: No auth token available.');
            throw new Error('Authentication required. Please log in to copy.');
        }
    }
    const response = await api.post(`/v1/learning-paths/copy/${shareId}`);
    // response.data should be the new LearningPathResponse object
    return response.data; 
  } catch (error) {
    console.error(`Error copying public course ${shareId}:`, error);
    throw error; // Re-throw formatted error from interceptor
  }
};

export default {
  generateLearningPath,
  getLearningPath,
  getHistoryPreview,
  getHistoryEntry,
  saveToHistory,
  updateHistoryEntry,
  deleteHistoryEntry,
  validateApiKeys,
  authenticateApiKeys,
  saveApiTokens,
  getSavedApiTokens,
  clearSavedApiTokens,
  register,
  login,
  refreshAuthToken,
  logout,
  migrateLearningPaths,
  deleteLearningPath,
  checkAuthStatus,
  downloadLearningPathPDF,
  getUserCredits,
  getUsers,
  getUser,
  updateUser,
  addCredits,
  getCreditTransactions,
  getUserCreditTransactions,
  getAdminStats,
  sendMessage,
  clearChatHistory,
  verifyEmail,
  resendVerificationEmail,
  forgotPassword,
  resetPassword,
  exportAllHistoryAPI,
  clearAllHistoryAPI,
  createCheckoutSession,
  getCheckoutSession,
  getActiveGenerations,
  updateSubmoduleProgress,
  updateLastVisited,
  purchaseChatAllowance,
  updateLearningPathPublicity,
  getPublicLearningPath,
  copyPublicPath,
};

    