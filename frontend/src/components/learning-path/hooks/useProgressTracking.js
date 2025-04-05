import { useState, useEffect, useRef, useCallback } from 'react';
import { getProgressUpdates, getLearningPath } from '../../../services/api';

/**
 * Custom hook for tracking progress of learning path generation
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
  
  // Setup progress updates via Server-Sent Events
  useEffect(() => {
    if (!taskId) return;
    
    const setupProgressUpdates = () => {
      try {
        const eventSource = getProgressUpdates(
          taskId,
          (data) => {
            if (data.message) {
              setProgressMessages((prev) => [...prev, data]);
            }
          },
          (error) => {
            console.error('SSE Error:', error);
          },
          () => {
            // On complete - will trigger the polling to fetch final result
          }
        );
        
        progressEventSourceRef.current = eventSource;
      } catch (err) {
        console.error('Error setting up progress updates:', err);
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
  }, [taskId]);
  
  // Poll for task status updates
  const checkTaskStatus = useCallback(async () => {
    try {
      const response = await getLearningPath(taskId);
      setTaskStatus(response.status);
      
      if (response.status === 'completed' && response.result) {
        // Task completed successfully with a result
        // Close polling and SSE connection
        setIsPolling(false);
        
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        
        if (progressEventSourceRef.current) {
          progressEventSourceRef.current.close();
          progressEventSourceRef.current = null;
        }
        
        // Notify parent component that task is complete
        if (onTaskComplete) {
          onTaskComplete(response);
        }
        
        return response;
      } else if (response.status === 'failed') {
        // Task failed
        setIsPolling(false);
        
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        
        if (progressEventSourceRef.current) {
          progressEventSourceRef.current.close();
          progressEventSourceRef.current = null;
        }
        
        // Notify parent component of failure
        if (onTaskComplete) {
          onTaskComplete(response);
        }
        
        return response;
      }
      
      return response;
    } catch (err) {
      console.error('Error checking task status:', err);
      // Don't stop polling on error - keep trying
      return null;
    }
  }, [taskId, onTaskComplete]);
  
  // Start polling for completion
  const startPollingForResult = useCallback(() => {
    // Clear any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    
    setIsPolling(true);
    
    // First check immediately
    checkTaskStatus();
    
    // Then poll every 3 seconds
    pollingIntervalRef.current = setInterval(checkTaskStatus, 3000);
  }, [checkTaskStatus]);
  
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
    startPollingForResult,
    checkTaskStatus
  };
};

export default useProgressTracking; 