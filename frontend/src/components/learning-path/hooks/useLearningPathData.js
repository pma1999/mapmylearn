import { useState, useEffect, useCallback } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { getLearningPath, getHistoryEntry } from '../../../services/api';

/**
 * Custom hook to load learning path data from different sources
 * Abstracts the source of the data (generated or history)
 * 
 * @param {string} source - Optional source override ('history' or null)
 * @returns {Object} { learningPath, loading, error, isFromHistory, savedToHistory, refreshData }
 */
const useLearningPathData = (source = null) => {
  const { taskId, entryId } = useParams();
  const location = useLocation();
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isFromHistory, setIsFromHistory] = useState(false);
  const [savedToHistory, setSavedToHistory] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Determine if data should be loaded from history
  const shouldLoadFromHistory = 
    source === 'history' || 
    location.pathname.startsWith('/history/') || 
    !!entryId;

  // Function to manually refresh data
  const refreshData = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, []);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        if (shouldLoadFromHistory) {
          // Load from history
          const historyResponse = await getHistoryEntry(entryId);
          
          if (!historyResponse || !historyResponse.entry) {
            throw new Error('Learning path not found in history. It may have been deleted or not properly migrated.');
          }
          
          const pathData = historyResponse.entry.path_data;
          setData(pathData);
          setIsFromHistory(true);
          setSavedToHistory(true);
          setLoading(false); // Set loading to false only when data is loaded
        } else {
          // Load from task API
          const response = await getLearningPath(taskId);
          
          if (response.status === 'completed' && response.result) {
            setData(response.result);
            setSavedToHistory(false);
            setIsFromHistory(false);
            setLoading(false); // Set loading to false only when data is loaded
          } else if (response.status === 'failed') {
            setError(response.error?.message || 'Learning path generation failed');
            setLoading(false); // Set loading to false on error
          } else if (response.status === 'running' || response.status === 'pending' || response.status === 'in_progress') {
            // Keep loading state true for running tasks
            // Don't update data yet - the progress tracking will handle updates
            console.log('Task is still running with status:', response.status);
            // Important: DON'T set loading to false here
          }
        }
      } catch (err) {
        console.error('Error loading learning path:', err);
        setError(err.message || 'Error loading learning path. Please try again.');
        setLoading(false); // Set loading to false on error
      }
    };
    
    if (shouldLoadFromHistory ? entryId : taskId) {
      loadData();
    }
  }, [taskId, entryId, shouldLoadFromHistory, refreshTrigger]);

  return {
    learningPath: data,
    loading,
    error,
    isFromHistory,
    savedToHistory,
    refreshData
  };
};

export default useLearningPathData; 