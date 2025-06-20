import { useState, useEffect, useRef, useCallback, useReducer } from 'react';
import { streamProgressUpdates, getLearningPath } from '../../../services/api';

// --- Initial state for liveBuildData ---
const initialLiveBuildData = {
  topic: sessionStorage.getItem('currentTopic') || 'Loading topic...',
  overallStatusMessage: 'Initializing generation...',
  overallProgress: 0,
  searchQueries: [], // { text: 'query', status: 'generated' }
  topicResources: {
    status: 'pending', // pending, loading, completed, error
    count: 0,
    resources_preview: [], // { title, type, url_preview }
  },
  modules: [], // Array of module objects, see structure in plan
  error: null, // To store any general error object from SSE
};

// --- Reducer function for liveBuildData ---
function liveBuildDataReducer(state, action) {
  const { type, payload } = action;
  // console.log("Reducer action:", type, payload); // For debugging

  switch (type) {
    case 'GENERATION_STARTED':
      return {
        ...state,
        topic: payload.topic || state.topic,
        language: payload.language || state.language,
        overallStatusMessage: `Starting generation for: ${payload.topic || state.topic}`,
        overallProgress: 0,
        searchQueries: [],
        topicResources: initialLiveBuildData.topicResources,
        modules: [],
        error: null,
      };
    case 'SET_TOPIC':
      return { ...state, topic: payload.topic };
    case 'OVERALL_PROGRESS_UPDATE':
      return { 
        ...state, 
        overallProgress: payload.overall_progress !== undefined ? payload.overall_progress : state.overallProgress,
        overallStatusMessage: payload.message || state.overallStatusMessage 
      };
    case 'search_queries_generated':
      return {
        ...state,
        searchQueries: payload.queries ? payload.queries.map(q => ({ text: q, status: 'generated' })) : [],
        overallStatusMessage: `Generated ${payload.queries?.length || 0} search queries.`
      };
    case 'modules_defined':
      return {
        ...state,
        modules: payload.modules ? payload.modules.map(m => ({ 
          id: m.id,
          title: m.title,
          order: m.order,
          descriptionPreview: m.description_preview,
          status: 'defined',
          resourceStatus: 'pending',
          resourceCount: 0,
          resources_preview: [],
          submodules: [] 
        })) : [],
        overallStatusMessage: `Defined ${payload.modules?.length || 0} modules.`
      };
    case 'module_submodules_planned':
      return {
        ...state,
        modules: state.modules.map(module => 
          module.id === payload.module_id 
            ? { 
                ...module, 
                submodules: payload.submodules ? payload.submodules.map(sm => ({ 
                  id: sm.id, 
                  title: sm.title, 
                  order: sm.order,
                  descriptionPreview: sm.description_preview,
                  status: 'planned',
                  resourceStatus: 'pending',
                  resourceCount: 0,
                  resources_preview: []
                })) : [],
                status: 'submodules_planned' 
              }
            : module
        ),
        overallStatusMessage: `Planned ${payload.submodules?.length || 0} submodules for ${payload.module_title}.`
      };
    case 'SUBMODULE_PROCESSING_STARTED':
    case 'SUBMODULE_STATUS_UPDATE':
    case 'SUBMODULE_COMPLETED':
    case 'SUBMODULE_ERROR':
      return {
        ...state,
        modules: state.modules.map(module =>
          module.id === payload.module_id
            ? {
                ...module,
                submodules: module.submodules.map(submodule =>
                  submodule.id === payload.submodule_id
                    ? { 
                        ...submodule, 
                        status: payload.status_detail || submodule.status, 
                        // Potentially update other fields based on status_detail
                        quiz_question_count: type === 'SUBMODULE_COMPLETED' ? payload.quiz_question_count : submodule.quiz_question_count,
                        error: type === 'SUBMODULE_ERROR' ? payload.error_message : null
                      }
                    : submodule
                ),
              }
            : module
        ),
        overallStatusMessage: payload.submodule_title ? 
          `Updating ${payload.submodule_title}: ${payload.status_detail || type}`:
          state.overallStatusMessage
      };
    case 'TOPIC_RESOURCES_STARTED':
      return { ...state, topicResources: { ...state.topicResources, status: 'loading' } };
    case 'TOPIC_RESOURCES_UPDATE':
      return {
        ...state,
        topicResources: {
          status: 'completed',
          count: payload.resource_count,
          resources_preview: payload.resources_preview || []
        },
        overallStatusMessage: `Found ${payload.resource_count} topic resources.`
      };
    case 'MODULE_RESOURCES_STARTED':
      return {
        ...state,
        modules: state.modules.map(m => m.id === payload.module_id ? {...m, resourceStatus: 'loading'} : m)
      };
    case 'MODULE_RESOURCES_UPDATE':
      return {
        ...state,
        modules: state.modules.map(m =>
          m.id === payload.module_id
            ? { 
                ...m, 
                resourceStatus: 'completed', 
                resourceCount: payload.resource_count,
                resources_preview: payload.resources_preview || []
              }
            : m
        ),
        overallStatusMessage: `Found ${payload.resource_count} resources for module ${payload.module_title || ''}.`
      };
    case 'SUBMODULE_RESOURCES_STARTED': // Renamed from SUBMODULE_RESOURCE_STATUS_UPDATE with generation_started
    case 'SUBMODULE_RESOURCE_STATUS_UPDATE':
         return {
            ...state,
            modules: state.modules.map(module =>
              module.id === payload.module_id
                ? {
                    ...module,
                    submodules: module.submodules.map(submodule =>
                      submodule.id === payload.submodule_id
                        ? { 
                            ...submodule, 
                            resourceStatus: payload.status_detail === 'generation_skipped' ? 'skipped' : (payload.status_detail?.includes('started') ? 'loading' : (payload.status_detail?.includes('completed') ? 'completed' : 'error')),
                            resourceCount: payload.resource_count !== undefined ? payload.resource_count : submodule.resourceCount,
                            resources_preview: payload.resources_preview || submodule.resources_preview,
                            error: payload.status_detail?.includes('error') ? payload.error : null
                          }
                        : submodule
                    ),
                  }
                : module
            ),
            overallStatusMessage: payload.submodule_title ? 
              `Resource update for ${payload.submodule_title}: ${payload.status_detail}`:
              state.overallStatusMessage
        };
    case 'TASK_FAILED_EVENT': // For general errors from SSE that are not specific to a component
      return { ...state, error: payload, overallStatusMessage: payload.message || "Generation failed." };
    case 'all_submodules_planned':
      return {
        ...state,
        overallStatusMessage: `All ${payload.total_submodules_planned || ''} submodules planned across ${payload.modules?.length || ''} modules.`,
      };
    case 'submodule_processing_started':
      return {
        ...state,
        modules: state.modules.map(module =>
          module.id === payload.module_id
            ? {
                ...module,
                submodules: module.submodules.map(submodule =>
                  submodule.id === payload.submodule_id
                    ? { ...submodule, status: payload.status_detail || 'processing_started' } 
                    : submodule
                ),
              }
            : module
        ),
        overallStatusMessage: payload.submodule_title ? 
          `Started processing: ${payload.submodule_title}`:
          state.overallStatusMessage
      };
    case 'topic_resources_started':
      return {
        ...state,
        topicResources: { ...state.topicResources, status: 'loading' },
        overallStatusMessage: `Searching for topic resources for ${payload.topic || state.topic}...`
      };
    case 'topic_resources_update':
      return {
        ...state,
        topicResources: {
          status: 'completed',
          count: payload.resource_count,
          resources_preview: payload.resources_preview || []
        },
        overallStatusMessage: `Found ${payload.resource_count || 0} topic resources.`
      };
    case 'submodule_status_update': // Exact match from logs
      return {
        ...state,
        modules: state.modules.map(module =>
          module.id === payload.module_id
            ? {
                ...module,
                submodules: module.submodules.map(submodule =>
                  submodule.id === payload.submodule_id
                    ? { 
                        ...submodule, 
                        status: payload.status_detail || submodule.status, 
                        queries: payload.queries !== undefined ? payload.queries : (submodule.queries || []),
                        search_result_count: payload.search_result_count !== undefined ? payload.search_result_count : (submodule.search_result_count || 0),
                        quiz_question_count: payload.quiz_question_count !== undefined ? payload.quiz_question_count : (submodule.quiz_question_count || 0),
                        resource_count: payload.resource_count !== undefined ? payload.resource_count : (submodule.resource_count || 0),
                        resourceStatus: payload.resource_status_detail ? 
                                            (payload.resource_status_detail === 'generation_skipped' ? 'skipped' : 
                                            (payload.resource_status_detail?.includes('started') ? 'loading' : 
                                            (payload.resource_status_detail?.includes('completed') ? 'completed' : 'error'))) 
                                          : submodule.resourceStatus,
                        error: payload.error_message ? payload.error_message : (payload.status_detail?.includes('error') ? 'Error in step' : submodule.error)
                      }
                    : submodule
                ),
              }
            : module
        ),
        overallStatusMessage: payload.submodule_title && payload.status_detail ?
          `${payload.submodule_title}: ${payload.status_detail}` :
          state.overallStatusMessage
      };
    case 'submodule_completed':
      return {
        ...state,
        modules: state.modules.map(module =>
          module.id === payload.module_id
            ? {
                ...module,
                submodules: module.submodules.map(submodule =>
                  submodule.id === payload.submodule_id
                    ? { 
                        ...submodule, 
                        status: payload.status_detail || 'completed',
                        quiz_question_count: payload.quiz_question_count !== undefined ? payload.quiz_question_count : submodule.quiz_question_count,
                        resource_count: payload.resource_count !== undefined ? payload.resource_count : submodule.resource_count,
                        error: null
                      }
                    : submodule
                ),
              }
            : module
        ),
        overallStatusMessage: payload.submodule_title ?
          `${payload.submodule_title} completed successfully.` :
          state.overallStatusMessage
      };
    case 'submodule_error':
      return {
        ...state,
        modules: state.modules.map(module =>
          module.id === payload.module_id
            ? {
                ...module,
                submodules: module.submodules.map(submodule =>
                  submodule.id === payload.submodule_id
                    ? { 
                        ...submodule, 
                        status: 'error',
                        error: payload.error_message 
                      }
                    : submodule
                ),
              }
            : module
        ),
        overallStatusMessage: payload.submodule_title && payload.error_message ?
          `Error in ${payload.submodule_title}: ${payload.error_message.substring(0,50)}...` :
          state.overallStatusMessage
      };
    case 'submodule_resource_status_update':
      return {
        ...state,
        modules: state.modules.map(module =>
          module.id === payload.module_id
            ? {
                ...module,
                submodules: module.submodules.map(submodule =>
                  submodule.id === payload.submodule_id
                    ? { 
                        ...submodule, 
                        resourceStatus: payload.status_detail === 'generation_skipped' ? 'skipped' : (payload.status_detail?.includes('started') ? 'loading' : (payload.status_detail?.includes('completed') ? 'completed' : 'error')),
                        resourceCount: payload.resource_count !== undefined ? payload.resource_count : submodule.resourceCount,
                        resources_preview: payload.resources_preview || submodule.resources_preview,
                        error: payload.status_detail?.includes('error') ? payload.error : null
                      }
                    : submodule
                ),
              }
            : module
        ),
        overallStatusMessage: payload.submodule_title ? 
          `Resource update for ${payload.submodule_title}: ${payload.status_detail}`:
          state.overallStatusMessage
      };
    case 'submodule_resources_started': // As seen in logs
      return {
        ...state,
        modules: state.modules.map(module =>
          module.id === payload.module_id
            ? {
                ...module,
                submodules: module.submodules.map(submodule =>
                  submodule.id === payload.submodule_id
                    ? { ...submodule, resourceStatus: 'loading' } 
                    : submodule
                ),
              }
            : module
        ),
        overallStatusMessage: payload.submodule_title ? 
          `Loading resources for ${payload.submodule_title}`:
          state.overallStatusMessage
      };
    case 'submodule_resources_update': // As seen in logs
      return {
        ...state,
        modules: state.modules.map(module =>
          module.id === payload.module_id
            ? {
                ...module,
                submodules: module.submodules.map(submodule =>
                  submodule.id === payload.submodule_id
                    ? { 
                        ...submodule, 
                        resourceStatus: 'completed', 
                        resourceCount: payload.resource_count,
                        resources_preview: payload.resources_preview || [] 
                      }
                    : submodule
                ),
              }
            : module
        ),
        overallStatusMessage: payload.submodule_title ? 
          `Updated resources for ${payload.submodule_title}`:
          state.overallStatusMessage
      };
    case 'module_resources_started': // As seen in logs
      return {
        ...state,
        modules: state.modules.map(m => m.id === payload.module_id ? {...m, resourceStatus: 'loading'} : m),
        overallStatusMessage: `Searching for resources for module: ${payload.module_title || ''}`
      };
    case 'module_resources_update': // As seen in logs
      return {
        ...state,
        modules: state.modules.map(m =>
          m.id === payload.module_id
            ? { 
                ...m, 
                resourceStatus: 'completed', 
                resourceCount: payload.resource_count,
                resources_preview: payload.resources_preview || []
              }
            : m
        ),
        overallStatusMessage: `Found ${payload.resource_count} resources for module ${payload.module_title || ''}.`
      };
    case 'COURSE_COMPLETED': // As per log (uppercase)
      return {
        ...state,
        overallStatusMessage: "Course generation complete! Finalizing...",
        overallProgress: 1.0,
        modules: state.modules.map(m => ({
          ...m,
          status: 'completed',
          resourceStatus: m.resourceStatus === 'pending' || m.resourceStatus === 'loading' ? 'completed' : m.resourceStatus,
          submodules: m.submodules.map(sm => ({
            ...sm,
            status: 'completed',
            resourceStatus: sm.resourceStatus === 'pending' || sm.resourceStatus === 'loading' ? 'completed' : sm.resourceStatus,
          }))
        }))
      };
    default:
      console.warn("Unknown reducer action type:", type, "with payload:", payload);
      return state;
  }
}

/**
 * Custom hook for tracking progress of course generation
 * 
 * @param {string} taskId - ID of the task being generated
 * @param {Function} onTaskComplete - Callback function to execute when task completes
 * @returns {Object} Progress tracking state and functions
 */
const useProgressTracking = (taskId, onTaskComplete) => {
  const [progressMessages, setProgressMessages] = useState([]);
  const [isPolling, setIsPolling] = useState(false);
  const [taskStatus, setTaskStatus] = useState(null);
  const progressEventSourceRef = useRef(null);
  const pollingIntervalRef = useRef(null);
  
  const eventIdKey = `lastEventId-${taskId}`;
  const storedLive = sessionStorage.getItem(`liveBuildData-${taskId}`);
  const [liveBuildData, dispatchLiveBuildDataUpdate] = useReducer(
    liveBuildDataReducer,
    storedLive ? JSON.parse(storedLive) : initialLiveBuildData
  );
  const lastEventIdRef = useRef(parseInt(sessionStorage.getItem(eventIdKey)) || 0);

  useEffect(() => {
    sessionStorage.setItem(`liveBuildData-${taskId}`, JSON.stringify(liveBuildData));
  }, [liveBuildData, taskId]);
  const [overallProgress, setOverallProgress] = useState(0); // Separate state for overall progress bar
  const [error, setError] = useState(null); // For task-level errors from polling or SSE 'error' action

  // Setup progress updates via Server-Sent Events
  useEffect(() => {
    if (!taskId) return;

    // Set initial topic from session storage if not already set by an event
    const storedTopic = sessionStorage.getItem('currentTopic');
    if (storedTopic && liveBuildData.topic === 'Loading topic...') {
        dispatchLiveBuildDataUpdate({ type: 'SET_TOPIC', payload: { topic: storedTopic } });
    }
    
    const setupProgressUpdates = () => {
      try {
        const eventSource = streamProgressUpdates(
          taskId,
          (eventData) => { // eventData is already parsed JSON from api.js wrapper
            console.log("Full SSE Event Data Received:", JSON.stringify(eventData, null, 2)); // Log the full event data

            if (eventData.message) {
              setProgressMessages((prev) => [...prev, eventData].slice(-100)); // Keep last 100 messages
            }

            if (eventData.id) {
              lastEventIdRef.current = eventData.id;
              sessionStorage.setItem(eventIdKey, String(eventData.id));
            }

            // Update overall progress if present in the event
            if (eventData.overall_progress !== undefined && eventData.overall_progress !== null) {
                setOverallProgress(eventData.overall_progress);
                // Also update it in liveBuildData for consistency if needed by BlueprintView
                dispatchLiveBuildDataUpdate({ type: 'OVERALL_PROGRESS_UPDATE', payload: eventData });
            } else if (eventData.phase_progress !== undefined && eventData.overall_progress === undefined) {
                 // If only phase_progress is available, we might need a more complex logic to estimate overall_progress
                 // For now, we rely on backend sending overall_progress
            }

            // Handle preview_data for live build
            if (eventData.preview_data && eventData.preview_data.type) {
              console.log("Dispatching preview_data.type:", eventData.preview_data.type, "with payload:", JSON.stringify(eventData.preview_data.data, null, 2)); // Log before dispatch
              dispatchLiveBuildDataUpdate({
                type: eventData.preview_data.type,
                payload: eventData.preview_data.data,
              });
            } else if (eventData.preview_data) {
              console.warn("Received preview_data without a type:", JSON.stringify(eventData.preview_data, null, 2));
            }
            
            // Handle general error actions from SSE
            if (eventData.action === 'error' && eventData.message) {
              setError({ message: eventData.message }); // Set task-level error
              dispatchLiveBuildDataUpdate({ type: 'TASK_FAILED_EVENT', payload: { message: eventData.message } });
            }

            // If SSE itself says generation complete (sometimes happens before polling catches it)
            if (eventData.action === 'completed' && eventData.phase === 'final_assembly' && eventData.overall_progress === 1.0) {
              console.log("SSE indicates completion, starting final check via polling.");
              // Don't immediately call onTaskComplete, let polling verify and fetch final result
              if (!isPolling) {
                 startPollingForResult();
              }
            }
          },
          (sseError) => {
            console.error('SSE Connection Error:', sseError);
            setError({ message: 'Connection to server lost. Please check your internet and try again.' });
            // Potentially stop polling or retry SSE connection based on error type
            if (progressEventSourceRef.current) {
                progressEventSourceRef.current.close();
            }
            setTimeout(setupProgressUpdates, 1000);
          },
          () => {
            // SSE stream closed by server (e.g., on task completion or explicit close)
            console.log("SSE stream closed by server. Starting polling for final result if not already.");
            if (!isPolling) {
              startPollingForResult();
            }
          },
          lastEventIdRef.current
        );
        
        progressEventSourceRef.current = eventSource;
      } catch (err) {
        console.error('Error setting up progress updates:', err);
        setError({ message: 'Could not initialize progress updates.' });
      }
    };
    
    setupProgressUpdates();
    
    // Cleanup function
    return () => {
      if (progressEventSourceRef.current) {
        progressEventSourceRef.current.close();
        progressEventSourceRef.current = null;
      }
    };
  }, [taskId, isPolling]); // Added isPolling to dependencies to avoid re-setup if polling starts due to SSE close
  
  // Poll for task status updates
  const checkTaskStatus = useCallback(async () => {
    try {
      const response = await getLearningPath(taskId);
      setTaskStatus(response.status);
      
      if (response.status === 'completed' && response.result) {
        setIsPolling(false);
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        if (progressEventSourceRef.current) {
          progressEventSourceRef.current.close();
          progressEventSourceRef.current = null;
        }
        setOverallProgress(1); // Ensure progress is 100%
        dispatchLiveBuildDataUpdate({ type: 'OVERALL_PROGRESS_UPDATE', payload: { overall_progress: 1, message: "Course generated successfully!" } });
        if (onTaskComplete) {
          onTaskComplete(response);
        }
        return response;
      } else if (response.status === 'failed') {
        setIsPolling(false);
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        if (progressEventSourceRef.current) {
          progressEventSourceRef.current.close();
          progressEventSourceRef.current = null;
        }
        const finalError = response.error || { message: 'Generation failed. Please try again.' };
        setError(finalError);
        dispatchLiveBuildDataUpdate({ type: 'TASK_FAILED_EVENT', payload: finalError });
        if (onTaskComplete) {
          onTaskComplete(response); // Pass the failed response
        }
        return response;
      }
      // If still pending or running, continue polling
      return response;
    } catch (err) {
      console.error('Error checking task status during polling:', err);
      setError({ message: err.message || 'Error fetching task status.' });
      // Potentially stop polling if error is critical (e.g. 404)
      if(err.status === 404){
        setIsPolling(false);
        if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current);
        if (progressEventSourceRef.current) progressEventSourceRef.current.close();
        setTaskStatus('failed');
        dispatchLiveBuildDataUpdate({ type: 'TASK_FAILED_EVENT', payload: { message: 'Task not found. It might have expired or been deleted.'} });
      }
      return null;
    }
  }, [taskId, onTaskComplete]);
  
  // Start polling for completion when SSE closes or if explicitly called
  const startPollingForResult = useCallback(() => {
    if (isPolling || taskStatus === 'completed' || taskStatus === 'failed') return;

    setIsPolling(true);
    console.log("Polling for task result started...");
    
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    checkTaskStatus(); // First check immediately
    pollingIntervalRef.current = setInterval(checkTaskStatus, 3000); // Then poll every 3 seconds

  }, [checkTaskStatus, isPolling, taskStatus]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (progressEventSourceRef.current) {
        progressEventSourceRef.current.close();
        progressEventSourceRef.current = null;
      }
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, []);
  
  return {
    progressMessages,
    isPolling,
    taskStatus,
    startPollingForResult, // Keep if needed by GeneratingPage for retries
    checkTaskStatus,     // Keep if needed
    liveBuildData,       // Expose liveBuildData
    overallProgress,     // Expose overallProgress for the progress bar
    error                // Expose task-level error
  };
};

export default useProgressTracking; 