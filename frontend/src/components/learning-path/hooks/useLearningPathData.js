import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useLocation } from 'react-router';
import { getLearningPath, getHistoryEntry, getPublicLearningPath } from '../../../services/api';
import { getOfflinePath } from '../../../services/offlineService';

const POLLING_INTERVAL = 5000; // 5 seconds
const MAX_POLLING_ATTEMPTS = 360; // 30 minutes (360 attempts * 5 seconds)

/**
 * Custom hook to load course data from different sources.
 * Handles direct history loads, public path loads, or generation via taskId (using polling).
 * 
 * @param {string} source - Optional source override ('history', 'public' or null for generation)
 * @returns {Object} { learningPath, loading, error, isFromHistory, initialDetailsWereSet, persistentPathId, temporaryPathId, refreshData, progressMap, setProgressMap, lastVisitedModuleIdx, lastVisitedSubmoduleIdx, isPublicView }
 */
const useLearningPathData = (source = null) => {
  const { taskId, entryId, shareId, offlineId } = useParams();
  const location = useLocation();
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isFromHistory, setIsFromHistory] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [temporaryPathId, setTemporaryPathId] = useState(null); // Kept for consistency if needed by UI before save
  const [persistentPathId, setPersistentPathId] = useState(null);
  const [initialDetailsWereSet, setInitialDetailsWereSet] = useState(false);
  const [progressMap, setProgressMap] = useState({});
  const [lastVisitedModuleIdx, setLastVisitedModuleIdx] = useState(null);
  const [lastVisitedSubmoduleIdx, setLastVisitedSubmoduleIdx] = useState(null);
  
  const [isPublicView, setIsPublicView] = useState(source === 'public' || !!shareId);

  // Refs for polling
  const pollingTimeoutRef = useRef(null);
  const pollingAttemptsRef = useRef(0);

  const shouldLoadFromHistory =
    source === 'history' ||
    location.pathname.startsWith('/history/') ||
    !!entryId;

  const shouldLoadOffline = source === 'offline' || location.pathname.startsWith('/offline/') || !!offlineId;
    
  const shouldLoadPublic = source === 'public' || !!shareId;

  const refreshData = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, []);

  // Effect to load data or setup polling
  useEffect(() => {
    const cleanup = () => {
      if (pollingTimeoutRef.current) {
        clearTimeout(pollingTimeoutRef.current);
        pollingTimeoutRef.current = null;
      }
      pollingAttemptsRef.current = 0;
    };
    
    cleanup(); // Clear any existing polling on new load trigger

    const loadData = async () => {
      console.log('useLearningPathData: Starting load...', { taskId, entryId, shareId, offlineId, shouldLoadFromHistory, shouldLoadPublic, shouldLoadOffline, source });
      setLoading(true);
      setError(null);
      setData(null); 
      setTemporaryPathId(null);
      setPersistentPathId(null); // Reset persistentPathId on new load
      setIsFromHistory(false); // Reset isFromHistory
      setInitialDetailsWereSet(false);
      setProgressMap({});
      setLastVisitedModuleIdx(null);
      setLastVisitedSubmoduleIdx(null);
      setIsPublicView(source === 'public' || !!shareId);
      pollingAttemptsRef.current = 0;
      
      try {
        if (shouldLoadOffline) {
          console.log('useLearningPathData: Loading offline path...', offlineId);
          const offlineData = getOfflinePath(offlineId);
          if (!offlineData) {
            throw new Error('Offline learning path not found.');
          }
          setData(offlineData);
          setIsFromHistory(false);
          setPersistentPathId(offlineId);
          setInitialDetailsWereSet(true);
          setProgressMap(offlineData.progress_map || {});
          setLastVisitedModuleIdx(offlineData.last_visited_module_idx);
          setLastVisitedSubmoduleIdx(offlineData.last_visited_submodule_idx);
          setLoading(false);
        } else if (shouldLoadFromHistory) {
          console.log('useLearningPathData: Loading from history...', entryId);
          const historyResponse = await getHistoryEntry(entryId); 
          
          if (!historyResponse || !historyResponse.entry) {
            throw new Error('Learning path not found in history or invalid response format.');
          }
          const entry = historyResponse.entry; 
          setData(entry); // path_data is within entry, or entry itself might be path_data based on structure
          setIsFromHistory(true);
          setPersistentPathId(entryId); // entry.path_id should be same as entryId
          setInitialDetailsWereSet((entry.tags && entry.tags.length > 0) || entry.favorite === true);
          setProgressMap(entry.progress_map || {});
          setLastVisitedModuleIdx(entry.last_visited_module_idx);
          setLastVisitedSubmoduleIdx(entry.last_visited_submodule_idx);
          setLoading(false);
        } else if (shouldLoadPublic) {
          console.log('useLearningPathData: Loading public path...', shareId);
          if (!shareId) throw new Error('Missing shareId for public course.');
          
          const publicResponse = await getPublicLearningPath(shareId);
          if (!publicResponse) throw new Error('Public course not found or invalid response format.');

          setData(publicResponse.path_data || publicResponse); // Assuming path_data or the root object
          setPersistentPathId(publicResponse.path_id); 
          setIsFromHistory(false); // It's public, not user's history directly
          setInitialDetailsWereSet(true); // Public paths are considered 'set' in terms of details
          // Public paths might not have user-specific progress, but can have general structure
          setProgressMap(publicResponse.progress_map || {}); 
          setLastVisitedModuleIdx(publicResponse.last_visited_module_idx); // Could be null
          setLastVisitedSubmoduleIdx(publicResponse.last_visited_submodule_idx); // Could be null
          setLoading(false);
        } else if (taskId) {
          console.log('useLearningPathData: Starting generation tracking via polling...', taskId);
          setInitialDetailsWereSet(false); 
          // Generate a temporary ID for immediate use if the UI needs it before persistence
          const tempId = crypto.randomUUID(); 
          setTemporaryPathId(tempId);
          
          // Start polling
          pollingAttemptsRef.current = 0;
          pollForTaskStatus(taskId);
        } else {
           console.error("useLearningPathData: Missing identifiers for loading.");
           setError("ID is missing, cannot load course.");
           setLoading(false);
        }
      } catch (err) {
        console.error('Error in loadData setup:', err);
        setError(err.message || 'Error loading course.');
        setLoading(false);
        cleanup();
      }
    };

    const pollForTaskStatus = async (currentTaskId) => {
      if (pollingAttemptsRef.current >= MAX_POLLING_ATTEMPTS) {
        console.error(`Max polling attempts reached for task ${currentTaskId}.`);
        setError('Course generation is taking longer than expected. Please check back later or try refreshing.');
        setLoading(false);
        return;
      }

      try {
        console.log(`Polling for task ${currentTaskId}, attempt ${pollingAttemptsRef.current + 1}`);
        const responseData = await getLearningPath(currentTaskId);
        pollingAttemptsRef.current++;

        if (responseData.status === 'completed' && responseData.result) {
          console.log('Polling successful: Task completed.', responseData.result);
          setData(responseData.result);
          // If the result has a path_id, it means it was saved to history during generation
          if (responseData.result.path_id) {
            setPersistentPathId(responseData.result.path_id);
            // Potentially update isFromHistory or initialDetailsWereSet if a backend save happened
            // For now, assume it's still a "newly generated" path until user explicitly saves via UI action
          }
          setProgressMap(responseData.result.progress_map || {});
          setLastVisitedModuleIdx(responseData.result.last_visited_module_idx);
          setLastVisitedSubmoduleIdx(responseData.result.last_visited_submodule_idx);
          setError(null);
          setLoading(false);
        } else if (responseData.status === 'failed') {
          console.log('Polling successful: Task failed.', responseData.error);
          const errorDetails = responseData.error || {};
          setError(errorDetails.message || 'Learning path generation failed.'); 
          setData(null); // Clear any partial data
          setLoading(false);
        } else if (responseData.status === 'pending' || responseData.status === 'running') {
          // Continue polling
          pollingTimeoutRef.current = setTimeout(() => pollForTaskStatus(currentTaskId), POLLING_INTERVAL);
        } else {
          console.warn('Unexpected status in polling response:', responseData.status);
          setError('Received an unexpected status from the server. Please try refreshing.');
          setLoading(false);
        }
      } catch (err) {
        console.error(`Error during polling attempt for task ${currentTaskId}:`, err);
        // Consider more nuanced error handling for retries on network errors vs. 404s
        if (pollingAttemptsRef.current < MAX_POLLING_ATTEMPTS / 2) { // Retry a few times for network issues
            pollingTimeoutRef.current = setTimeout(() => pollForTaskStatus(currentTaskId), POLLING_INTERVAL * 2); // Longer delay on error
        } else {
            setError(err.message || 'Failed to get course status. Please check your connection or try refreshing.');
            setLoading(false);
        }
      }
    };
    
    loadData();

    return cleanup; // Cleanup function for useEffect
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId, entryId, shareId, offlineId, source, refreshTrigger]);

  return {
    learningPath: data,
    loading,
    error,
    isFromHistory,
    initialDetailsWereSet,
    persistentPathId,
    temporaryPathId,
    refreshData,
    progressMap,
    setProgressMap,
    lastVisitedModuleIdx,
    lastVisitedSubmoduleIdx,
    isPublicView,
  };
};

export default useLearningPathData; 