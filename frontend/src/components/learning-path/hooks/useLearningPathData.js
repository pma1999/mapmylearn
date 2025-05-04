import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useLocation } from 'react-router';
import { getLearningPath, getHistoryEntry, getPublicLearningPath, API_URL } from '../../../services/api';

/**
 * Custom hook to load course data from different sources.
 * Handles direct history loads or generation via taskId, including SSE progress.
 * Also handles loading public paths via shareId.
 * 
 * @param {string} source - Optional source override ('history', 'public' or null for generation)
 * @returns {Object} { learningPath, loading, error, isFromHistory, initialDetailsWereSet, persistentPathId, temporaryPathId, progressMessages, isReconnecting, retryAttempt, refreshData, progressMap, setProgressMap, lastVisitedModuleIdx, lastVisitedSubmoduleIdx, isPublicView, accumulatedPreviewData }
 */
const useLearningPathData = (source = null) => {
  const { taskId, entryId, shareId } = useParams();
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
  const [accumulatedPreviewData, setAccumulatedPreviewData] = useState(null);
  
  // NEW: State to explicitly track if it's a public view
  const [isPublicView, setIsPublicView] = useState(source === 'public' || !!shareId);

  // State for SSE reconnection logic
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [retryAttempt, setRetryAttempt] = useState(0);
  const retryTimeoutRef = useRef(null);
  const MAX_RETRIES = 5; // Max reconnection attempts
  
  // Ref to hold the EventSource instance
  const eventSourceRef = useRef(null);
  // Ref to track if completion/error was already signaled by onmessage
  const receivedFinalSignalRef = useRef(false); 
  // Ref to track if connection was ever opened successfully
  const connectionOpenedRef = useRef(false);

  // Determine if data should be loaded from history or public
  const shouldLoadFromHistory = 
    source === 'history' || 
    location.pathname.startsWith('/history/') || 
    !!entryId;
    
  const shouldLoadPublic = source === 'public' || !!shareId;

  // Function to manually refresh data
  const refreshData = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, []);

  // Helper function to attempt fetching the final result first
  const tryFetchFinalResult = async (id, isInitialAttempt = false) => {
    console.log(`Attempting to fetch final result ${isInitialAttempt ? 'initially' : 'finally'} for task:`, id);
    try {
      const responseData = await getLearningPath(id);
      
      // Handle successful fetch (task completed or failed)
      if (responseData.status === 'completed' && responseData.result) {
        console.log('Direct fetch successful: Task completed.');
        setData(responseData.result);
        // Only set temporary ID if it's the *initial* fetch completion
        // Otherwise, it might overwrite a temp ID set by SSE
        if (isInitialAttempt) {
           const tempId = crypto.randomUUID(); 
           setTemporaryPathId(tempId);
        } 
        setIsFromHistory(false);
        setPersistentPathId(responseData.result.path_id || null);
        // Initialize progress map and last visited from the final result
        setProgressMap(responseData.result.progress_map || {});
        setLastVisitedModuleIdx(responseData.result.last_visited_module_idx);
        setLastVisitedSubmoduleIdx(responseData.result.last_visited_submodule_idx);
        setError(null);
        setLoading(false);
        setIsReconnecting(false); // Ensure reconnecting is false
        return { status: 'completed' };
      } else if (responseData.status === 'failed') {
        console.log('Direct fetch successful: Task failed.');
        // Use the structured error if available
        const errorDetails = responseData.error || {};
        setError(errorDetails.message || 'Learning path generation failed.'); 
        setData(null);
        setLoading(false);
        setIsReconnecting(false); // Ensure reconnecting is false
        return { status: 'failed' };
      } else {
        console.warn('Unexpected status in successful result fetch:', responseData.status);
        if (isInitialAttempt) {
           // On initial attempt, if status is not final, proceed to SSE
           return { status: 'processing' };
        } else {
           // On final attempt after SSE/retries, this is unexpected
           setError('Failed to retrieve the completed course data (unexpected status).');
           setData(null);
           setLoading(false);
           setIsReconnecting(false); 
           return { status: 'error' };
        }
      }
    } catch (err) {
      if (err.response?.status === 404 || err.message?.includes('not found')) {
        console.log('Direct fetch resulted in "Task not found" (404).');
        if (isInitialAttempt) {
             // Assume task is processing or doesn't exist yet; proceed to SSE
            return { status: 'processing' };
        } else {
             // After SSE/retries, a 404 is a more definite error
             setError('Failed to retrieve the course. Task not found.');
             setData(null);
             setLoading(false);
             setIsReconnecting(false);
             return { status: 'error' };
        }
      } else {
        console.error(`Error during ${isInitialAttempt ? 'initial' : 'final'} fetch attempt:`, err);
        setError(err.message || `Failed to ${isInitialAttempt ? 'check task status' : 'retrieve final result'}.`);
        setData(null);
        setLoading(false);
        setIsReconnecting(false); // Ensure reconnecting is false on error
        return { status: 'error' };
      }
    }
  };

  // Effect to load data or setup SSE
  useEffect(() => {
    const cleanup = () => {
      if (eventSourceRef.current) {
        console.log('useLearningPathData: Cleaning up EventSource.');
        eventSourceRef.current.close();
        eventSourceRef.current = null; // Clear ref immediately
      }
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }
      setIsReconnecting(false);
      setRetryAttempt(0);
      receivedFinalSignalRef.current = false; 
      connectionOpenedRef.current = false; // Reset connection open flag
    };
    
    cleanup();

    const loadData = async () => {
      console.log('useLearningPathData: Starting load...', { taskId, entryId, shareId, shouldLoadFromHistory, shouldLoadPublic, source });
      setLoading(true);
      setError(null);
      setData(null); 
      setTemporaryPathId(null);
      setProgressMessages([]); 
      setIsReconnecting(false); 
      setRetryAttempt(0);    
      receivedFinalSignalRef.current = false; 
      connectionOpenedRef.current = false; 
      setProgressMap({});
      setLastVisitedModuleIdx(null);
      setLastVisitedSubmoduleIdx(null);
      setAccumulatedPreviewData(null);
      setIsPublicView(source === 'public' || !!shareId);
      
      try {
        if (shouldLoadFromHistory) {
          // --- Load from History --- 
          console.log('useLearningPathData: Loading from history...', entryId);
          setInitialDetailsWereSet(false); 
          const historyResponse = await getHistoryEntry(entryId); 
          
          if (!historyResponse || !historyResponse.entry) {
            throw new Error('Learning path not found in history or invalid response format.');
          }

          const entry = historyResponse.entry; 
          // Update data partially first with topic
          setData({ topic: entry.topic }); 

          const pathData = entry.path_data || entry; 
          const fetchedProgressMap = entry.progress_map || {}; 
          const fetchedLastVisitedModIdx = entry.last_visited_module_idx;
          const fetchedLastVisitedSubIdx = entry.last_visited_submodule_idx;
          
          if ((entry.tags && entry.tags.length > 0) || entry.favorite === true) {
            console.log('useLearningPathData: History entry has existing details (tags/favorite).');
            setInitialDetailsWereSet(true);
          }
          
          // Set the full data state
          setData(entry);
          setIsFromHistory(true);
          setPersistentPathId(entryId);
          setProgressMap(fetchedProgressMap);
          setLastVisitedModuleIdx(fetchedLastVisitedModIdx);
          setLastVisitedSubmoduleIdx(fetchedLastVisitedSubIdx);
          
          // Set loading to false LAST
          setLoading(false);
          console.log('useLearningPathData: History load complete.');
        
        } else if (shouldLoadPublic) {
          // --- Load Public Path --- 
          console.log('useLearningPathData: Loading public path...', shareId);
          setInitialDetailsWereSet(true); 
          setIsFromHistory(false); 
          
          if (!shareId) {
            throw new Error('Missing shareId for public course.');
          }
          
          const publicResponse = await getPublicLearningPath(shareId);
          
          if (!publicResponse) {
             throw new Error('Public course not found or invalid response format.');
          }

          // Update data partially first with topic
          setData({ topic: publicResponse.topic }); 
          
          // Set the full data state
          const pathData = publicResponse.path_data || publicResponse; 
          const fetchedProgressMap = publicResponse.progress_map || {}; 
          const fetchedLastVisitedModIdx = publicResponse.last_visited_module_idx;
          const fetchedLastVisitedSubIdx = publicResponse.last_visited_submodule_idx;

          setData(pathData);
          setPersistentPathId(publicResponse.path_id); 
          setProgressMap(fetchedProgressMap);
          setLastVisitedModuleIdx(fetchedLastVisitedModIdx);
          setLastVisitedSubmoduleIdx(fetchedLastVisitedSubIdx);
          
          // Set loading to false LAST
          setLoading(false);
          console.log('useLearningPathData: Public load complete.');

        } else if (taskId) {
          // --- Load via Generation Task (Modified) --- 
          setInitialDetailsWereSet(false); 
          
          // 1. Attempt to fetch final result directly first
          const initialResult = await tryFetchFinalResult(taskId, true); 

          // 2. Only connect to SSE if the initial fetch indicated processing is needed
          if (initialResult.status === 'processing') {
            connectSSE();
          }
          
        } else {
           console.error("useLearningPathData: Missing taskId/entryId/shareId for loading.");
           setError("ID is missing, cannot load course.");
            setLoading(false);
        }
      } catch (err) {
        console.error('Error in loadData setup:', err);
        setError(err.message || 'Error loading course.');
        setLoading(false);
        cleanup(); // Ensure cleanup on outer catch
      }
    };
    
    // Helper function to fetch the final result (used after SSE completes/fails)
    const fetchFinalResultAfterSSE = async (id) => {
       await tryFetchFinalResult(id, false); // Mark as *not* initial attempt
       // Ensure cleanup after final fetch attempt
       if (eventSourceRef.current) {
          console.log('Closing EventSource after final fetch attempt.');
          eventSourceRef.current.close();
          eventSourceRef.current = null;
       } 
    };

    // Function to connect to SSE
    const connectSSE = () => {
      console.log('useLearningPathData: Starting generation tracking via SSE...', taskId);
      receivedFinalSignalRef.current = false; 
      if (!loading && !isReconnecting) setLoading(true); // Only set loading if not already loading/reconnecting
      if (error && isReconnecting) setError(null); // Clear error only if reconnecting (might be a transient network error)
            
      if (retryAttempt === 0 && progressMessages.length === 0) {
          // Keep the initial message simple, snapshot will provide more details
          setProgressMessages([{ message: 'Connecting to generation progress...', timestamp: Date.now(), phase: 'connection', progress: null }]); 
      }

      const apiUrl = `${API_URL}/api/progress/${taskId}`;
      console.log(`useLearningPathData: Connecting to SSE: ${apiUrl} (Attempt: ${retryAttempt + 1})`);
      
      // Ensure previous instance is closed before creating a new one
      if (eventSourceRef.current) {
         console.warn('connectSSE called while an EventSource instance already exists. Closing previous.');
         eventSourceRef.current.close();
      }
      
      const es = new EventSource(apiUrl);
      eventSourceRef.current = es; // Store NEW instance

      es.onopen = () => {
        console.log('SSE Connection Opened Successfully.');
        connectionOpenedRef.current = true; // Mark connection as opened
        // --- State Reset on Successful Open --- 
        setIsReconnecting(false); 
        setRetryAttempt(0);
        if (retryTimeoutRef.current) {
            clearTimeout(retryTimeoutRef.current);
            retryTimeoutRef.current = null;
        }
        // --- End State Reset --- 
      };
      
      es.onmessage = (event) => {
        try {
          // --- State Reset on Receiving Message --- 
          // (Redundant if onopen fired, but good fallback)
          if (isReconnecting || retryAttempt > 0) {
             console.log('Received message, resetting reconnect state.');
             setIsReconnecting(false);
             setRetryAttempt(0);
             if (retryTimeoutRef.current) { clearTimeout(retryTimeoutRef.current); retryTimeoutRef.current = null; }
          }
          // --- End State Reset --- 
          
          // Handle completion signal first
          if (event.data === '{"complete": true}') {
             console.log('SSE stream signaled completion.');
             receivedFinalSignalRef.current = true; 
             fetchFinalResultAfterSSE(taskId); // Fetch final result
             return; // Stop processing further messages for this stream
          }

          // Parse and process regular progress messages
          const progressData = JSON.parse(event.data);
          console.log('SSE Message Received:', progressData);

          // ---> MODIFICATION START: Handle partial module updates <---
          if (progressData.preview_data && progressData.preview_data.module_update) {
            const moduleUpdate = progressData.preview_data.module_update;
            setAccumulatedPreviewData(prevData => {
              // Initialize state if it's the first update or null
              let newData = prevData ? { ...prevData } : { modules: [] };
              // Ensure modules array exists
              newData.modules = newData.modules || []; 

              // Find the index of the module to update
              const moduleIndex = newData.modules.findIndex(m => m.id === moduleUpdate.module_id);

              if (moduleIndex > -1) {
                // Module exists, update its title and submodules
                newData.modules[moduleIndex] = {
                    ...newData.modules[moduleIndex], // Keep existing fields
                    title: moduleUpdate.title,
                    submodules: moduleUpdate.submodules,
                    id: moduleUpdate.module_id // Ensure id is set
                };
              } else {
                // Module doesn't exist, add it
                newData.modules.push({
                  id: moduleUpdate.module_id,
                  title: moduleUpdate.title,
                  submodules: moduleUpdate.submodules
                });
                // Ensure modules are sorted by id after adding a new one
                newData.modules.sort((a, b) => (a.id ?? Infinity) - (b.id ?? Infinity)); 
              }
              
              console.log('Merged module update into preview data:', newData);
              return newData;
            });
          } else if (progressData.preview_data && progressData.preview_data.modules && !progressData.preview_data.module_update) {
             // ---> MODIFICATION START: Merge incoming module list, don't replace <---
             const incomingModules = progressData.preview_data.modules;
             console.log('Received base module preview data, merging:', incomingModules);
             setAccumulatedPreviewData(prevData => {
                let newData = prevData ? { ...prevData } : { modules: [] };
                newData.modules = newData.modules || [];
                
                const existingModuleMap = new Map(newData.modules.map(m => [m.id, m]));

                incomingModules.forEach((incomingMod, index) => {
                  // --- Ensure incoming module has an ID (use index as fallback) ---
                  const modId = incomingMod.id ?? index; 
                  if (existingModuleMap.has(modId)) {
                    // Module exists, update basic info but keep existing submodules
                    const existingMod = existingModuleMap.get(modId);
                    existingMod.title = incomingMod.title;
                    // Optionally update description if provided
                    if (incomingMod.description) {
                        existingMod.description = incomingMod.description;
                    }
                  } else {
                    // Module is new, add it (without submodules initially)
                     newData.modules.push({
                       ...incomingMod, // Spread incoming data (like title, desc)
                       id: modId, // Ensure ID is set
                       submodules: [] // Initialize empty submodules
                     });
                  }
                });

                // Ensure final array is sorted by ID
                newData.modules.sort((a, b) => (a.id ?? Infinity) - (b.id ?? Infinity));
                
                return newData;
             });
             // ---> MODIFICATION END <---
          }
          // ---> MODIFICATION END <---
          
          // Check for specific error messages from the backend stream
          if (progressData.error && progressData.type === 'stream_error') {
             console.error('Received error message from SSE stream:', progressData.error);
             setError(progressData.error || 'An error occurred during generation stream.');
             receivedFinalSignalRef.current = true; // Treat as final signal
             setLoading(false);
             setIsReconnecting(false); // Ensure reconnecting is false
             // Close the event source on explicit stream error
             if (eventSourceRef.current) {
                 eventSourceRef.current.close();
                 eventSourceRef.current = null;
             }
             return;
          }
          
          // Validate progress value (optional but good practice)
          let overallProgressValue = progressData.overall_progress;
          if (overallProgressValue !== undefined && overallProgressValue !== null) {
              overallProgressValue = Math.max(0, Math.min(1, Number(overallProgressValue)));
              if (isNaN(overallProgressValue)) overallProgressValue = null;
          }
          
          // Update progress messages state
          setProgressMessages(prev => {
             // Avoid adding duplicate messages (simple check based on message content)
             if (prev.length > 0 && prev[prev.length - 1].message === progressData.message) {
                 return prev;
             }
             return [...prev, {
                 message: progressData.message || 'Processing...', // Default message
                 timestamp: progressData.timestamp || Date.now(),
                 phase: progressData.phase,
                 overall_progress: overallProgressValue, // Use validated value
                 preview_data: progressData.preview_data, // Pass preview data through
                 action: progressData.action,
                 // Add any other relevant fields from progressData
             }];
          });

          // Handle persistent path ID updates from SSE
          if (progressData.persistentPathId && !persistentPathId) {
            console.log('Received persistentPathId via SSE:', progressData.persistentPathId);
            setPersistentPathId(progressData.persistentPathId);
          }
          
          // If an update message is received, assume loading is still true
          if (!loading) setLoading(true);
          // Clear any transient network error if we get a valid message
          if (error) setError(null); 

        } catch (parseError) {
          console.error('Error parsing SSE message:', event.data, parseError);
          // Don't necessarily set a global error here, maybe just log it
        }
      };

      es.onerror = (err) => {
        // Ignore errors if a completion signal was already received
        if (receivedFinalSignalRef.current) {
            console.log('SSE error occurred after final signal. Ignoring.');
            if (eventSourceRef.current) {
                 eventSourceRef.current.close(); // Ensure closed
                 eventSourceRef.current = null;
            }
            return; 
        }
        
        console.error('EventSource failed:', err);
        if (eventSourceRef.current) {
            eventSourceRef.current.close(); // Close the current failed connection
            eventSourceRef.current = null;
        }
        
        // Only attempt retries if the connection was opened at least once OR if it's the first attempt
        if (connectionOpenedRef.current || retryAttempt < MAX_RETRIES) {
           if (retryAttempt < MAX_RETRIES) {
             const delay = Math.pow(2, retryAttempt) * 1000 + Math.random() * 1000; // Add jitter
             // --- Set Reconnecting State BEFORE Timeout --- 
             setIsReconnecting(true);
             setRetryAttempt(prev => prev + 1); 
             // --- End Set Reconnecting State --- 
             console.log(`Attempting to reconnect in ${delay / 1000}s... (Attempt ${retryAttempt + 1}/${MAX_RETRIES})`);
             
             if (retryTimeoutRef.current) { clearTimeout(retryTimeoutRef.current); }
             
             retryTimeoutRef.current = setTimeout(() => {
               // Only reconnect if still in reconnecting state (prevents race conditions)
               if (isReconnecting) { 
                  connectSSE(); 
               }
             }, delay);
           } else {
             // --- Max Retries Reached --- 
             console.log('Max retries reached. Performing final status check via API.');
             setIsReconnecting(true); // Keep reconnecting true during final check
             
             (async () => {
                 await fetchFinalResultAfterSSE(taskId);
                 // fetchFinalResultAfterSSE will set loading/error/reconnecting state appropriately
             })();
             // --- End Max Retry Logic --- 
           } 
        } else {
             // If connection NEVER opened and retries exhausted (or not applicable)
             console.error('SSE connection never established successfully.');
             setError('Failed to connect to progress updates. Please check your network or try again later.');
             setLoading(false);
             setIsReconnecting(false);
        }
      };
    };

    // Execute loading logic
    loadData();

    // Cleanup function for useEffect
    return cleanup;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId, entryId, shareId, source, refreshTrigger]); // Add shareId and source dependencies

  return {
    learningPath: data,
    loading,
    error,
    isFromHistory,
    initialDetailsWereSet,
    persistentPathId,
    temporaryPathId,
    progressMessages, // Pass the full messages array
    isReconnecting, 
    retryAttempt,
    refreshData,
    progressMap,
    setProgressMap,
    lastVisitedModuleIdx,
    lastVisitedSubmoduleIdx,
    isPublicView, // Return public view status
    accumulatedPreviewData, // <-- RETURN STATE
  };
};

export default useLearningPathData; 