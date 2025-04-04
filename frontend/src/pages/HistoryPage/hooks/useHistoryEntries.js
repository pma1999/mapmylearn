import { useState, useEffect } from 'react';
import * as api from '../../../services/api';

/**
 * Custom hook for managing history entries data
 * @param {Object} filterOptions - Options for filtering history entries
 * @param {string} filterOptions.sortBy - Sort criteria
 * @param {string|null} filterOptions.filterSource - Filter by source
 * @param {string} filterOptions.searchTerm - Search term
 * @param {Function} showNotification - Function to show notifications
 * @returns {Object} History entries state and loading status
 */
const useHistoryEntries = ({ sortBy, filterSource, searchTerm }, showNotification) => {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);

  /**
   * Load history entries from API with current filter settings
   */
  const loadHistory = async () => {
    try {
      setLoading(true);
      
      // Check auth status first to handle invalid tokens
      await api.checkAuthStatus();
      
      const response = await api.getHistoryPreview(sortBy, filterSource, searchTerm);
      
      // Ensure entries is always an array, even if response is invalid
      if (!response || !response.entries) {
        console.warn('History response missing entries array, using empty array');
        setEntries([]);
      } else {
        setEntries(response.entries);
      }
    } catch (error) {
      console.error('Error loading history:', error);
      setEntries([]); // Ensure we set an empty array on error
      showNotification('Error loading history: ' + (error.message || 'Unknown error'), 'error');
    } finally {
      setLoading(false);
    }
  };

  // Load history when filter options change
  useEffect(() => {
    loadHistory();
  }, [sortBy, filterSource, searchTerm]);

  /**
   * Force reload the history entries
   */
  const refreshEntries = () => {
    loadHistory();
  };

  return {
    entries,
    loading,
    refreshEntries
  };
};

export default useHistoryEntries; 