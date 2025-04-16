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
   * Save the generated path to history via the API
   * @param {Object} learningPath - Learning path object to save
   * @param {Array} tags - Initial tags for the saved path
   * @param {boolean} favorite - Initial favorite status
   * @returns {Promise<{success: boolean, pathId: string | null}>} Result with success status and the new path ID
   */
  const saveToHistoryAPI = async (learningPath, tags = [], favorite = false) => {
    try {
      // Include initial favorite/tags in the creation payload if desired
      // This depends on whether the LearningPathCreate schema and backend logic support it.
      // Assuming for now it does NOT, and we need a separate update call.
      // If it DOES support it, we can pass tags/favorite here.
      const createPayload = {
        topic: learningPath.topic || 'Untitled',
        path_data: learningPath,
        source: 'generated',
        language: learningPath.language || 'en',
        // Pass initial favorite/tags ONLY if API supports it on creation:
        // favorite: favorite,
        // tags: tags,
      };

      const saveResponse = await apiService.saveToHistory(createPayload);
      const pathId = saveResponse.path_id;

      if (!pathId) {
          throw new Error("Save operation did not return a valid path ID.");
      }
      
      // If tags or favorite are set, update the entry immediately after creation
      if (tags.length > 0 || favorite) {
        console.log(`Updating entry ${pathId} with tags/favorite status.`);
        try {
            await apiService.updateHistoryEntry(pathId, { tags, favorite });
        } catch(updateError) {
            console.error(`Failed to update tags/favorite for ${pathId} after saving:`, updateError);
            // Notify user, but the path itself was saved successfully.
            showNotification('Path saved, but failed to set initial tags/favorite.', 'warning');
        }
      }
      
      showNotification('Learning path saved to history successfully!', 'success');
      return { success: true, pathId: pathId };
    } catch (error) {
      console.error('Error saving to history via API:', error);
      showNotification(`Failed to save to history: ${error.message || 'Unknown error'}`, 'error');
      return { success: false, pathId: null };
    }
  };

  /**
   * Handle save dialog confirmation
   * @returns {Promise<boolean>} Success status of the save operation
   */
  const handleSaveConfirm = async () => {
    if (generatedPath) {
      // Use the refactored API save function
      const result = await saveToHistoryAPI(generatedPath, saveDialogTags, saveDialogFavorite);
      setSaveDialogOpen(false);
      return result.success;
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