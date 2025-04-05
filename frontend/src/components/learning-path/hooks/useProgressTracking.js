import { useState, useEffect, useRef } from 'react';
import { getProgressUpdates, getLearningPath } from '../../../services/api';

/**
 * Custom hook for tracking progress of learning path generation
 * 
 * @param {string} taskId - ID of the task being generated
 * @returns {Object} Progress tracking state and functions
 */
const useProgressTracking = (taskId) => {
  const [progressMessages, setProgressMessages] = useState([]);
  const [isPolling, setIsPolling] = useState(false);
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
  
  // Start polling for completion
  const startPollingForResult = () => {
    // Clear any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    
    setIsPolling(true);
    
    // Poll every 3 seconds
    pollingIntervalRef.current = setInterval(async () => {
      try {
        const response = await getLearningPath(taskId);
        
        if (response.status === 'completed' || response.status === 'failed') {
          // We have a final state - stop polling
          setIsPolling(false);
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
          
          // Close SSE connection
          if (progressEventSourceRef.current) {
            progressEventSourceRef.current.close();
            progressEventSourceRef.current = null;
          }
          
          return response;
        }
      } catch (err) {
        console.error('Error polling for learning path result:', err);
        // Don't stop polling on error - keep trying
      }
    }, 3000);
  };
  
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
    startPollingForResult
  };
};

export default useProgressTracking; 