import { useState, useEffect, useRef, useCallback } from 'react';
import * as apiService from '../../../services/api';

/**
 * Custom hook for tracking progress of learning path generation via SSE
 * @returns {Object} Progress state and management functions
 */
const useProgressTracking = () => {
  const [progressUpdates, setProgressUpdates] = useState([]);
  const [progressPercentage, setProgressPercentage] = useState(null);
  const [taskId, setTaskId] = useState(null);
  const eventSourceRef = useRef(null);

  /**
   * Calculate progress percentage based on update messages
   * @param {Array} updates - Array of progress update objects
   * @returns {number} Progress percentage (0-100)
   */
  const calculateProgress = useCallback((updates) => {
    if (updates.length === 0) return 10;
    
    const lastMessage = updates[updates.length - 1].message;
    
    if (lastMessage.includes("Generated") && lastMessage.includes("search queries")) {
      return 20;
    } else if (lastMessage.includes("Executed") && lastMessage.includes("web searches")) {
      return 30;
    } else if (lastMessage.includes("Created learning path with")) {
      return 40;
    } else if (lastMessage.includes("Planned") && lastMessage.includes("submodules")) {
      return 50;
    } else if (lastMessage.includes("Organized") && lastMessage.includes("submodules into")) {
      return 60;
    } else if (lastMessage.includes("Processing submodule batch")) {
      // Extract batch numbers to calculate progress
      const batchMatch = lastMessage.match(/batch (\d+) with/);
      if (batchMatch && batchMatch[1]) {
        const currentBatch = parseInt(batchMatch[1]);
        // Assuming typical path has about 10 batches (adjust based on your data)
        return 60 + Math.min(30 * (currentBatch / 10), 30);
      }
      return 70;
    } else if (lastMessage.includes("Completed batch")) {
      return 80;
    } else if (lastMessage.includes("Finalized")) {
      return 95;
    }
    
    // Default increment for any progress
    const baseProgress = Math.min(5 + updates.length * 2, 90);
    return baseProgress;
  }, []);

  /**
   * Reset progress tracking state
   */
  const resetProgress = useCallback(() => {
    setProgressUpdates([]);
    setProgressPercentage(0);
    setTaskId(null);
    
    // Close any existing EventSource connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  /**
   * Connect to the SSE endpoint for progress updates
   * @param {string} id - Task ID to track progress for
   */
  const connectToProgressUpdates = useCallback((id) => {
    // Close any existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    
    // Save the task ID
    setTaskId(id);
    
    // Reset progress state
    setProgressUpdates([]);
    setProgressPercentage(10); // Start at 10%
    
    // Use the API service to connect to progress updates
    const progressUpdatesService = apiService.getProgressUpdates(
      id,
      (data) => {
        setProgressUpdates(prevUpdates => {
          // Only add if it's not a duplicate message
          if (prevUpdates.length === 0 || prevUpdates[prevUpdates.length-1].message !== data.message) {
            const newUpdates = [...prevUpdates, data];
            // Update progress percentage
            setProgressPercentage(calculateProgress(newUpdates));
            return newUpdates;
          }
          return prevUpdates;
        });
      },
      (error) => {
        console.error('EventSource error:', error);
      }
    );
    
    eventSourceRef.current = progressUpdatesService;
  }, [calculateProgress]);

  // Clean up the EventSource when component unmounts
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, []);

  return {
    progressUpdates,
    progressPercentage,
    taskId,
    connectToProgressUpdates,
    setTaskId,
    resetProgress
  };
};

export default useProgressTracking; 