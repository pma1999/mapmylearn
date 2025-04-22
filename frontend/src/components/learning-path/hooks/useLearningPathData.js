import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { getLearningPath, getHistoryEntry, API_URL } from '../../../services/api';

/**
 * Custom hook to load learning path data from different sources.
 * Handles direct history loads or generation via taskId, including SSE progress.
 * 
 * @param {string} source - Optional source override ('history' or null)
 * @returns {Object} { learningPath, loading, error, isFromHistory, savedToHistory, refreshData, temporaryPathId, progressMessages }
 */
const useLearningPathData = (source = null) => {
  const { taskId, entryId } = useParams();
  const location = useLocation();
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isFromHistory, setIsFromHistory] = useState(false);
  const [savedToHistory, setSavedToHistory] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [temporaryPathId, setTemporaryPathId] = useState(null);
  const [progressMessages, setProgressMessages] = useState([]); 
  
  // Ref to hold the EventSource instance
  const eventSourceRef = useRef(null);

  // Determine if data should be loaded from history
  const shouldLoadFromHistory = 
    source === 'history' || 
    location.pathname.startsWith('/history/') || 
    !!entryId;

  // Function to manually refresh data
  const refreshData = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, []);

  // Effect to load data or setup SSE
  useEffect(() => {
    // Ensure previous EventSource is closed on re-run
    if (eventSourceRef.current) {
      console.log('useLearningPathData: Closing previous EventSource due to dependency change.');
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    const loadData = async () => {
      console.log('useLearningPathData: Starting load...', { taskId, entryId, shouldLoadFromHistory });
      setLoading(true);
      setError(null);
      setData(null); 
      setTemporaryPathId(null);
      setProgressMessages([]); 
      
      try {
        if (shouldLoadFromHistory) {
          // --- Load from History --- 
          console.log('useLearningPathData: Loading from history...', entryId);
          const historyResponse = await getHistoryEntry(entryId);
          
          if (!historyResponse || !historyResponse.entry) {
            throw new Error('Learning path not found in history.');
          }
          
          const pathData = historyResponse.entry.path_data || historyResponse.entry;
          setData(pathData);
          setIsFromHistory(true);
          setSavedToHistory(true);
          setLoading(false);
          console.log('useLearningPathData: History load complete.');
        
        } else if (taskId) {
          // --- Load via Generation Task (SSE) --- 
          console.log('useLearningPathData: Starting generation tracking...', taskId);
          setProgressMessages([{ message: 'Initializing learning path generation...', timestamp: Date.now(), phase: 'initialization', progress: 0.0 }]);
          setLoading(true); // Ensure loading is true

          // Construct the FULL URL for EventSource using the imported API_URL
          const apiUrl = `${API_URL}/api/progress/${taskId}`; 
          console.log(`useLearningPathData: Connecting to SSE: ${apiUrl}`);
          const es = new EventSource(apiUrl); // Use the full URL
          eventSourceRef.current = es; // Store instance in ref

          es.onmessage = (event) => {
            try {
              // Check for the specific completion signal string first
              if (event.data === '{"complete": true}') {
                 console.log('SSE stream signaled completion.');
                 es.close();
                 eventSourceRef.current = null;
                 // Fetch final result *after* completion is signaled
                 fetchFinalResult(taskId);
                 return; 
              }

              // If not the completion string, parse the JSON payload
              const progressData = JSON.parse(event.data);
              console.log('SSE Message Received:', progressData);
              
              // Add the new message to the list
              let progressValue = progressData.progress;
              if (progressValue !== undefined && progressValue !== null) {
                  progressValue = Math.max(0, Math.min(1, Number(progressValue)));
                  if (isNaN(progressValue)) progressValue = null; // Handle NaN
              }
              
              setProgressMessages(prev => [...prev, {
                message: progressData.message || 'Processing...', // Default message
                timestamp: progressData.timestamp || Date.now(),
                phase: progressData.phase,
                progress: progressValue, // Use validated progress
                action: progressData.action,
                preview_data: progressData.preview_data
              }]);

              // Check ONLY for failure signals within the JSON payload
              // DO NOT treat phase completion (action: 'completed') as overall completion
              if (progressData.status === 'failed' || progressData.action === 'error' || progressData.level === 'ERROR') {
                  console.error('SSE JSON signaled failure:', progressData.message);
                  setError(progressData.message || 'Learning path generation failed during progress updates.');
                  setLoading(false);
                  es.close();
                  eventSourceRef.current = null;
                  // No need to return here, just stop processing
              }

            } catch (parseError) {
              console.error('Error parsing SSE message:', event.data, parseError);
              // Optional: Set error state on parse failure?
              // setError('Failed to parse progress update from server.');
              // setLoading(false);
              // if (es) es.close(); // Ensure es is defined before closing
              // eventSourceRef.current = null;
            }
          };

          es.onerror = (err) => {
            console.error('EventSource failed:', err);
            // Only set error if we are still in loading state and haven't received final data/error yet.
            // This avoids overriding a completion/failure signal that might have just closed the stream.
            if (loading && !error && !data) { 
                setError('Connection to progress updates was lost unexpectedly.');
                setLoading(false);
            }
            es.close(); // Close the connection on error
            eventSourceRef.current = null;
          };
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
                const tempId = crypto.randomUUID();
                setTemporaryPathId(tempId);
                setSavedToHistory(false); 
                setIsFromHistory(false);
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
        }
    };

    // Execute loading logic
      loadData();

    // Cleanup function for useEffect: Close EventSource if component unmounts
    return () => {
      if (eventSourceRef.current) {
        console.log('useLearningPathData: Cleaning up EventSource on unmount/re-run.');
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId, entryId, shouldLoadFromHistory, refreshTrigger]); // Dependencies

  return {
    learningPath: data,
    loading,
    error,
    isFromHistory,
    savedToHistory,
    refreshData,
    temporaryPathId,
    progressMessages 
  };
};

export default useLearningPathData; 