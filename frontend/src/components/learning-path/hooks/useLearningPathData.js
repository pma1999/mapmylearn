import { useState, useEffect } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { getLearningPath, getHistoryEntry } from '../../../services/api';

/**
 * Custom hook to load learning path data from different sources
 * Abstracts the source of the data (generated or history)
 * 
 * @param {string} source - Optional source override ('history' or null)
 * @returns {Object} { learningPath, loading, error, isFromHistory, savedToHistory }
 */
const useLearningPathData = (source = null) => {
  const { taskId, entryId } = useParams();
  const location = useLocation();
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isFromHistory, setIsFromHistory] = useState(false);
  const [savedToHistory, setSavedToHistory] = useState(false);

  // Determine if data should be loaded from history
  const shouldLoadFromHistory = 
    source === 'history' || 
    location.pathname.startsWith('/history/') || 
    !!entryId;

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
        } else {
          // Load from task API
          const response = await getLearningPath(taskId);
          
          if (response.status === 'completed' && response.result) {
            setData(response.result);
            setSavedToHistory(false);
            setIsFromHistory(false);
          } else if (response.status === 'failed') {
            setError(response.error?.message || 'Learning path generation failed');
          } else {
            // For pending/running tasks, don't update data yet
            // The calling component should handle progress updates
            return;
          }
        }
      } catch (err) {
        console.error('Error loading learning path:', err);
        setError(err.message || 'Error loading learning path. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    
    if (shouldLoadFromHistory ? entryId : taskId) {
      loadData();
    }
  }, [taskId, entryId, shouldLoadFromHistory]);

  return {
    learningPath: data,
    loading,
    error,
    isFromHistory,
    savedToHistory
  };
};

export default useLearningPathData; 