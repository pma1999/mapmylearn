import { useState, useEffect, useRef, useCallback } from 'react';
import * as api from '../../../services/api';

/**
 * Enhanced loading state interface for granular UI control
 */
const createLoadingState = () => ({
  initialLoading: false,      // True only on first load with no cache
  backgroundRefreshing: false, // True when fetching fresh data with cache available
  showingCache: false         // True when displaying cached data
});

/**
 * Global cache that persists across component re-renders
 * This survives auth context re-initializations and component unmounting
 */
const globalHistoryCache = {};

/**
 * Smart merge function for combining history entries and active generations
 * Ensures consistent sorting and duplicate handling
 * @param {Array} historyEntries - Array of history entries from API
 * @param {Array} activeGenerations - Array of active generation tasks
 * @param {string} sortBy - Current sort criteria
 * @returns {Array} Merged and sorted array of entries
 */
const mergeEntriesWithActiveGenerations = (historyEntries, activeGenerations, sortBy) => {
  // Map active generations to consistent format
  const mappedActiveGenerations = activeGenerations.map(task => ({
    ...task,
    topic: task.request_topic, // Map request_topic to topic
    isActive: true // Mark active tasks
  }));

  // For most sort orders, we want active generations at the top
  // Exception: alphabetical sorting should sort everything together
  if (sortBy === 'topic') {
    // Merge all entries and sort alphabetically
    const allEntries = [...mappedActiveGenerations, ...historyEntries];
    return allEntries.sort((a, b) => {
      const topicA = (a.topic || '').toLowerCase();
      const topicB = (b.topic || '').toLowerCase();
      return topicA.localeCompare(topicB);
    });
  } else {
    // For date-based and favorite sorting, put active generations first
    return [...mappedActiveGenerations, ...historyEntries];
  }
};

/**
 * Custom hook for managing history entries data with optimized loading and pagination
 * Now fetches both active generations and completed history entries with immediate cache display.
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
  const [loadingState, setLoadingState] = useState(createLoadingState);
  const [initialLoadComplete, setInitialLoadComplete] = useState(false);
  const [error, setError] = useState(null);
  // Store full pagination state
  const [pagination, setPagination] = useState({ total: 0, page: 1, perPage: 10 });
  const [stats, setStats] = useState({ loadTime: 0 });
  
  // Use global cache that survives re-renders instead of useRef
  // const previousEntriesRef = useRef({}); // Replaced with globalHistoryCache
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
   * Load history entries and active generations from API with parallel loading and immediate cache display
   * Implements stale-while-revalidate pattern with parallel loading and smart data merging
   */
  const loadHistoryAndGenerations = useCallback(async (forceRefresh = false) => {
    // Prevent too frequent refreshes (throttle to at most once per second)
    const now = Date.now();
    if (!forceRefresh && now - lastLoadTimeRef.current < 1000) {
      console.log('Throttling: Skipping load, too recent');
      return;
    }
    
    // Check for cached data first
    const cacheKey = getCacheKey();
    const cachedData = globalHistoryCache[cacheKey];
    
    // If we have fresh cache (less than 30 seconds old) and it's not a forced refresh, use cache only
    if (cachedData && !forceRefresh && cachedData.timestamp && (now - cachedData.timestamp) < 30000) {
      console.log('Using fresh cache, skipping API call');
      setEntries(cachedData.entries);
      setPagination({ 
        total: cachedData.total || 0, 
        page: cachedData.page || page, 
        perPage: cachedData.perPage || perPage 
      });
      setStats({
        loadTime: 0,
        fromCache: true,
        initialLoad: !initialLoadComplete,
        serverTime: cachedData.serverTime
      });
      setLoadingState({
        initialLoading: false,
        backgroundRefreshing: false,
        showingCache: true
      });
      if (!initialLoadComplete) {
        setInitialLoadComplete(true);
      }
      return; // CRITICAL: Return early to skip API call
    }
    
    // For stale cache (>30 seconds), show it immediately but refresh in background
    if (cachedData && !forceRefresh) {
      console.log('Using stale cache, will refresh in background');
      setEntries(cachedData.entries);
      setPagination({ 
        total: cachedData.total || 0, 
        page: cachedData.page || page, 
        perPage: cachedData.perPage || perPage 
      });
      setStats({
        loadTime: 0,
        fromCache: true,
        initialLoad: !initialLoadComplete,
        serverTime: cachedData.serverTime
      });
      setLoadingState({
        initialLoading: false,
        backgroundRefreshing: true,
        showingCache: true
      });
      if (!initialLoadComplete) {
        setInitialLoadComplete(true);
      }
    }
    
    // Show initial loading state for first load without cache
    if (!initialLoadComplete) {
      setLoadingState({
        initialLoading: true,
        backgroundRefreshing: false,
        showingCache: false
      });
    } else {
      // For subsequent loads without cache, show background refresh
      setLoadingState(prev => ({
        ...prev,
        backgroundRefreshing: true
      }));
    }
    
    lastLoadTimeRef.current = now;
    
    // Increment load counter for this session (used for stale request detection)
    const currentLoadCount = ++loadCountRef.current;
    
    console.log(`🚀 Loading history data: cache=${!!cachedData}, forceRefresh=${forceRefresh}, key=${cacheKey}`);
    
    try {
      // Cancel any in-flight requests
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      
      // Create a new abort controller for this request
      abortControllerRef.current = new AbortController();
      const signal = abortControllerRef.current.signal;
      
      // Start measuring load time
      const startTime = performance.now();
      
      // Set loading state if no cache was used
      if (!cachedData) {
        if (!initialLoadComplete) {
          setLoadingState({
            initialLoading: true,
            backgroundRefreshing: false,
            showingCache: false
          });
        } else {
          setLoadingState(prev => ({
            ...prev,
            backgroundRefreshing: true
          }));
        }
      }
      
      // Check auth status first to handle invalid tokens (only if no valid cache)
      if (!cachedData) {
        await api.checkAuthStatus();
      }
      
      // Use parallel loading with deduplication and abort signal
      const parallelResult = await api.loadHistoryDataParallelDeduped(
        sortBy, 
        filterSource, 
        searchTerm, 
        page, 
        perPage, 
        signal
      );
      
      console.log(`API call completed in ${(performance.now() - startTime).toFixed(1)}ms`);
      
      // If this is a stale request (a newer one has started), ignore the results
      if (currentLoadCount < loadCountRef.current) {
        console.log('Ignoring stale response from previous request');
        return;
      }
      
      // Calculate load time
      const loadTime = performance.now() - startTime;
      
      // Process the parallel loading results
      const { historyResult, activeGenerationsResult, errors } = parallelResult;
      
      // Handle errors gracefully - show what we can and notify about failures
      if (errors.history && errors.activeGenerations) {
        // Both requests failed
        if (entries.length > 0) {
          // Keep showing cached data if available
          setLoadingState({
            initialLoading: false,
            backgroundRefreshing: false,
            showingCache: true
          });
          showNotification('Failed to refresh data from server', 'warning');
        } else {
          // No cached data, show error state
          setEntries([]);
          setPagination({ total: 0, page: 1, perPage: perPage });
          setLoadingState({
            initialLoading: false,
            backgroundRefreshing: false,
            showingCache: false
          });
          setError('Failed to load history data');
          showNotification('Error loading history: ' + (errors.history?.message || 'Unknown error'), 'error');
        }
        return;
      }
      
      // Handle partial failures with notifications
      if (errors.activeGenerations) {
        showNotification('Could not load active generations: ' + (errors.activeGenerations?.message || 'Unknown error'), 'warning');
      }
      if (errors.history) {
        showNotification('Could not load history: ' + (errors.history?.message || 'Unknown error'), 'warning');
      }
      
      // Merge the results using smart merging
      const historyEntries = historyResult?.entries || [];
      const activeGenerations = activeGenerationsResult || [];
      const mergedEntries = mergeEntriesWithActiveGenerations(historyEntries, activeGenerations, sortBy);
      
      // Update cache with the history result (for future cache hits)
      if (historyResult) {
        const cacheEntry = {
          ...historyResult,
          entries: mergedEntries, // Store merged entries for consistency
          timestamp: now // Add timestamp for freshness check
        };
        console.log('✅ Storing in cache with key:', cacheKey);
        globalHistoryCache[cacheKey] = cacheEntry;
      }
      
      // Only update state if data has actually changed or this is a forced refresh
      const entriesChanged = JSON.stringify(entries) !== JSON.stringify(mergedEntries);
      const paginationChanged = historyResult && (
        pagination.total !== historyResult.total || 
        pagination.page !== historyResult.page || 
        pagination.perPage !== historyResult.perPage
      );

      if (entriesChanged || paginationChanged || forceRefresh) {
        setEntries(mergedEntries);
        
        if (historyResult) {
          setPagination({ 
            total: historyResult.total || 0, // Pagination info comes from history preview
            page: historyResult.page || page, 
            perPage: historyResult.perPage || perPage 
          });
        }
        
        setStats({
          loadTime, 
          fromCache: false,
          serverTime: historyResult?.request_time_ms,
          initialLoad: !initialLoadComplete,
          total: historyResult?.total || 0,
          parallelLoad: true // Indicate this was a parallel load
        });
      }
      
      setInitialLoadComplete(true);
      // Set final loading state - no longer loading or refreshing
      setLoadingState({
        initialLoading: false,
        backgroundRefreshing: false,
        showingCache: false
      });
      setError(null);
      
    } catch (error) {
      // Ignore aborted requests
      if (error.name === 'AbortError') {
        console.log('Request was aborted:', error);
        return;
      }
      
      console.error('Error loading history:', error);
      
      // If we have cached data, keep showing it and just show error for refresh
      if (entries.length > 0) {
        setLoadingState({
          initialLoading: false,
          backgroundRefreshing: false,
          showingCache: true
        });
        showNotification('Failed to refresh data: ' + (error.message || 'Unknown error'), 'warning');
      } else {
        // Only set error state if no cached data is available
        setEntries([]); // Ensure we set an empty array on error
        setPagination({ total: 0, page: 1, perPage: perPage }); // Reset pagination
        setLoadingState({
          initialLoading: false,
          backgroundRefreshing: false,
          showingCache: false
        });
        setError(error.message || 'Unknown error');
        showNotification('Error loading history: ' + (error.message || 'Unknown error'), 'error');
      }
    }
  }, [sortBy, filterSource, searchTerm, page, perPage, getCacheKey, showNotification]);
  
  // Load history when filter or pagination options change
  useEffect(() => {
    loadHistoryAndGenerations();
    
    // Cleanup function
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [sortBy, filterSource, searchTerm, page, perPage]); // Removed loadHistoryAndGenerations to prevent infinite loop
  
  /**
   * Force reload the history entries
   */
  const refreshEntries = useCallback(() => {
    setLoadingState(prev => ({
      ...prev,
      backgroundRefreshing: true
    }));
    loadHistoryAndGenerations(true);
  }, [loadHistoryAndGenerations]);

  // Backward compatibility: provide legacy 'loading' property
  const legacyLoading = loadingState.initialLoading;
  
  return {
    entries,
    pagination,
    loading: legacyLoading, // Legacy compatibility
    loadingState, // New enhanced loading state
    error,
    stats,
    initialLoadComplete,
    refreshEntries
  };
};

export default useHistoryEntries; 