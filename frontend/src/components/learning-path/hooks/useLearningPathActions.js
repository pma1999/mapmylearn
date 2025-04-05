import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  saveToHistory, 
  updateHistoryEntry, 
  downloadLearningPathPDF 
} from '../../../services/api';

/**
 * Custom hook for managing actions related to a learning path
 * 
 * @param {Object} learningPath - The learning path data
 * @param {boolean} isFromHistory - Whether the learning path is from history
 * @param {boolean} savedToHistory - Whether the learning path is saved to history
 * @param {string} entryId - ID of the history entry (if from history)
 * @param {string} taskId - ID of the task (if from generation)
 * @returns {Object} Actions and states for learning path management
 */
const useLearningPathActions = (
  learningPath, 
  isFromHistory, 
  savedToHistory, 
  entryId, 
  taskId
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
    severity: 'success' 
  });

  /**
   * Shows a notification message
   * @param {string} message - Message to display
   * @param {string} severity - Severity level (success, error, warning, info)
   */
  const showNotification = (message, severity = 'success') => {
    setNotification({
      open: true,
      message,
      severity
    });
  };
  
  /**
   * Closes the notification
   */
  const handleNotificationClose = (event, reason) => {
    if (reason === 'clickaway') return;
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
      a.download = `learning_path_${learningPath.topic.replace(/\\s+/g, '_').substring(0, 30)}.json`;
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
    
    try {
      // Show loading notification
      showNotification('Generating PDF...', 'info');
      
      // Get the entry ID from either the URL params or from the saved history entry
      const id = isFromHistory ? entryId : taskId;
      
      // If the path is not saved to history yet, save it first
      let targetId = id;
      if (!isFromHistory && !savedToHistory) {
        try {
          const result = await saveToHistory(learningPath, 'generated');
          if (result.success) {
            targetId = result.entry_id;
            // Signal that the learning path is now saved
            return {
              savedToHistory: true,
              entryId: result.entry_id
            };
          }
        } catch (error) {
          console.error('Error saving to history before PDF download:', error);
          showNotification('Please save the learning path to history first', 'error');
          return { savedToHistory: false };
        }
      }
      
      // Download the PDF
      const pdfBlob = await downloadLearningPathPDF(targetId);
      
      // Create a download link
      const url = URL.createObjectURL(pdfBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `learning_path_${learningPath.topic.replace(/\\s+/g, '_').substring(0, 30)}.pdf`;
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
      showNotification('This learning path is already saved to history', 'info');
      return;
    }
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
    if (!learningPath) return;
    
    try {
      const result = await saveToHistory(learningPath, 'generated');
      
      if (result.success) {
        showNotification('Learning path saved to history successfully', 'success');
        
        // If tags or favorite are set, update the entry
        if (tags.length > 0 || favorite) {
          try {
            await updateHistoryEntry(result.entry_id, { tags, favorite });
          } catch (error) {
            console.error('Error updating history entry:', error);
          }
        }
        
        // Signal that the learning path is now saved
        setSaveDialogOpen(false);
        return {
          savedToHistory: true,
          entryId: result.entry_id
        };
      } else {
        showNotification('Failed to save learning path to history', 'error');
        setSaveDialogOpen(false);
        return { savedToHistory: false };
      }
    } catch (error) {
      console.error('Error saving to history:', error);
      showNotification('Failed to save learning path to history', 'error');
      setSaveDialogOpen(false);
      return { savedToHistory: false };
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