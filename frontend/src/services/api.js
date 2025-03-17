import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

// Create axios instance with base URL
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Generate learning path
export const generateLearningPath = async (topic, options = {}) => {
  const { 
    parallelCount = 2, 
    searchParallelCount = 3, 
    submoduleParallelCount = 2 
  } = options;
  
  try {
    const response = await api.post('/generate-learning-path', {
      topic,
      parallel_count: parallelCount,
      search_parallel_count: searchParallelCount,
      submodule_parallel_count: submoduleParallelCount,
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
  const eventSource = new EventSource(`${API_URL}/progress/${taskId}`);
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.complete) {
      eventSource.close();
      if (onComplete) onComplete();
      return;
    }
    
    if (onMessage) onMessage(data);
  };
  
  eventSource.onerror = (error) => {
    console.error('SSE Error:', error);
    eventSource.close();
    if (onError) onError(error);
  };
  
  return {
    close: () => eventSource.close(),
  };
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
}; 