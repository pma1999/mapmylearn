import { useState } from 'react';
import * as apiService from '../../../services/api';

/**
 * Custom hook for managing history settings, tags, and favorites
 * @param {Function} showNotification - Function to display notifications
 * @returns {Object} History management state and functions
 */
const useHistoryManagement = (showNotification) => {
  // History states
  const [autoSaveToHistory, setAutoSaveToHistory] = useState(true);
  const [initialTags, setInitialTags] = useState([]);
  const [initialFavorite, setInitialFavorite] = useState(false);
  const [newTag, setNewTag] = useState('');

  // Save dialog states
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [saveDialogTags, setSaveDialogTags] = useState([]);
  const [saveDialogFavorite, setSaveDialogFavorite] = useState(false);
  const [saveDialogNewTag, setSaveDialogNewTag] = useState('');
  const [generatedPath, setGeneratedPath] = useState(null);

  /**
   * Handle adding a tag to the initial tags list
   */
  const handleAddTag = () => {
    if (newTag.trim() && !initialTags.includes(newTag.trim())) {
      setInitialTags([...initialTags, newTag.trim()]);
      setNewTag('');
    }
  };

  /**
   * Handle deleting a tag from the initial tags list
   * @param {string} tagToDelete - Tag to remove
   */
  const handleDeleteTag = (tagToDelete) => {
    setInitialTags(initialTags.filter(tag => tag !== tagToDelete));
  };

  /**
   * Handle keydown events in the tag input field
   * @param {Event} e - Keydown event
   */
  const handleTagKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  /**
   * Handle adding a tag in the save dialog
   */
  const handleAddDialogTag = () => {
    if (saveDialogNewTag.trim() && !saveDialogTags.includes(saveDialogNewTag.trim())) {
      setSaveDialogTags([...saveDialogTags, saveDialogNewTag.trim()]);
      setSaveDialogNewTag('');
    }
  };

  /**
   * Handle deleting a tag in the save dialog
   * @param {string} tagToDelete - Tag to remove
   */
  const handleDeleteDialogTag = (tagToDelete) => {
    setSaveDialogTags(saveDialogTags.filter(tag => tag !== tagToDelete));
  };

  /**
   * Handle keydown events in the dialog tag input field
   * @param {Event} e - Keydown event
   */
  const handleDialogTagKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddDialogTag();
    }
  };

  /**
   * Open the save dialog with current settings
   * @param {Object} path - Generated learning path object
   */
  const openSaveDialog = (path) => {
    setGeneratedPath(path);
    // Initialize dialog with current settings
    setSaveDialogTags([...initialTags]);
    setSaveDialogFavorite(initialFavorite);
    setSaveDialogOpen(true);
  };

  /**
   * Close the save dialog
   */
  const closeSaveDialog = () => {
    setSaveDialogOpen(false);
  };

  /**
   * Save the generated path to history
   * @param {Object} learningPath - Learning path object to save
   * @param {Array} tags - Tags to apply to the saved path
   * @param {boolean} favorite - Whether the path should be marked as favorite
   * @returns {Promise<boolean>} Success status
   */
  const saveToHistory = async (learningPath, tags = [], favorite = false) => {
    try {
      await apiService.saveToHistory(learningPath, 'generated');
      
      // If tags or favorite are set, update the entry
      if (tags.length > 0 || favorite) {
        // Note: In a real implementation, you would get the entry ID from the saveToHistory response
        // and then update it. For now, we'll just show a success message.
      }
      
      showNotification('Learning path saved to history successfully!', 'success');
      return true;
    } catch (error) {
      console.error('Error saving to history:', error);
      showNotification('Failed to save to history. Please try again.', 'error');
      return false;
    }
  };

  /**
   * Handle save dialog confirmation
   * @returns {Promise<boolean>} Success status
   */
  const handleSaveConfirm = async () => {
    if (generatedPath) {
      const success = await saveToHistory(generatedPath, saveDialogTags, saveDialogFavorite);
      setSaveDialogOpen(false);
      return success;
    }
    setSaveDialogOpen(false);
    return false;
  };

  /**
   * Save auto-save preferences to session storage for the ResultPage to use
   * @param {string} topic - Current topic being learned
   */
  const savePreferencesToSessionStorage = (topic) => {
    sessionStorage.setItem('autoSaveToHistory', autoSaveToHistory);
    sessionStorage.setItem('initialTags', JSON.stringify(initialTags));
    sessionStorage.setItem('initialFavorite', initialFavorite);
    sessionStorage.setItem('currentTopic', topic);
  };

  return {
    // Initial history settings
    autoSaveToHistory,
    setAutoSaveToHistory,
    initialTags,
    setInitialTags,
    initialFavorite,
    setInitialFavorite,
    newTag,
    setNewTag,
    handleAddTag,
    handleDeleteTag,
    handleTagKeyDown,
    
    // Save dialog
    saveDialogOpen,
    saveDialogTags,
    saveDialogFavorite,
    saveDialogNewTag,
    setSaveDialogNewTag,
    handleAddDialogTag,
    handleDeleteDialogTag,
    handleDialogTagKeyDown,
    openSaveDialog,
    closeSaveDialog,
    handleSaveConfirm,
    
    // Session storage
    savePreferencesToSessionStorage
  };
};

export default useHistoryManagement; 