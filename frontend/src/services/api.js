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

// Session storage keys
const OPENAI_KEY_STORAGE = 'learning_path_openai_key';
const PPLX_KEY_STORAGE = 'learning_path_pplx_key';
const REMEMBER_KEYS_STORAGE = 'learning_path_remember_keys';

// API key management functions
export const saveApiKeys = (openaiKey, pplxKey, remember = false) => {
  // Only save if remember is true
  if (remember) {
    try {
      // Use sessionStorage for temporary storage during the browser session
      sessionStorage.setItem(OPENAI_KEY_STORAGE, openaiKey || '');
      sessionStorage.setItem(PPLX_KEY_STORAGE, pplxKey || '');
      sessionStorage.setItem(REMEMBER_KEYS_STORAGE, 'true');
    } catch (error) {
      console.error('Error saving API keys to session storage:', error);
    }
  } else {
    clearSavedApiKeys();
  }
  
  return { openaiKey, pplxKey, remember };
};

export const getSavedApiKeys = () => {
  try {
    const remember = sessionStorage.getItem(REMEMBER_KEYS_STORAGE) === 'true';
    if (remember) {
      return {
        openaiKey: sessionStorage.getItem(OPENAI_KEY_STORAGE) || null,
        pplxKey: sessionStorage.getItem(PPLX_KEY_STORAGE) || null,
        remember,
      };
    }
  } catch (error) {
    console.error('Error retrieving API keys from session storage:', error);
  }
  
  return { openaiKey: null, pplxKey: null, remember: false };
};

export const clearSavedApiKeys = () => {
  try {
    sessionStorage.removeItem(OPENAI_KEY_STORAGE);
    sessionStorage.removeItem(PPLX_KEY_STORAGE);
    sessionStorage.removeItem(REMEMBER_KEYS_STORAGE);
  } catch (error) {
    console.error('Error clearing API keys from session storage:', error);
  }
};

// Validate API keys
export const validateApiKeys = async (openaiKey, pplxKey) => {
  try {
    const response = await api.post('/validate-api-keys', {
      openai_api_key: openaiKey,
      pplx_api_key: pplxKey,
    });
    return response.data;
  } catch (error) {
    console.error('Error validating API keys:', error);
    throw error;
  }
};

// Generate learning path
export const generateLearningPath = async (topic, options = {}) => {
  const { 
    parallelCount = 2, 
    searchParallelCount = 3, 
    submoduleParallelCount = 2,
    desiredModuleCount = null,
    desiredSubmoduleCount = null,
    openaiApiKey = null,
    pplxApiKey = null
  } = options;
  
  // Get stored API keys if not provided
  let finalOpenaiKey = openaiApiKey;
  let finalPplxKey = pplxApiKey;
  
  // If keys not explicitly provided, try to get from session storage
  if (!finalOpenaiKey || !finalPplxKey) {
    const savedKeys = getSavedApiKeys();
    
    if (!finalOpenaiKey && savedKeys.openaiKey) {
      finalOpenaiKey = savedKeys.openaiKey;
    }
    
    if (!finalPplxKey && savedKeys.pplxKey) {
      finalPplxKey = savedKeys.pplxKey;
    }
  }
  
  // Validate that both API keys are present
  if (!finalOpenaiKey || !finalPplxKey) {
    throw new Error("Both OpenAI and Perplexity API keys are required");
  }
  
  // Trim API keys to remove any whitespace
  finalOpenaiKey = finalOpenaiKey.trim();
  finalPplxKey = finalPplxKey.trim();
  
  // Final validation check
  if (!finalOpenaiKey || !finalPplxKey) {
    throw new Error("API keys cannot be empty");
  }
  
  try {
    console.log("Sending API keys to backend for learning path generation");
    
    // Prepare request data
    const requestData = {
      topic,
      parallel_count: parallelCount,
      search_parallel_count: searchParallelCount,
      submodule_parallel_count: submoduleParallelCount,
      openai_api_key: finalOpenaiKey,
      pplx_api_key: finalPplxKey
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
    throw error;
  }
};

// Get learning path by task ID
export const getLearningPath = async (taskId) => {
  try {
    const response = await api.get(`/learning-path/${taskId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching learning path:', error);
    throw error;
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
        
        if (onMessage) onMessage(data);
      } catch (err) {
        console.error('Error parsing SSE message:', err);
        if (onError) onError(err);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
      eventSource.close();
      if (onError) onError(error);
    };
    
    return {
      close: () => eventSource.close(),
    };
  } catch (initError) {
    console.error('Error initializing SSE connection:', initError);
    if (onError) onError(initError);
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
    throw error;
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
  saveApiKeys,
  getSavedApiKeys,
  clearSavedApiKeys,
};
