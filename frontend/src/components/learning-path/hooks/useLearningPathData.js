import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useLocation } from 'react-router';
import { getLearningPath, getHistoryEntry, API_URL } from '../../../services/api';

/**
 * Custom hook to load learning path data from different sources.
 * Handles direct history loads or generation via taskId, including SSE progress.
 * 
 * @param {string} source - Optional source override ('history' or null)
 * @returns {Object} { learningPath, loading, error, isFromHistory, savedToHistory, refreshData, temporaryPathId, progressMessages, isReconnecting, retryAttempt, progressMap, setProgressMap, lastVisitedModuleIdx, lastVisitedSubmoduleIdx }
 */
const useLearningPathData = (source = null) => {
  const { taskId, entryId } = useParams();
  const location = useLocation();
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isFromHistory, setIsFromHistory] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [temporaryPathId, setTemporaryPathId] = useState(null);
  const [progressMessages, setProgressMessages] = useState([]); 
  const [persistentPathId, setPersistentPathId] = useState(null);
  const [initialDetailsWereSet, setInitialDetailsWereSet] = useState(false);
  const [progressMap, setProgressMap] = useState({});
  const [lastVisitedModuleIdx, setLastVisitedModuleIdx] = useState(null);
  const [lastVisitedSubmoduleIdx, setLastVisitedSubmoduleIdx] = useState(null);
  
  // State for SSE reconnection logic
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [retryAttempt, setRetryAttempt] = useState(0);
  const retryTimeoutRef = useRef(null);
  const MAX_RETRIES = 5; // Max reconnection attempts
  
  // Ref to hold the EventSource instance
  const eventSourceRef = useRef(null);
  // Ref to track if completion/error was already signaled by onmessage
  const receivedFinalSignalRef = useRef(false); 

  // Determine if data should be loaded from history
  const shouldLoadFromHistory = 
    source === 'history' || 
    location.pathname.startsWith('/history/') || 
    !!entryId;

  // Function to manually refresh data
  const refreshData = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, []);

  // Helper function to attempt fetching the final result first
  const tryFetchFinalResult = async (id) => {
    console.log('Attempting to fetch final result directly for task:', id);
    try {
      const responseData = await getLearningPath(id);
      
      // Handle successful fetch (task completed or failed)
      if (responseData.status === 'completed' && responseData.result) {
        console.log('Direct fetch successful: Task completed.');
        setData(responseData.result);
        const tempId = crypto.randomUUID();
        setTemporaryPathId(tempId);
        setIsFromHistory(false);
        setPersistentPathId(responseData.result.path_id || null);
        setError(null);
        setLoading(false);
        return { status: 'completed' };
      } else if (responseData.status === 'failed') {
        console.log('Direct fetch successful: Task failed.');
        setError(responseData.error?.message || 'Learning path generation failed.');
        setData(null);
        setLoading(false);
        return { status: 'failed' };
      } else {
        // Unexpected status in a successful response (e.g., PENDING/RUNNING)
        console.warn('Unexpected status in successful result fetch:', responseData.status);
        // Treat as still processing and proceed to SSE
        return { status: 'processing' };
      }
    } catch (err) {
      // Handle errors during fetch attempt
      if (err.message === 'Task not found') {
        // This is the 404 case from getLearningPath
        // Assume task is still processing or non-existent; SSE will handle it.
        console.log('Direct fetch resulted in "Task not found" (404), proceeding to SSE.');
        return { status: 'processing' };
      } else {
        // Any other error (network, server error 5xx, etc.)
        console.error('Error during initial fetch attempt:', err);
        setError(err.message || 'Failed to check task status.');
        setData(null);
        setLoading(false);
        return { status: 'error' };
      }
    }
  };

  // Effect to load data or setup SSE
  useEffect(() => {
    // Ensure previous EventSource is closed AND retry timer is cleared on re-run/unmount
    const cleanup = () => {
      if (eventSourceRef.current) {
        console.log('useLearningPathData: Cleaning up EventSource.');
        eventSourceRef.current.close();
      }
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }
      setIsReconnecting(false);
      setRetryAttempt(0);
      receivedFinalSignalRef.current = false; // Reset signal flag
    };
    
    cleanup(); // Clean up before starting

    const loadData = async () => {
      console.log('useLearningPathData: Starting load...', { taskId, entryId, shouldLoadFromHistory });
      setLoading(true);
      setError(null);
      setData(null); 
      setTemporaryPathId(null);
      setProgressMessages([]); 
      setIsReconnecting(false); 
      setRetryAttempt(0);    
      receivedFinalSignalRef.current = false; 
      setProgressMap({});
      setLastVisitedModuleIdx(null);
      setLastVisitedSubmoduleIdx(null);
      
      try {
        if (shouldLoadFromHistory) {
          // --- Load from History --- 
          console.log('useLearningPathData: Loading from history...', entryId);
          setInitialDetailsWereSet(false); // Reset on new load
          const historyResponse = await getHistoryEntry(entryId); // Returns { entry: { ... } }
          
          // Log the raw response structure
          // console.log('API History Entry Response Object:', historyResponse); // <-- REMOVE/COMMENT THIS LOG
          
          // Corrected Check: Check for the nested entry object
          if (!historyResponse || !historyResponse.entry) {
            throw new Error('Learning path not found in history or invalid response format.');
          }

          // Corrected Extraction: Access the nested entry object
          const entry = historyResponse.entry; 
          const pathData = entry.path_data || entry; // Use path_data if present, otherwise the entry itself
          const fetchedProgressMap = entry.progress_map || {}; // Extract new progress map
          const fetchedLastVisitedModIdx = entry.last_visited_module_idx;
          const fetchedLastVisitedSubIdx = entry.last_visited_submodule_idx;
          
          // Check details on the actual entry object
          if ((entry.tags && entry.tags.length > 0) || entry.favorite === true) {
            console.log('useLearningPathData: History entry has existing details (tags/favorite).');
            setInitialDetailsWereSet(true);
          }
          
          // Set state with the correct path data object
          setData(pathData);
          setIsFromHistory(true);
          setPersistentPathId(entryId);
          setProgressMap(fetchedProgressMap);
          setLastVisitedModuleIdx(fetchedLastVisitedModIdx);
          setLastVisitedSubmoduleIdx(fetchedLastVisitedSubIdx);
          setLoading(false);
          console.log('useLearningPathData: History load complete. Progress Map:', fetchedProgressMap, 'Last Visited:', fetchedLastVisitedModIdx, fetchedLastVisitedSubIdx);
        
        } else if (taskId) {
          // --- Load via Generation Task (Modified) --- 
          setInitialDetailsWereSet(false); // Reset/ensure false for generation
          
          // 1. Attempt to fetch final result directly first
          const initialResult = await tryFetchFinalResult(taskId);

          // 2. Only connect to SSE if the initial fetch indicated processing is needed
          if (initialResult.status === 'processing') {
            connectSSE();
          }
          // If initialResult status was 'completed', 'failed', or 'error', 
          // the state (loading, data, error) was already set by tryFetchFinalResult.
          
        } else {
           // Should not happen if routing is correct (ResultPage requires taskId)
           console.error("useLearningPathData: Missing taskId for generation.");
           setError("Task ID is missing, cannot load learning path.");
            setLoading(false);
        }
      } catch (err) {
        // Catch errors during initial setup (e.g., history fetch)
        console.error('Error in loadData setup:', err);
        setError(err.message || 'Error loading learning path.');
        setLoading(false);
        if (eventSourceRef.current) {
          eventSourceRef.current.close(); // Ensure cleanup on outer catch
          eventSourceRef.current = null;
        }
      }
    };
    
    // Helper function to fetch the final result
    const fetchFinalResult = async (id) => {
        console.log('Fetching final result for task:', id);
        try {
            const finalResponse = await getLearningPath(id);
            if (finalResponse.status === 'completed' && finalResponse.result) {
                setData(finalResponse.result);
                setIsFromHistory(false);
                setPersistentPathId(finalResponse.result.path_id || null);
                setError(null); // Clear any previous transient errors
            } else if (finalResponse.status === 'failed') {
                 console.error('Final fetch indicated failure:', finalResponse.error?.message);
                 setError(finalResponse.error?.message || 'Learning path generation failed.');
            } else {
                 // Should not happen if SSE signaled completion, but handle defensively
                 console.warn('Final fetch status was not completed/failed:', finalResponse.status);
                 setError('Failed to retrieve the completed learning path data.');
            }
        } catch (fetchErr) {
            console.error('Error fetching final learning path after SSE completion:', fetchErr);
            setError(fetchErr.message || 'Error retrieving final learning path data.');
        } finally {
            setLoading(false); // Always stop loading after attempting final fetch
            // Add conditional close logic here
            if (receivedFinalSignalRef.current && eventSourceRef.current) {
                console.log('Closing EventSource after successful signal and final fetch.');
                eventSourceRef.current.close();
                eventSourceRef.current = null;
            }
        }
    };

    // Function to connect to SSE (remains mostly the same, just called conditionally)
    const connectSSE = () => {
      console.log('useLearningPathData: Starting generation tracking via SSE...', taskId);
      // Reset signal flag before connecting
      receivedFinalSignalRef.current = false; 
      // Ensure loading is true when connecting/reconnecting (might already be true)
      if (!loading) setLoading(true); 
      // Clear previous errors on connection attempt (tryFetchFinalResult might have set one)
      if (error) setError(null); 
            
      // Only show initializing message on first connect, not retries
      if (retryAttempt === 0 && progressMessages.length === 0) {
          setProgressMessages([{ message: 'Initializing learning path generation...', timestamp: Date.now(), phase: 'initialization', progress: 0.0 }]);
      }

      // Construct the FULL URL for EventSource using the imported API_URL
      const apiUrl = `${API_URL}/api/progress/${taskId}`; 
      console.log(`useLearningPathData: Connecting to SSE: ${apiUrl} (Attempt: ${retryAttempt + 1})`);
      const es = new EventSource(apiUrl); // Use the full URL
      eventSourceRef.current = es; // Store instance in ref

      es.onopen = () => {
        console.log('SSE Connection Opened Successfully.');
        if (isReconnecting) {
          setIsReconnecting(false);
          setRetryAttempt(0);
          if (retryTimeoutRef.current) {
            clearTimeout(retryTimeoutRef.current);
            retryTimeoutRef.current = null;
          }
        }
      };
      
      es.onmessage = (event) => {
        try {
          if (retryAttempt > 0) { setRetryAttempt(0); }
          if (isReconnecting) {
              setIsReconnecting(false); 
              if (retryTimeoutRef.current) { clearTimeout(retryTimeoutRef.current); retryTimeoutRef.current = null; }
          }
          
          if (event.data === '{\"complete\": true}') {
             console.log('SSE stream signaled completion.');
             receivedFinalSignalRef.current = true; 
             fetchFinalResult(taskId); // Call fetch, it will handle closing later
             return; 
          }

          const progressData = JSON.parse(event.data);
          console.log('SSE Message Received:', progressData);
          
          let progressValue = progressData.progress;
          if (progressValue !== undefined && progressValue !== null) {
              progressValue = Math.max(0, Math.min(1, Number(progressValue)));
              if (isNaN(progressValue)) progressValue = null;
          }
          
          setProgressMessages(prev => [...prev, {
            message: progressData.message || 'Processing...',
            timestamp: progressData.timestamp || Date.now(),
            phase: progressData.phase,
            progress: progressValue,
            action: progressData.action,
            preview_data: progressData.preview_data
          }]);

          if (progressData.status === 'failed' || progressData.action === 'error' || progressData.level === 'ERROR') {
              console.error('SSE JSON signaled failure:', progressData.message);
              receivedFinalSignalRef.current = true;
              setError(progressData.message || 'Learning path generation failed during progress updates.');
              setLoading(false);
          }

          if (progressData.persistentPathId) {
            setPersistentPathId(progressData.persistentPathId);
          }

        } catch (parseError) {
          console.error('Error parsing SSE message:', event.data, parseError);
        }
      };

      es.onerror = (err) => {
        console.error('EventSource failed:', err);
        es.close(); 
        eventSourceRef.current = null;
        
        if (receivedFinalSignalRef.current) {
            console.log('SSE error occurred after a final signal (complete/fail) was received. Not retrying.');
            return; 
        }

        if (retryAttempt < MAX_RETRIES) {
          const delay = Math.pow(2, retryAttempt) * 1000; 
          setRetryAttempt(prev => prev + 1);
          setIsReconnecting(true);
          console.log(`Attempting to reconnect in ${delay / 1000}s... (Attempt ${retryAttempt + 1}/${MAX_RETRIES})`);
          
          if (retryTimeoutRef.current) { clearTimeout(retryTimeoutRef.current); }
          
          retryTimeoutRef.current = setTimeout(() => {
            connectSSE(); 
          }, delay);
        } else {
          // --- Modified Max Retry Logic ---
          console.log('Max retries reached. Performing final status check via API.');
          setIsReconnecting(false); // Ensure this is reset

          // Use an IIFE to handle async call within the synchronous handler logic flow
          (async () => {
              const finalCheckResult = await tryFetchFinalResult(taskId);
              console.log('Final API check status:', finalCheckResult.status);

              // Only set the connection error if the final API check didn't resolve the state
              if (finalCheckResult.status !== 'completed' && finalCheckResult.status !== 'failed') {
                  console.error('Final API check did not resolve to completed/failed status. Setting connection error.');
                  setError('Connection lost after multiple retries. Please check the History page for final status.');
                  // setLoading(false) should already be handled by tryFetchFinalResult in this case (error or processing)
                  // Ensure loading is false just in case tryFetch didn't set it
                  if(loading) setLoading(false); 
              } else {
                  // State was successfully updated by tryFetchFinalResult
                  console.log('Successfully recovered final state via API after SSE failure.');
              }
          })();
          // --- End Modified Max Retry Logic ---
        }
      };
    };

    // Execute loading logic
    loadData();

    // Cleanup function for useEffect
    return cleanup;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId, entryId, shouldLoadFromHistory, refreshTrigger]); // Keep original dependencies

  return {
    learningPath: data,
    loading,
    error,
    isFromHistory,
    initialDetailsWereSet,
    persistentPathId,
    temporaryPathId,
    progressMessages,
    isReconnecting, 
    retryAttempt,
    refreshData,
    progressMap,
    setProgressMap,
    lastVisitedModuleIdx,
    lastVisitedSubmoduleIdx
  };
};

export default useLearningPathData; 