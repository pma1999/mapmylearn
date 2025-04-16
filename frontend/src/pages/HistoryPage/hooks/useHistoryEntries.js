import { useState, useEffect, useRef, useCallback } from 'react';
import * as api from '../../../services/api';

/**
 * Custom hook for managing history entries data with optimized loading and pagination
 * @param {Object} filterOptions - Options for filtering history entries
 * @param {string} filterOptions.sortBy - Sort criteria
 * @param {string|null} filterOptions.filterSource - Filter by source
 * @param {string} filterOptions.searchTerm - Search term
 * @param {number} filterOptions.page - Current page number
 * @param {number} filterOptions.perPage - Items per page
 * @param {Function} showNotification - Function to show notifications
 * @returns {Object} History entries state, pagination info, and loading status
 */
const useHistoryEntries = ({ sortBy, filterSource, searchTerm, page, perPage }, showNotification) => {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [initialLoadComplete, setInitialLoadComplete] = useState(false);
  const [error, setError] = useState(null);
  // Store full pagination state
  const [pagination, setPagination] = useState({ total: 0, page: 1, perPage: 10 });
  const [stats, setStats] = useState({ loadTime: 0 }); // Remove total from here
  
  // Cache previous results for stale-while-revalidate pattern
  const previousEntriesRef = useRef({});
  const requestRef = useRef(null);
  const abortControllerRef = useRef(null);
  const lastLoadTimeRef = useRef(0);
  const loadCountRef = useRef(0);
  
  /**
   * Generate a cache key from the filter options including pagination
   * @returns {string} Cache key
   */
  const getCacheKey = useCallback(() => {
    return `${sortBy}:${filterSource || 'all'}:${searchTerm || 'none'}:${page}:${perPage}`;
  }, [sortBy, filterSource, searchTerm, page, perPage]);
  
  /**
   * Load history entries from API with current filter and pagination settings
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
          setPagination({ 
            total: cachedData.total || 0, 
            page: cachedData.page || page, 
            perPage: cachedData.perPage || perPage 
          });
          setStats({
            loadTime: 0,
            fromCache: true,
            initialLoad: true,
            serverTime: cachedData.serverTime
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
      
      // Make the API call with pagination
      requestRef.current = api.getHistoryPreview(sortBy, filterSource, searchTerm, page, perPage);
      const response = await requestRef.current;
      
      // If this is a stale request (a newer one has started), ignore the results
      if (currentLoadCount < loadCountRef.current) {
        console.log('Ignoring stale response from previous request');
        return;
      }
      
      // Calculate load time
      const loadTime = performance.now() - startTime;
      
      // Update cache with full response including pagination
      previousEntriesRef.current[cacheKey] = response;
      
      // Ensure response format is valid
      if (!response || !response.entries || !Array.isArray(response.entries)) {
        console.warn('History response missing or invalid entries array, using empty array');
        setEntries([]);
        setPagination({ total: 0, page: 1, perPage: perPage }); // Reset pagination
        setStats({ 
          loadTime, 
          fromCache: false,
          initialLoad: !initialLoadComplete 
        });
      } else {
        // Only update state if the data has actually changed
        const entriesChanged = JSON.stringify(entries) !== JSON.stringify(response.entries);
        const paginationChanged = pagination.total !== response.total || pagination.page !== response.page || pagination.perPage !== response.perPage;

        if (entriesChanged || paginationChanged || forceRefresh) {
          setEntries(response.entries);
          setPagination({ 
            total: response.total || 0, 
            page: response.page || page, 
            perPage: response.perPage || perPage 
          });
          setStats({
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
      setEntries([]); // Ensure we set an empty array on error
      setPagination({ total: 0, page: 1, perPage: perPage }); // Reset pagination
      setLoading(false);
      setError(error.message || 'Unknown error');
      showNotification('Error loading history: ' + (error.message || 'Unknown error'), 'error');
    }
  }, [sortBy, filterSource, searchTerm, page, perPage, initialLoadComplete, getCacheKey, showNotification, entries, pagination]);
  
  // Load history when filter or pagination options change
  useEffect(() => {
    loadHistory();
    
    // Remove polling logic - refresh should be triggered explicitly or by cache invalidation
    /*
    const pollingInterval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        loadHistory(false);
      }
    }, 30000);
    */
    
    // Cleanup function
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      // clearInterval(pollingInterval);
    };
  }, [sortBy, filterSource, searchTerm, page, perPage, loadHistory]);
  
  /**
   * Force reload the history entries (resets to page 1 potentially, or current page?)
   * Let's keep it simple: reloads current view.
   */
  const refreshEntries = useCallback(() => {
    setLoading(true);
    loadHistory(true);
  }, [loadHistory]);
  
  return {
    entries,
    pagination, // Return pagination state
    loading,
    error,
    stats,
    initialLoadComplete,
    refreshEntries
  };
};

export default useHistoryEntries; 