import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import * as api from '../../../services/api';

/**
 * Custom hook for managing history entry actions
 * @param {Function} showNotification - Function to show notifications
 * @param {Function} refreshEntries - Function to refresh entries after actions
 * @returns {Object} Actions and related states for history management
 */
const useHistoryActions = (showNotification, refreshEntries) => {
  const navigate = useNavigate();
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [clearHistoryDialog, setClearHistoryDialog] = useState(false);
  
  /**
   * View a learning path by navigating to its detail page
   * @param {string} entryId - ID of the entry to view
   */
  const handleViewLearningPath = (entryId) => {
    try {
      navigate(`/history/${entryId}`);
    } catch (error) {
      console.error('Error navigating to learning path:', error);
      showNotification('Error loading learning path: ' + (error.message || 'Unknown error'), 'error');
    }
  };
  
  /**
   * Delete a learning path
   * @param {string} entryId - ID of the entry to delete
   */
  const handleDeleteLearningPath = async (entryId) => {
    try {
      await api.deleteHistoryEntry(entryId);
      showNotification('Learning path deleted successfully', 'success');
      refreshEntries();
    } catch (error) {
      showNotification('Error deleting learning path: ' + (error.message || 'Unknown error'), 'error');
    }
  };
  
  /**
   * Toggle favorite status of a learning path
   * @param {string} entryId - ID of the entry to update
   * @param {boolean} favoriteStatus - New favorite status
   */
  const handleToggleFavorite = async (entryId, favoriteStatus) => {
    try {
      await api.updateHistoryEntry(entryId, { favorite: favoriteStatus });
      showNotification(
        favoriteStatus ? 'Added to favorites' : 'Removed from favorites',
        'success'
      );
      refreshEntries();
    } catch (error) {
      showNotification('Error updating favorite status: ' + (error.message || 'Unknown error'), 'error');
    }
  };
  
  /**
   * Update tags for a learning path
   * @param {string} entryId - ID of the entry to update
   * @param {Array<string>} tags - New tags array
   */
  const handleUpdateTags = async (entryId, tags) => {
    try {
      await api.updateHistoryEntry(entryId, { tags });
      showNotification('Tags updated successfully', 'success');
      refreshEntries();
    } catch (error) {
      showNotification('Error updating tags: ' + (error.message || 'Unknown error'), 'error');
    }
  };
  
  /**
   * Export a single learning path as JSON file
   * @param {string} entryId - ID of the entry to export
   */
  const handleExportLearningPath = async (entryId) => {
    try {
      const response = await api.getHistoryEntry(entryId);
      const learningPath = response.entry.path_data;
      
      // Create a JSON file and trigger download
      const json = JSON.stringify(learningPath, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `learning_path_${learningPath.topic.replace(/\s+/g, '_')}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      showNotification('Learning path exported successfully', 'success');
    } catch (error) {
      showNotification('Error exporting learning path: ' + (error.message || 'Unknown error'), 'error');
    }
  };
  
  /**
   * Export all history entries as a single JSON file
   */
  const handleExportAllHistory = async () => {
    try {
      const response = await api.exportHistory();
      
      // Create a JSON file and trigger download
      const json = JSON.stringify(response, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const date = new Date().toISOString().replace(/:/g, '-').split('.')[0];
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `learning_path_history_${date}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      showNotification('History exported successfully', 'success');
    } catch (error) {
      showNotification('Error exporting history: ' + (error.message || 'Unknown error'), 'error');
    }
  };
  
  /**
   * Import a learning path from JSON data
   * @param {string} jsonData - JSON string to import
   */
  const handleImportLearningPath = async (jsonData) => {
    try {
      const response = await api.importLearningPath(jsonData);
      showNotification(`Learning path "${response.topic}" imported successfully`, 'success');
      refreshEntries();
      return true;
    } catch (error) {
      showNotification('Error importing learning path: ' + (error.message || 'Unknown error'), 'error');
      throw error; // Re-throw so the dialog can handle it
    }
  };
  
  /**
   * Clear all history entries
   */
  const handleClearHistory = async () => {
    try {
      await api.clearHistory();
      showNotification('History cleared successfully', 'success');
      refreshEntries();
      setClearHistoryDialog(false);
    } catch (error) {
      showNotification('Error clearing history: ' + (error.message || 'Unknown error'), 'error');
    }
  };

  return {
    // Dialog states
    importDialogOpen,
    setImportDialogOpen,
    clearHistoryDialog,
    setClearHistoryDialog,
    
    // Actions
    handleViewLearningPath,
    handleDeleteLearningPath,
    handleToggleFavorite,
    handleUpdateTags,
    handleExportLearningPath,
    handleExportAllHistory,
    handleImportLearningPath,
    handleClearHistory
  };
};

export default useHistoryActions; 