import axios from 'axios';
import * as localHistoryService from './localHistoryService';

// Use local API when in development mode, Railway API in production
const API_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000' 
  : 'https://web-production-62f88.up.railway.app';
console.log('Using API URL:', API_URL);

// Create axios instance with base URL
const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor to handle standardized error format
api.interceptors.response.use(
  response => response, // Return successful responses as-is
  error => {
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

// Session storage keys
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

// Generate learning path with tokens
export const generateLearningPath = async (topic, options = {}) => {
  const { 
    parallelCount = 2, 
    searchParallelCount = 3, 
    submoduleParallelCount = 2,
    desiredModuleCount = null,
    desiredSubmoduleCount = null,
    googleKeyToken = null,
    pplxKeyToken = null,
    rememberTokens = false
  } = options;
  
  // Get stored API tokens if not provided
  let finalGoogleKeyToken = googleKeyToken;
  let finalPplxKeyToken = pplxKeyToken;
  
  // If tokens not explicitly provided, try to get from session storage
  if (!finalGoogleKeyToken || !finalPplxKeyToken) {
    const savedTokens = getSavedApiTokens();
    
    if (!finalGoogleKeyToken && savedTokens.googleKeyToken) {
      finalGoogleKeyToken = savedTokens.googleKeyToken;
    }
    
    if (!finalPplxKeyToken && savedTokens.pplxKeyToken) {
      finalPplxKeyToken = savedTokens.pplxKeyToken;
    }
  }
  
  // Validate that at least one token is present (backend will fall back to env vars if needed)
  if (!finalGoogleKeyToken && !finalPplxKeyToken) {
    throw new Error("At least one API key token is required. Please authenticate your API keys first.");
  }
  
  try {
    console.log("Using token-based API key access for learning path generation");
    
    // Prepare request data
    const requestData = {
      topic,
      parallel_count: parallelCount,
      search_parallel_count: searchParallelCount,
      submodule_parallel_count: submoduleParallelCount,
      google_key_token: finalGoogleKeyToken,
      pplx_key_token: finalPplxKeyToken
    };
    
    // Add desired module count if specified
    if (desiredModuleCount !== null) {
      requestData.desired_module_count = desiredModuleCount;
    }
    
    // Add desired submodule count if specified
    if (desiredSubmoduleCount !== null) {
      requestData.desired_submodule_count = desiredSubmoduleCount;
    }
    
    const response = await api.post('/generate-learning-path', requestData);
    return response.data;
  } catch (error) {
    console.error('Error generating learning path:', error);
    throw new Error(error.message || 'Failed to start learning path generation. Please try again.');
  }
};

// Get learning path by task ID
export const getLearningPath = async (taskId) => {
  try {
    const response = await api.get(`/learning-path/${taskId}`);
    
    // Check for error field in completed tasks
    if (response.data.status === 'failed' && response.data.error) {
      const error = new Error(
        response.data.error.message || 
        'The learning path generation failed. Please try again.'
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
    
    return response.data;
  } catch (error) {
    console.error('Error fetching learning path:', error);
    throw new Error(error.message || 'Failed to retrieve learning path. Please try again.');
  }
};

// Get progress updates for a learning path using SSE (Server-Sent Events)
export const getProgressUpdates = (taskId, onMessage, onError, onComplete) => {
  // Create the correct URL using the same API_URL base
  const url = new URL(`/api/progress/${taskId}`, API_URL);
  
  try {
    const eventSource = new EventSource(url.toString());
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.complete) {
          eventSource.close();
          if (onComplete) onComplete();
          return;
        }
        
        // Check for error message format
        if (data.message && data.message.startsWith("Error:")) {
          // This is an error message from the server
          if (onError) {
            onError(new Error(data.message.replace("Error: ", "")));
          }
          return;
        }
        
        if (onMessage) onMessage(data);
      } catch (err) {
        console.error('Error parsing SSE message:', err);
        if (onError) onError(err);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
      eventSource.close();
      if (onError) onError(new Error('Connection to progress updates was lost. Please check your network connection.'));
    };
    
    return {
      close: () => eventSource.close(),
    };
  } catch (initError) {
    console.error('Error initializing SSE connection:', initError);
    if (onError) onError(new Error('Failed to connect to progress updates. Please try refreshing the page.'));
    return {
      close: () => {}, // Dummy close function for consistent API
    };
  }
};

// Delete a learning path task
export const deleteLearningPath = async (taskId) => {
  try {
    const response = await api.delete(`/learning-path/${taskId}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting learning path:', error);
    throw new Error(error.message || 'Failed to delete learning path. Please try again.');
  }
};

// HISTORY API METHODS - Using local storage instead of server

// Get history preview list
export const getHistoryPreview = async (sortBy = 'creation_date', filterSource = null, search = null) => {
  const entries = localHistoryService.getHistoryPreview(sortBy, filterSource, search);
  return { entries };
};

// Get complete learning path data for a specific entry
export const getHistoryEntry = async (entryId) => {
  return localHistoryService.getHistoryEntry(entryId);
};

// Save a new learning path to history
export const saveToHistory = async (learningPath, source = 'generated') => {
  return localHistoryService.saveToHistory(learningPath, source);
};

// Update history entry metadata (favorite status, tags)
export const updateHistoryEntry = async (entryId, data) => {
  return localHistoryService.updateHistoryEntry(entryId, data);
};

// Delete history entry
export const deleteHistoryEntry = async (entryId) => {
  return localHistoryService.deleteHistoryEntry(entryId);
};

// Import learning path from JSON
export const importLearningPath = async (jsonData) => {
  return localHistoryService.importLearningPath(jsonData);
};

// Export all history as JSON
export const exportHistory = async () => {
  return localHistoryService.exportHistory();
};

// Clear all history
export const clearHistory = async () => {
  return localHistoryService.clearHistory();
};

export default {
  generateLearningPath,
  getLearningPath,
  getProgressUpdates,
  deleteLearningPath,
  getHistoryPreview,
  getHistoryEntry,
  saveToHistory,
  updateHistoryEntry,
  deleteHistoryEntry,
  importLearningPath,
  exportHistory,
  clearHistory,
  validateApiKeys,
  authenticateApiKeys,
  saveApiTokens,
  getSavedApiTokens,
  clearSavedApiTokens,
};

