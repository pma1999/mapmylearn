import React, { useEffect, useState, useCallback } from 'react';
import PropTypes from 'prop-types';
import { useParams } from 'react-router';
import { Container, Snackbar, Alert, AlertTitle, useMediaQuery, useTheme, Box, Typography, Paper, Divider, IconButton } from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { helpTexts } from '../../../constants/helpTexts'; // Corrected path

// Custom hooks
import useLearningPathData from '../hooks/useLearningPathData';
import useLearningPathActions from '../hooks/useLearningPathActions';

// View components
import LearningPathHeader from './LearningPathHeader';
import ModuleSection from './ModuleSection';
import LoadingState from './LoadingState';
import ErrorState from './ErrorState';
import SaveDialog from './SaveDialog';

// Import the new ResourcesSection component instead of PlaceholderContent
import ResourcesSection from '../../shared/ResourcesSection';
import MenuBookIcon from '@mui/icons-material/MenuBook';

/**
 * Main component for viewing a learning path
 * This is a shared component used both by ResultPage and HistoryPage/detail view
 * 
 * @param {Object} props Component props
 * @param {string} props.source Source of the learning path (history or null)
 * @returns {JSX.Element} Learning path view component
 */
const LearningPathView = ({ source }) => {
  const { taskId, entryId } = useParams();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [showFirstViewAlert, setShowFirstViewAlert] = useState(false);
  
  // Load learning path data using the hook
  const {
    learningPath, 
    loading,      
    error,        
    isFromHistory,
    initialDetailsWereSet, // <-- Destructure new value
    persistentPathId, 
    temporaryPathId,
    progressMessages, 
    isReconnecting, 
    retryAttempt,   
    refreshData 
  } = useLearningPathData(source); 
  
  // Local state for tracking if details (tags/favorites) have been set via dialog
  // Initialize based on whether the loaded path (if from history) already had details
  const [localDetailsHaveBeenSet, setLocalDetailsHaveBeenSet] = useState(false);
  const [localEntryId, setLocalEntryId] = useState(null);

  // Effect to initialize local state once loading is done and we have initial data
  useEffect(() => {
    if (!loading) {
        setLocalDetailsHaveBeenSet(initialDetailsWereSet || false);
        // Also set localEntryId if we loaded from history and have a persistentId
        if (isFromHistory && persistentPathId) {
            setLocalEntryId(persistentPathId);
        } else {
            // Reset if not loading from history or no persistentId yet
            setLocalEntryId(null);
        }
    }
  }, [loading, initialDetailsWereSet, isFromHistory, persistentPathId]);
  
  // Derived states based on hook values and local actions
  const isPdfReady = !loading && !!persistentPathId; // Determine if PDF can be downloaded
  const isPersisted = isFromHistory || localDetailsHaveBeenSet || isPdfReady; // Determine if path is generally considered persistent (for other UI logic?)
  const isTemporaryPath = !loading && !!temporaryPathId && !persistentPathId; // Path has temporary ID but not yet persistent one
  
  // Determine the correct pathId to use for component interactions
  let derivedPathId = null;
  const currentEntryId = localEntryId || entryId || persistentPathId; // Use persistentId as fallback
  
  if (!loading && learningPath) { 
    if (isTemporaryPath) {
      derivedPathId = temporaryPathId;
    } else {
      derivedPathId = currentEntryId; // Use the combined entryId / persistentId
    }
    // Additional safety checks (if derivedPathId is still null, log warning)
    if (!derivedPathId) {
      console.warn('Could not reliably determine pathId for LearningPathView interactions.');
    }
  }
  
  // Extract the actual path data object, handling both history and generation cases
  // Checks if the newer nested structure (learningPath.path_data) exists when loading from history.
  const actualPathData = isFromHistory
    ? (learningPath?.path_data ? learningPath.path_data : learningPath) // Handle both old/new history structures
    : learningPath; // Use learningPath directly for generation

  // Callback for when save is confirmed in the action hook
  const handleSaveSuccess = useCallback((result) => {
    if (result?.entryId) {
      setLocalDetailsHaveBeenSet(true);
      setLocalEntryId(result.entryId);
    }
  }, []); // Dependencies: none, relies on setters

  // Setup actions for the learning path
  const {
    saveDialogOpen,
    setSaveDialogOpen,
    tags,
    setTags,
    newTag,
    setNewTag,
    favorite,
    setFavorite,
    notification,
    handleDownloadJSON,
    handleDownloadPDF,
    handleHomeClick,
    handleNewLearningPathClick,
    handleSaveToHistory,
    handleSaveDialogClose,
    handleSaveConfirm, // Keep this if SaveDialog calls it directly
    handleAddTag,
    handleDeleteTag,
    handleTagKeyDown,
    handleNotificationClose,
    showNotification // Make showNotification available if needed directly
  } = useLearningPathActions(
    actualPathData, 
    isFromHistory,
    localDetailsHaveBeenSet, // Pass renamed state
    currentEntryId, 
    taskId,         
    temporaryPathId, 
    handleSaveSuccess // Pass the callback
  );
  
  // Adjust action handlers if they directly used `learningPath` expecting the wrong structure
  // e.g., handleDownloadJSON likely needs `actualPathData` now
  const handleDownloadJSONAdjusted = () => {
      if (!actualPathData) return;
      try {
          const json = JSON.stringify(actualPathData, null, 2);
          const blob = new Blob([json], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          const fileName = actualPathData.topic
              ? `learning_path_${actualPathData.topic.replace(/\s+/g, '_').substring(0, 30)}.json`
              : 'learning_path.json';
          a.download = fileName;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
          // Use showNotification from useLearningPathActions if available
          if (showNotification) {
              showNotification('Learning path downloaded successfully', 'success');
          } else {
              // Fallback or handle differently if showNotification isn't returned
              console.log('Learning path downloaded successfully');
          }
      } catch (err) {
          console.error('Error downloading JSON:', err);
          if (showNotification) {
              showNotification('Failed to download learning path', 'error');
          } else {
              console.error('Failed to download learning path');
          }
      }
  };

  // Update PDF download handler: remove incorrect state update
  const handleDownloadPDFWithUpdate = async () => {
    // Call original function from hook
    await handleDownloadPDF(); // Removed state updates based on result
    // No need to set localDetailsHaveBeenSet or localEntryId here
  };

  // Show dismissible alert on first view of a newly generated path
  useEffect(() => {
    const alertDismissedKey = `mapmylearn_alert_dismissed_${taskId}`;
    if (!loading && !error && taskId && !isFromHistory && !sessionStorage.getItem(alertDismissedKey)) {
      setShowFirstViewAlert(true);
    }
  }, [loading, error, taskId, isFromHistory]);

  const handleDismissFirstViewAlert = () => {
    const alertDismissedKey = `mapmylearn_alert_dismissed_${taskId}`;
    sessionStorage.setItem(alertDismissedKey, 'true');
    setShowFirstViewAlert(false);
  };

  // Use `loading` directly from hook
  if (loading) {
    return (
      // Pass progressMessages, isReconnecting, and retryAttempt to LoadingState
      <LoadingState 
        progressMessages={progressMessages} 
        isReconnecting={isReconnecting}
        retryAttempt={retryAttempt}
      /> 
    );
  }
  
  // Use `error` directly from hook
  if (error) {
    return (
      <ErrorState 
        error={error || 'An error occurred'} // Use error object/message
        onHomeClick={handleHomeClick}
        onNewLearningPathClick={handleNewLearningPathClick}
      />
    );
  }
  
  // Success state - show learning path
  return (
    <Container maxWidth="lg" sx={{ py: { xs: 3, md: 4 } }}>
      {/* Render the dismissible alert first */}
      {showFirstViewAlert && (
        <Alert 
          severity="info" 
          sx={{ mb: 3, borderRadius: 2 }} 
          onClose={handleDismissFirstViewAlert}
        >
          <AlertTitle>Your Learning Path is Ready!</AlertTitle>
          {helpTexts.lpFirstViewAlert}
        </Alert>
      )}

      {/* Use actualPathData for rendering */} 
      {actualPathData && (
        <>
          <LearningPathHeader 
            topic={actualPathData.topic} 
            detailsHaveBeenSet={localDetailsHaveBeenSet} // Pass renamed state
            isPdfReady={isPdfReady} // Pass new state for PDF readiness
            onDownload={handleDownloadJSONAdjusted} 
            onDownloadPDF={handleDownloadPDFWithUpdate}
            onSaveToHistory={handleSaveToHistory} // Passed from action hook
            onNewLearningPath={handleNewLearningPathClick}
          />
          
          {derivedPathId ? (
            <ModuleSection
              modules={actualPathData.modules} 
              pathId={derivedPathId}
              isTemporaryPath={isTemporaryPath} // Pass re-calculated temporary state
              actualPathData={actualPathData} 
            />
          ) : (
            !loading && <Typography sx={{mt: 2, color: 'error.main'}}>Module ID could not be determined.</Typography>
          )}
          
          {/* Learning Path Resources Section */} 
          {actualPathData.topic_resources && actualPathData.topic_resources.length > 0 && (
            <Box sx={{ mt: 6, mb: 4 }}>
              <ResourcesSection 
                // Access resources correctly based on actualPathData structure
                resources={actualPathData.topic_resources} 
                title="Learning Path Resources"
                type="topic"
              />
            </Box>
          )}
        </>
      )}
      
      {/* Keep Save Dialog and Snackbar as they use actions/state */} 
      <SaveDialog
        open={saveDialogOpen}
        onClose={handleSaveDialogClose}
        onConfirm={handleSaveConfirm} // Use onConfirm, pass handler from action hook
        tags={tags} // Pass state variable from action hook
        newTag={newTag} // Pass state variable from action hook
        favorite={favorite} // Pass state variable from action hook
        onAddTag={handleAddTag} // Pass handler from action hook
        onDeleteTag={handleDeleteTag} // Pass handler from action hook
        onTagChange={setNewTag} // Pass setter from action hook as the change handler
        onTagKeyDown={handleTagKeyDown} // Pass handler from action hook
        onFavoriteChange={setFavorite} // Pass setter from action hook as the change handler
        isMobile={isMobile}
      />
      {/* Ensure notification uses the object structure from the hook */}
      {notification && notification.open && (
          <Snackbar
            open={notification.open}
            autoHideDuration={6000}
            onClose={handleNotificationClose}
            anchorOrigin={{ 
              vertical: 'bottom', 
              horizontal: isMobile ? 'center' : 'right' 
            }}
            sx={{
              bottom: { xs: 16, sm: 24 }
            }}
          >
            <Alert 
              onClose={handleNotificationClose} 
              severity={notification.severity}
              sx={{ width: { xs: '100%', sm: 'auto' } }}
            >
              {notification.message}
            </Alert>
          </Snackbar>
      )}
    </Container>
  );
}

LearningPathView.propTypes = {
  source: PropTypes.string, // 'history' or null/undefined
};

export default LearningPathView;