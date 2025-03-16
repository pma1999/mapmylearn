import axios from 'axios';

// Base API configuration
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Learning path generation
export const generateLearningPath = async (params) => {
  try {
    const response = await api.post('/learning-path', params);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to start generation' };
  }
};

export const startGeneration = async (connectionId, params) => {
  try {
    const response = await api.post(`/start-generation/${connectionId}`, params);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to start generation' };
  }
};

// WebSocket connection
export const createWebSocketConnection = (connectionId, onMessage, onClose, onError) => {
  // Determine WebSocket URL based on current URL
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  const wsUrl = `${protocol}//${host}/ws/${connectionId}`;
  
  const socket = new WebSocket(wsUrl);
  
  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (onMessage) onMessage(data);
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
      if (onError) onError(error);
    }
  };
  
  socket.onclose = (event) => {
    if (onClose) onClose(event);
  };
  
  socket.onerror = (error) => {
    console.error('WebSocket error:', error);
    if (onError) onError(error);
  };
  
  return socket;
};

// History operations
export const getHistoryItems = async () => {
  try {
    const response = await api.get('/history');
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to fetch history' };
  }
};

export const getHistoryItem = async (id) => {
  try {
    const response = await api.get(`/history/${id}`);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to fetch learning path' };
  }
};

export const deleteHistoryItem = async (id) => {
  try {
    const response = await api.delete(`/history/${id}`);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to delete learning path' };
  }
};

export const updateHistoryItemFavorite = async (id, favorite) => {
  try {
    const response = await api.put(`/history/${id}/favorite`, { favorite });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to update favorite status' };
  }
};

export const updateHistoryItemTags = async (id, tags) => {
  try {
    const response = await api.put(`/history/${id}/tags`, { tags });
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to update tags' };
  }
};

export const importLearningPath = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post('/api/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to import learning path' };
  }
};

export const exportHistory = async () => {
  try {
    const response = await api.get('/export');
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to export history' };
  }
};

export const clearHistory = async () => {
  try {
    const response = await api.delete('/history');
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to clear history' };
  }
};

// Settings operations
export const getSettings = async () => {
  try {
    const response = await api.get('/settings');
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to fetch settings' };
  }
};

export const updateSettings = async (settings) => {
  try {
    const response = await api.post('/settings', settings);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Failed to update settings' };
  }
}; 