import { useState, useEffect, useRef, useCallback } from 'react';
import * as api from '../../../services/api';

/**
 * Custom hook for managing history entries data with optimized loading
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
  const [initialLoadComplete, setInitialLoadComplete] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({ total: 0, loadTime: 0 });
  
  // Cache previous results for stale-while-revalidate pattern
  const previousEntriesRef = useRef({});
  const requestRef = useRef(null);
  const abortControllerRef = useRef(null);
  const lastLoadTimeRef = useRef(0);
  const loadCountRef = useRef(0);
  
  /**
   * Generate a cache key from the filter options
   * @returns {string} Cache key
   */
  const getCacheKey = useCallback(() => {
    return `${sortBy}:${filterSource || 'all'}:${searchTerm || 'none'}`;
  }, [sortBy, filterSource, searchTerm]);
  
  /**
   * Load history entries from API with current filter settings
   * Implements stale-while-revalidate pattern and aborts ongoing requests
   */
  const loadHistory = useCallback(async (forceRefresh = false) => {
    // Prevent too frequent refreshes (throttle to at most once per second)
    const now = Date.now();
    if (!forceRefresh && now - lastLoadTimeRef.current < 1000) {
      return;
    }
    lastLoadTimeRef.current = now;
    
    // Increment load counter for this session
    const currentLoadCount = ++loadCountRef.current;
    
    try {
      // Cancel any in-flight requests
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      
      // Create a new abort controller for this request
      abortControllerRef.current = new AbortController();
      
      // Start measuring load time
      const startTime = performance.now();
      
      // If we already have a cached entry for these filters and not forcing refresh,
      // immediately show it without waiting for network
      const cacheKey = getCacheKey();
      const cachedData = previousEntriesRef.current[cacheKey];
      
      if (cachedData && !forceRefresh) {
        // Immediately show cached data (stale-while-revalidate pattern)
        if (!initialLoadComplete) {
          setEntries(cachedData.entries);
          setStats({
            total: cachedData.total || 0,
            loadTime: 0,
            fromCache: true,
            initialLoad: true
          });
          setInitialLoadComplete(true);
          setLoading(false);
        }
      } else if (!initialLoadComplete) {
        // Show loading state for first load
        setLoading(true);
      }
      
      // Check auth status first to handle invalid tokens
      await api.checkAuthStatus();
      
      // Make the API call without waiting for the previous ones to return
      requestRef.current = api.getHistoryPreview(sortBy, filterSource, searchTerm);
      const response = await requestRef.current;
      
      // If this is a stale request (a newer one has started), ignore the results
      if (currentLoadCount < loadCountRef.current) {
        console.log('Ignoring stale response from previous request');
        return;
      }
      
      // Calculate load time
      const loadTime = performance.now() - startTime;
      
      // Update cache
      previousEntriesRef.current[cacheKey] = response;
      
      // Ensure entries is always an array, even if response is invalid
      if (!response || !response.entries) {
        console.warn('History response missing entries array, using empty array');
        setEntries([]);
        setStats({ 
          total: 0, 
          loadTime, 
          fromCache: false,
          initialLoad: !initialLoadComplete 
        });
      } else {
        // Only update state if the data has actually changed
        const entriesChanged = JSON.stringify(entries) !== JSON.stringify(response.entries);
        
        if (entriesChanged || forceRefresh) {
          setEntries(response.entries);
          setStats({
            total: response.total || 0,
            loadTime, 
            fromCache: false,
            serverTime: response.request_time_ms,
            initialLoad: !initialLoadComplete
          });
        }
      }
      
      setInitialLoadComplete(true);
      setLoading(false);
      setError(null);
    } catch (error) {
      // Ignore aborted requests
      if (error.name === 'AbortError') {
        console.log('Request was aborted:', error);
        return;
      }
      
      console.error('Error loading history:', error);
      
      // Only set error state if no cached data is available
      if (!initialLoadComplete) {
        setEntries([]); // Ensure we set an empty array on error
        setLoading(false);
        setError(error.message || 'Unknown error');
        showNotification('Error loading history: ' + (error.message || 'Unknown error'), 'error');
      }
    }
  }, [sortBy, filterSource, searchTerm, initialLoadComplete, getCacheKey, showNotification, entries]);
  
  // Load history when filter options change
  useEffect(() => {
    loadHistory();
    
    // Set up polling for background updates (every 30 seconds)
    const pollingInterval = setInterval(() => {
      // Only poll if the page is visible to save resources
      if (document.visibilityState === 'visible') {
        loadHistory(false);
      }
    }, 30000); // 30 seconds
    
    // Cleanup function to abort any pending requests on unmount or filter change
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      clearInterval(pollingInterval);
    };
  }, [sortBy, filterSource, searchTerm, loadHistory]);
  
  /**
   * Force reload the history entries
   */
  const refreshEntries = useCallback(() => {
    setLoading(true);
    loadHistory(true);
  }, [loadHistory]);
  
  return {
    entries,
    loading,
    error,
    stats,
    initialLoadComplete,
    refreshEntries
  };
};

export default useHistoryEntries; 