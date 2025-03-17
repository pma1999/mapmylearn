import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with base URL
const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Session storage keys
const OPENAI_KEY_STORAGE = 'learning_path_openai_key';
const TAVILY_KEY_STORAGE = 'learning_path_tavily_key';
const REMEMBER_KEYS_STORAGE = 'learning_path_remember_keys';

// API key management functions
export const saveApiKeys = (openaiKey, tavilyKey, remember = false) => {
  // Only save if remember is true
  if (remember) {
    try {
      // Use sessionStorage for temporary storage during the browser session
      sessionStorage.setItem(OPENAI_KEY_STORAGE, openaiKey || '');
      sessionStorage.setItem(TAVILY_KEY_STORAGE, tavilyKey || '');
      sessionStorage.setItem(REMEMBER_KEYS_STORAGE, 'true');
    } catch (error) {
      console.error('Error saving API keys to session storage:', error);
    }
  } else {
    clearSavedApiKeys();
  }
  
  return { openaiKey, tavilyKey, remember };
};

export const getSavedApiKeys = () => {
  try {
    const remember = sessionStorage.getItem(REMEMBER_KEYS_STORAGE) === 'true';
    if (remember) {
      return {
        openaiKey: sessionStorage.getItem(OPENAI_KEY_STORAGE) || null,
        tavilyKey: sessionStorage.getItem(TAVILY_KEY_STORAGE) || null,
        remember,
      };
    }
  } catch (error) {
    console.error('Error retrieving API keys from session storage:', error);
  }
  
  return { openaiKey: null, tavilyKey: null, remember: false };
};

export const clearSavedApiKeys = () => {
  try {
    sessionStorage.removeItem(OPENAI_KEY_STORAGE);
    sessionStorage.removeItem(TAVILY_KEY_STORAGE);
    sessionStorage.removeItem(REMEMBER_KEYS_STORAGE);
  } catch (error) {
    console.error('Error clearing API keys from session storage:', error);
  }
};

// Validate API keys
export const validateApiKeys = async (openaiKey, tavilyKey) => {
  try {
    const response = await api.post('/validate-api-keys', {
      openai_api_key: openaiKey,
      tavily_api_key: tavilyKey,
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
    openaiApiKey = null,
    tavilyApiKey = null
  } = options;
  
  // Get stored API keys if not provided
  let finalOpenaiKey = openaiApiKey;
  let finalTavilyKey = tavilyApiKey;
  
  // If keys not explicitly provided, try to get from session storage
  if (!finalOpenaiKey || !finalTavilyKey) {
    const savedKeys = getSavedApiKeys();
    
    if (!finalOpenaiKey && savedKeys.openaiKey) {
      finalOpenaiKey = savedKeys.openaiKey;
    }
    
    if (!finalTavilyKey && savedKeys.tavilyKey) {
      finalTavilyKey = savedKeys.tavilyKey;
    }
  }
  
  // Validate that both API keys are present
  if (!finalOpenaiKey || !finalTavilyKey) {
    throw new Error("Both OpenAI and Tavily API keys are required");
  }
  
  // Trim API keys to remove any whitespace
  finalOpenaiKey = finalOpenaiKey.trim();
  finalTavilyKey = finalTavilyKey.trim();
  
  // Final validation check
  if (!finalOpenaiKey || !finalTavilyKey) {
    throw new Error("API keys cannot be empty");
  }
  
  try {
    console.log("Sending API keys to backend for learning path generation");
    const response = await api.post('/generate-learning-path', {
      topic,
      parallel_count: parallelCount,
      search_parallel_count: searchParallelCount,
      submodule_parallel_count: submoduleParallelCount,
      openai_api_key: finalOpenaiKey,
      tavily_api_key: finalTavilyKey,
    });
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

// HISTORY API METHODS

// Get history preview list
export const getHistoryPreview = async (sortBy = 'creation_date', filterSource = null, search = null) => {
  try {
    const params = { sort_by: sortBy };
    if (filterSource) params.filter_source = filterSource;
    if (search) params.search = search;
    
    const response = await api.get('/history', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching history preview:', error);
    throw error;
  }
};

// Get complete learning path data for a specific entry
export const getHistoryEntry = async (entryId) => {
  try {
    const response = await api.get(`/history/${entryId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching history entry:', error);
    throw error;
  }
};

// Save a new learning path to history
export const saveToHistory = async (learningPath, source = 'generated') => {
  try {
    const response = await api.post('/history', learningPath, {
      params: { source }
    });
    return response.data;
  } catch (error) {
    console.error('Error saving to history:', error);
    throw error;
  }
};

// Update history entry metadata (favorite status, tags)
export const updateHistoryEntry = async (entryId, data) => {
  try {
    const response = await api.put(`/history/${entryId}`, data);
    return response.data;
  } catch (error) {
    console.error('Error updating history entry:', error);
    throw error;
  }
};

// Delete history entry
export const deleteHistoryEntry = async (entryId) => {
  try {
    const response = await api.delete(`/history/${entryId}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting history entry:', error);
    throw error;
  }
};

// Import learning path from JSON
export const importLearningPath = async (jsonData) => {
  try {
    const response = await api.post('/history/import', { json_data: jsonData });
    return response.data;
  } catch (error) {
    console.error('Error importing learning path:', error);
    throw error;
  }
};

// Export all history as JSON
export const exportHistory = async () => {
  try {
    const response = await api.get('/history/export');
    return response.data;
  } catch (error) {
    console.error('Error exporting history:', error);
    throw error;
  }
};

// Clear all history
export const clearHistory = async () => {
  try {
    const response = await api.delete('/history/clear');
    return response.data;
  } catch (error) {
    console.error('Error clearing history:', error);
    throw error;
  }
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
