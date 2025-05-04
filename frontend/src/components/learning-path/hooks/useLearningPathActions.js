import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router';
import { 
  saveToHistory, 
  updateHistoryEntry, 
  downloadLearningPathPDF,
  getHistoryEntry
} from '../../../services/api';

/**
 * Custom hook for managing actions related to a course
 * 
 * @param {Object} learningPath - The course data
 * @param {boolean} isFromHistory - Whether the course is from history
 * @param {boolean} detailsHaveBeenSet - Whether tags/favorites have been set for the path
 * @param {string} entryId - ID of the history entry (if from history or after save)
 * @param {string} taskId - ID of the task (if from generation)
 * @param {string} temporaryPathId - Newly added temporary ID (if applicable)
 * @param {Function} onSaveSuccess - Callback function invoked after successful save
 * @returns {Object} Actions and states for course management
 */
const useLearningPathActions = (
  learningPath, 
  isFromHistory, 
  detailsHaveBeenSet,
  entryId, 
  taskId,
  temporaryPathId,
  onSaveSuccess
) => {
  const navigate = useNavigate();
  
  // States
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [tags, setTags] = useState([]);
  const [newTag, setNewTag] = useState('');
  const [favorite, setFavorite] = useState(false);
  const [notification, setNotification] = useState({ 
    open: false, 
    message: '', 
    severity: 'info' 
  });

  /**
   * Shows a notification message
   * @param {string} message - Message to display
   * @param {string} severity - Severity level (success, error, warning, info)
   */
  const showNotification = (message, severity = 'info') => {
    setNotification({
      open: true,
      message,
      severity
    });
  };
  
  /**
   * Closes the notification
   */
  const handleNotificationClose = () => {
    setNotification({ ...notification, open: false });
  };

  /**
   * Downloads the course as JSON
   */
  const handleDownloadJSON = () => {
    if (!learningPath) return;
    
    try {
      const json = JSON.stringify(learningPath, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      const fileName = learningPath.topic 
        ? `learning_path_${learningPath.topic.replace(/\\s+/g, '_').substring(0, 30)}.json`
        : 'learning_path.json';
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      showNotification('Learning path downloaded successfully', 'success');
    } catch (err) {
      console.error('Error downloading JSON:', err);
      showNotification('Failed to download course', 'error');
    }
  };

  /**
   * Downloads the course as PDF
   */
  const handleDownloadPDF = async () => {
    if (!learningPath) return;

    // Ensure we have the correct ID. Priority: history entryId
    // The entryId prop passed to this hook IS the correct one after saving
    const targetId = entryId; 

    if (!targetId) {
      // This should ideally not happen if the button is correctly disabled
      // when !isPersisted, but as a safeguard:
      console.error("PDF Download Error: Cannot download PDF without a valid History Entry ID.");
      showNotification('Please save the course to history first', 'error');
      return { savedToHistory: false }; 
    }

    try {
      // Show loading notification
      showNotification('Generating PDF...', 'info');

      // Download the PDF using the history entry ID
      const pdfBlob = await downloadLearningPathPDF(targetId);
      
      // Create a download link
      const url = URL.createObjectURL(pdfBlob);
      const a = document.createElement('a');
      a.href = url;
      const fileName = learningPath.topic 
        ? `learning_path_${learningPath.topic.replace(/\\s+/g, '_').substring(0, 30)}.pdf`
        : 'learning_path.pdf';
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      showNotification('PDF downloaded successfully', 'success');
      return { savedToHistory: true };
    } catch (err) {
      console.error('Error downloading PDF:', err);
      showNotification('Failed to download PDF', 'error');
      return { savedToHistory: false };
    }
  };

  /**
   * Navigates to home page
   */
  const handleHomeClick = () => {
    navigate('/');
  };

  /**
   * Navigates to generator page to create a new course
   */
  const handleNewLearningPathClick = () => {
    navigate('/generator');
  };
  
  /**
   * Opens the save dialog
   */
  const handleSaveToHistory = () => {
    if (detailsHaveBeenSet) {
      showNotification('Learning path details already set.', 'info');
      return;
    }
    // Reset dialog state
    setTags([]);
    setNewTag('');
    setFavorite(false);
    setSaveDialogOpen(true);
  };
  
  /**
   * Closes the save dialog
   */
  const handleSaveDialogClose = () => {
    setSaveDialogOpen(false);
  };
  
  /**
   * Saves the course to history
   */
  const handleSaveConfirm = async () => {
    if (!learningPath) {
      showNotification('Learning path data is not available to save.', 'error');
      return null;
    }
    
    if (detailsHaveBeenSet) {
       showNotification('Learning path details already set.', 'info');
       return null; // Or return indicating already saved
    }

    try {
      showNotification('Saving details...', 'info');
      let response;
      let successEntryId = entryId; // Assume existing entryId for updates

      if (isFromHistory) {
        // --- Update existing history entry --- 
        console.log(`Updating history entry ${entryId} with details...`);
        const updatePayload = { 
          favorite: favorite, 
          tags: tags 
        };
        response = await updateHistoryEntry(entryId, updatePayload);
        // Assuming updateHistoryEntry returns success confirmation, maybe { success: true }
        // If it returns the updated entry, adjust accordingly.
      } else {
        // --- Save new entry to history --- 
        console.log('Saving new entry to history...');
        const payload = {
          path_data: learningPath,        
          topic: learningPath.topic || 'Untitled Learning Path', 
          favorite: favorite,             
          tags: tags,                     
          source_task_id: taskId,         
        };
        if (temporaryPathId) { 
           payload.temporary_path_id = temporaryPathId;
           console.log('Saving path with temporary_path_id:', temporaryPathId);
        }
        response = await saveToHistory(learningPath, 'generated', taskId, payload); // Pass full payload now
        // Keep original logic: saveToHistory returns { path_id: new_id }
        if (response && response.path_id) {
           successEntryId = response.path_id; // Update entryId if new one was created
        }
      }
      
      // Handle response - update state, show success/error
      // Simplify response check: Check if response indicates success (might need adjustment based on actual API response)
      if (response) { // Basic check, refine if API gives clearer success/error
        showNotification('Learning path details saved successfully!', 'success');
        setSaveDialogOpen(false);
        
        // Invoke the callback passed from the parent component with the relevant entryId
        if (onSaveSuccess) {
          onSaveSuccess({ entryId: successEntryId });
        }

        // Return success and the relevant entry ID
        return { success: true, entryId: successEntryId }; 
      } else {
         // Throw an error if the response structure wasn't as expected
         throw new Error('API response did not indicate success.');
      }

    } catch (error) {
      console.error("Error saving course:", error);
      showNotification(`Error saving course: ${error.message || 'Unknown error'}`, 'error');
      setSaveDialogOpen(false); // Close dialog on error too
      return null;
    }
  };
  
  // Tag management functions
  const handleAddTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()]);
      setNewTag('');
    }
  };
  
  const handleDeleteTag = (tagToDelete) => {
    setTags(tags.filter(tag => tag !== tagToDelete));
  };
  
  const handleTagKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  return {
    // States
    saveDialogOpen,
    setSaveDialogOpen,
    tags,
    setTags,
    newTag,
    setNewTag,
    favorite,
    setFavorite,
    notification,
    
    // Actions
    handleDownloadJSON,
    handleDownloadPDF,
    handleHomeClick,
    handleNewLearningPathClick,
    handleSaveToHistory,
    handleSaveDialogClose,
    handleSaveConfirm,
    handleAddTag,
    handleDeleteTag,
    handleTagKeyDown,
    handleNotificationClose,
    showNotification
  };
};

export default useLearningPathActions; 