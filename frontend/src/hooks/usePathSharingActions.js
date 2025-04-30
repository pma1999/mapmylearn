import { useCallback } from 'react';
import * as api from '../services/api';

/**
 * Hook providing actions related to learning path sharing.
 * 
 * @param {Function} showNotification - Function to display notifications.
 * @param {Function} onComplete - Callback function to execute after an action completes successfully (e.g., refresh data).
 * @returns {Object} Object containing handleTogglePublic and handleCopyShareLink functions.
 */
const usePathSharingActions = (showNotification, onComplete) => {

  const handleTogglePublic = useCallback(async (pathId, newIsPublic) => {
    const action = newIsPublic ? 'public' : 'private';
    const actionVerb = newIsPublic ? 'making' : 'making';
    
    try {
      showNotification(`${actionVerb.charAt(0).toUpperCase() + actionVerb.slice(1)} path ${action}...`, 'info');
      const updatedPath = await api.updateLearningPathPublicity(pathId, newIsPublic);
      showNotification(`Learning path successfully made ${action}.`, 'success');
      if (onComplete) {
        onComplete(updatedPath); // Pass updated path data to callback if needed
      }
    } catch (error) {
      console.error(`Error ${actionVerb} path ${action}:`, error);
      showNotification(`Error ${actionVerb} path ${action}: ${error.message || 'Unknown error'}`, 'error');
    }
  }, [showNotification, onComplete]);

  const handleCopyShareLink = useCallback(async (shareId) => {
    if (!shareId) {
      showNotification('Cannot copy link: Share ID is missing.', 'error');
      return;
    }
    const shareUrl = `${window.location.origin}/public/${shareId}`;
    try {
      await navigator.clipboard.writeText(shareUrl);
      showNotification('Public share link copied to clipboard!', 'success');
    } catch (err) {
      console.error('Failed to copy share link: ', err);
      showNotification('Failed to copy link. Please try again or copy manually.', 'error');
    }
  }, [showNotification]);

  return {
    handleTogglePublic,
    handleCopyShareLink,
  };
};

export default usePathSharingActions; 