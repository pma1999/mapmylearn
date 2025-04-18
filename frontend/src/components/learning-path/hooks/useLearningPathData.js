import { useState, useEffect, useCallback } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { getLearningPath, getHistoryEntry } from '../../../services/api';

/**
 * Custom hook to load learning path data from different sources
 * Abstracts the source of the data (generated or history)
 * 
 * @param {string} source - Optional source override ('history' or null)
 * @returns {Object} { learningPath, loading, error, isFromHistory, savedToHistory, refreshData, temporaryPathId }
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
  const [temporaryPathId, setTemporaryPathId] = useState(null);

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
      setTemporaryPathId(null);
      
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
          setLoading(false);
        } else {
          // Load from task API
          const response = await getLearningPath(taskId);
          
          if (response.status === 'completed' && response.result) {
            setData(response.result);
            const tempId = crypto.randomUUID();
            setTemporaryPathId(tempId);
            setSavedToHistory(false);
            setIsFromHistory(false);
            setLoading(false);
          } else if (response.status === 'failed') {
            setError(response.error?.message || 'Learning path generation failed');
            setLoading(false);
          } else if (response.status === 'running' || response.status === 'pending' || response.status === 'in_progress') {
            console.log('Task is still running with status:', response.status);
          }
        }
      } catch (err) {
        console.error('Error loading learning path:', err);
        setError(err.message || 'Error loading learning path. Please try again.');
        setLoading(false);
      }
    };
    
    if (shouldLoadFromHistory ? entryId : taskId) {
      loadData();
    } else {
      setLoading(false);
      setError("Required ID (taskId or entryId) is missing.");
    }
  }, [taskId, entryId, shouldLoadFromHistory, refreshTrigger]);

  return {
    learningPath: data,
    loading,
    error,
    isFromHistory,
    savedToHistory,
    refreshData,
    temporaryPathId
  };
};

export default useLearningPathData; 