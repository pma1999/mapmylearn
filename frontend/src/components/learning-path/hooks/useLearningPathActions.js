import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router';
import { 
  saveToHistory, 
  updateHistoryEntry, 
  downloadLearningPathPDF,
  getHistoryEntry
} from '../../../services/api';

/**
 * Custom hook for managing actions related to a learning path
 * 
 * @param {Object} learningPath - The learning path data
 * @param {boolean} isFromHistory - Whether the learning path is from history
 * @param {boolean} savedToHistory - Whether the learning path is saved to history
 * @param {string} entryId - ID of the history entry (if from history)
 * @param {string} taskId - ID of the task (if from generation)
 * @param {string} temporaryPathId - Newly added temporary ID (if applicable)
 * @returns {Object} Actions and states for learning path management
 */
const useLearningPathActions = (
  learningPath, 
  isFromHistory, 
  savedToHistory, 
  entryId, 
  taskId,
  temporaryPathId
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
   * Downloads the learning path as JSON
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
      showNotification('Failed to download learning path', 'error');
    }
  };

  /**
   * Downloads the learning path as PDF
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
      showNotification('Please save the learning path to history first', 'error');
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
   * Navigates to generator page to create a new learning path
   */
  const handleNewLearningPathClick = () => {
    navigate('/generator');
  };
  
  /**
   * Opens the save dialog
   */
  const handleSaveToHistory = () => {
    if (savedToHistory) {
      showNotification('Learning path is already saved.', 'info');
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
   * Saves the learning path to history
   */
  const handleSaveConfirm = async () => {
    if (!learningPath) {
      showNotification('Learning path data is not available to save.', 'error');
      return null;
    }
    
    if (savedToHistory) {
       showNotification('Learning path is already saved.', 'info');
       return null; // Or return indicating already saved
    }

    try {
      // Prepare payload for the saveToHistory API endpoint
      const payload = {
        path_data: learningPath,         // The main learning path content
        topic: learningPath.topic || 'Untitled Learning Path', // Ensure topic exists
        favorite: favorite,              // From dialog state
        tags: tags,                      // From dialog state
        source_task_id: taskId,          // Include the original task ID for reference
      };

      // Include temporaryPathId if this path was temporary before saving
      if (temporaryPathId && !isFromHistory) { // Only add if it was temporary
         payload.temporary_path_id = temporaryPathId;
         console.log('Saving path with temporary_path_id:', temporaryPathId);
      }

      showNotification('Saving learning path...', 'info');
      
      // Call the API to save the learning path, passing the original taskId
      const response = await saveToHistory(learningPath, 'generated', taskId); 
      
      // Handle response - update state, show success/error
      if (response && response.path_id) {
        showNotification('Learning path saved successfully!', 'success');
        setSaveDialogOpen(false);
        return {
          savedToHistory: true,
          path_id: response.path_id // <<<< Use path_id from response
        };
      }

    } catch (error) {
      console.error("Error saving learning path:", error);
      showNotification(`Error saving learning path: ${error.message || 'Unknown error'}`, 'error');
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