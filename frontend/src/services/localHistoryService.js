/**
 * Local History Service
 * 
 * This service manages learning path history in the browser's localStorage,
 * ensuring each user's history is kept private to their browser without needing authentication.
 * Uses a unique identifier for each browser to isolate histories.
 */

const BASE_STORAGE_KEY = 'learny_history';
const USER_ID_KEY = 'learny_user_id';

/**
 * Gets or creates a unique user ID for the current browser
 * @returns {string} The unique user ID
 */
const getUserId = () => {
  let userId = localStorage.getItem(USER_ID_KEY);
  
  // If no user ID exists, create one
  if (!userId) {
    userId = generateUUID();
    localStorage.setItem(USER_ID_KEY, userId);
  }
  
  return userId;
};

/**
 * Gets the storage key specific to the current user
 * @returns {string} The user-specific storage key
 */
const getStorageKey = () => {
  const userId = getUserId();
  return `${BASE_STORAGE_KEY}_${userId}`;
};

/**
 * Get the complete history from localStorage
 * @returns {Object} The history object with entries array
 */
export const getLocalHistory = () => {
  try {
    const storageKey = getStorageKey();
    const historyData = localStorage.getItem(storageKey);
    if (!historyData) {
      return { entries: [], last_updated: new Date().toISOString() };
    }
    return JSON.parse(historyData);
  } catch (error) {
    console.error('Error loading history from localStorage:', error);
    return { entries: [], last_updated: new Date().toISOString() };
  }
};

/**
 * Save the complete history to localStorage
 * @param {Object} history The history object to save
 * @returns {boolean} Success status
 */
export const saveLocalHistory = (history) => {
  try {
    const storageKey = getStorageKey();
    const historyString = JSON.stringify({
      ...history,
      last_updated: new Date().toISOString()
    });
    localStorage.setItem(storageKey, historyString);
    return true;
  } catch (error) {
    console.error('Error saving history to localStorage:', error);
    return false;
  }
};

/**
 * Get a list of history entries for display
 * @param {string} sortBy Field to sort by
 * @param {string} filterSource Filter by source type
 * @param {string} search Search term
 * @returns {Array} Array of history entry previews
 */
export const getHistoryPreview = (sortBy = 'creation_date', filterSource = null, search = null) => {
  const history = getLocalHistory();
  let entries = [...history.entries];
  
  // Apply filtering
  if (filterSource) {
    entries = entries.filter(entry => entry.source === filterSource);
  }
  
  // Apply search
  if (search && search.trim()) {
    const searchTerm = search.toLowerCase().trim();
    entries = entries.filter(entry => 
      entry.topic.toLowerCase().includes(searchTerm) ||
      (entry.tags && entry.tags.some(tag => tag.toLowerCase().includes(searchTerm)))
    );
  }
  
  // Apply sorting
  if (sortBy === 'creation_date') {
    entries.sort((a, b) => new Date(b.creation_date) - new Date(a.creation_date));
  } else if (sortBy === 'last_modified_date') {
    entries.sort((a, b) => {
      const dateA = a.last_modified_date ? new Date(a.last_modified_date) : new Date(a.creation_date);
      const dateB = b.last_modified_date ? new Date(b.last_modified_date) : new Date(b.creation_date);
      return dateB - dateA;
    });
  } else if (sortBy === 'topic') {
    entries.sort((a, b) => a.topic.localeCompare(b.topic));
  } else if (sortBy === 'favorite') {
    entries.sort((a, b) => {
      if (a.favorite === b.favorite) {
        return new Date(b.creation_date) - new Date(a.creation_date);
      }
      return a.favorite ? -1 : 1;
    });
  }
  
  return entries;
};

/**
 * Get a specific history entry by ID
 * @param {string} entryId The entry ID to retrieve
 * @returns {Object|null} The entry or null if not found
 */
export const getHistoryEntry = (entryId) => {
  const history = getLocalHistory();
  const entry = history.entries.find(entry => entry.id === entryId);
  return entry ? { entry } : null;
};

/**
 * Save a learning path to history
 * @param {Object} learningPath The learning path to save
 * @param {string} source Source of the learning path ('generated' or 'imported')
 * @returns {Object} Result with success flag and entry ID
 */
export const saveToHistory = (learningPath, source = 'generated') => {
  try {
    const history = getLocalHistory();
    const entryId = generateUUID();
    
    const entry = {
      id: entryId,
      topic: learningPath.topic || 'Untitled',
      creation_date: new Date().toISOString(),
      last_modified_date: null,
      path_data: learningPath,
      favorite: false,
      tags: [],
      source: source
    };
    
    history.entries.push(entry);
    const success = saveLocalHistory(history);
    
    return { success, entry_id: entryId };
  } catch (error) {
    console.error('Error saving to history:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Update a history entry (favorite status or tags)
 * @param {string} entryId The entry ID to update
 * @param {Object} data The data to update (favorite, tags)
 * @returns {Object} Result with success flag
 */
export const updateHistoryEntry = (entryId, data) => {
  try {
    const history = getLocalHistory();
    const entryIndex = history.entries.findIndex(entry => entry.id === entryId);
    
    if (entryIndex === -1) {
      return { success: false, error: 'Entry not found' };
    }
    
    if (data.favorite !== undefined) {
      history.entries[entryIndex].favorite = data.favorite;
    }
    
    if (data.tags !== undefined) {
      history.entries[entryIndex].tags = data.tags;
    }
    
    history.entries[entryIndex].last_modified_date = new Date().toISOString();
    
    const success = saveLocalHistory(history);
    return { success };
  } catch (error) {
    console.error('Error updating history entry:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Delete a history entry
 * @param {string} entryId The entry ID to delete
 * @returns {Object} Result with success flag
 */
export const deleteHistoryEntry = (entryId) => {
  try {
    const history = getLocalHistory();
    const initialLength = history.entries.length;
    
    history.entries = history.entries.filter(entry => entry.id !== entryId);
    
    if (history.entries.length === initialLength) {
      return { success: false, error: 'Entry not found' };
    }
    
    const success = saveLocalHistory(history);
    return { success };
  } catch (error) {
    console.error('Error deleting history entry:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Import a learning path from JSON
 * @param {string} jsonData The JSON string to import
 * @returns {Object} Result with success flag and imported path info
 */
export const importLearningPath = (jsonData) => {
  try {
    const learningPath = JSON.parse(jsonData);
    
    if (!isValidLearningPath(learningPath)) {
      throw new Error('Invalid learning path format');
    }
    
    const result = saveToHistory(learningPath, 'imported');
    
    return {
      success: result.success,
      entry_id: result.entry_id,
      topic: learningPath.topic
    };
  } catch (error) {
    console.error('Error importing learning path:', error);
    throw error;
  }
};

/**
 * Export all history as JSON
 * @returns {string} JSON string of the history
 */
export const exportHistory = () => {
  const history = getLocalHistory();
  return history;
};

/**
 * Clear all history
 * @returns {Object} Result with success flag
 */
export const clearHistory = () => {
  try {
    localStorage.removeItem(getStorageKey());
    return { success: true };
  } catch (error) {
    console.error('Error clearing history:', error);
    return { success: false, error: error.message };
  }
};

// Helper functions

/**
 * Generate a UUID v4 using cryptographically secure random values
 * @returns {string} A UUID string
 */
function generateUUID() {
  const randomBytes = new Uint8Array(16);
  window.crypto.getRandomValues(randomBytes);
  
  // Set version (4) and variant bits according to RFC 4122
  randomBytes[6] = (randomBytes[6] & 0x0f) | 0x40;  // version 4
  randomBytes[8] = (randomBytes[8] & 0x3f) | 0x80;  // variant 1
  
  // Convert to hex string with proper formatting
  const hexValues = Array.from(randomBytes).map(b => b.toString(16).padStart(2, '0'));
  return [
    hexValues.slice(0, 4).join(''),
    hexValues.slice(4, 6).join(''),
    hexValues.slice(6, 8).join(''),
    hexValues.slice(8, 10).join(''),
    hexValues.slice(10, 16).join('')
  ].join('-');
}

/**
 * Validate if an object is a valid learning path
 * @param {Object} obj The object to validate
 * @returns {boolean} Whether the object is a valid learning path
 */
function isValidLearningPath(obj) {
  return (
    obj && 
    typeof obj === 'object' &&
    typeof obj.topic === 'string' &&
    Array.isArray(obj.modules)
  );
}

export default {
  getLocalHistory,
  saveLocalHistory,
  getHistoryPreview,
  getHistoryEntry,
  saveToHistory,
  updateHistoryEntry,
  deleteHistoryEntry,
  importLearningPath,
  exportHistory,
  clearHistory
}; 