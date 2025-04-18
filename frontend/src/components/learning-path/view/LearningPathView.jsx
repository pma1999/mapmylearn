import React, { useEffect, useState, useCallback } from 'react';
import PropTypes from 'prop-types';
import { useParams } from 'react-router-dom';
import { Container, Snackbar, Alert, useMediaQuery, useTheme, Box, Typography, Paper, Divider } from '@mui/material';

// Custom hooks
import useLearningPathData from '../hooks/useLearningPathData';
import useLearningPathActions from '../hooks/useLearningPathActions';
import useProgressTracking from '../hooks/useProgressTracking';

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
  
  // States for tracking save status updates
  const [localSavedToHistory, setLocalSavedToHistory] = useState(false);
  const [localEntryId, setLocalEntryId] = useState(null);
  const [localLearningPath, setLocalLearningPath] = useState(null);
  const [localLoading, setLocalLoading] = useState(true);
  const [localError, setLocalError] = useState('');
  
  // Load learning path data from appropriate source
  const {
    learningPath,
    loading,
    error,
    isFromHistory,
    savedToHistory: initialSavedToHistory,
    temporaryPathId,
    refreshData
  } = useLearningPathData(source);
  
  // Combined states (from hook or local updates)
  const savedToHistory = localSavedToHistory || initialSavedToHistory;
  const currentLearningPath = localLearningPath || learningPath;
  const isLoading = localLoading !== false && loading;
  const currentError = localError || error;
  const isPersisted = isFromHistory || savedToHistory; // Calculate persisted status
  const isTemporaryPath = !isPersisted && !!temporaryPathId; // Calculate temporary path status
  
  // Determine the correct pathId to use
  // Priority: localEntryId (after save) > entryId (from URL) > learningPath.path_id (intrinsic)
  let derivedPathId = null;
  const currentEntryId = localEntryId || entryId; // Use localEntryId if path was just saved
  if (!isLoading && currentLearningPath) {
    if (isTemporaryPath) {
      derivedPathId = temporaryPathId; // Use temporary ID for unsaved paths
    } else if (currentEntryId) {
      derivedPathId = currentEntryId;
    } else if (!isFromHistory && currentLearningPath.path_id) {
      // Use intrinsic ID if loaded from task result and ID exists
      derivedPathId = currentLearningPath.path_id;
    } else {
      // Log if we somehow can't determine an ID after loading is complete
      console.warn('Could not determine pathId for LearningPathView');
    }
  }
  
  // Callback for when a task completes
  const handleTaskComplete = useCallback((response) => {
    console.log('Task completed with status:', response.status);
    if (response.status === 'completed' && response.result) {
      // Update the data directly
      setLocalLearningPath(response.result);
      setLocalLoading(false);
      setLocalError('');
    } else if (response.status === 'failed') {
      // Set error state
      setLocalError(response.error?.message || 'Learning path generation failed');
      setLocalLoading(false);
    }
  }, []);
  
  // Track generation progress for new learning paths
  const {
    progressMessages,
    isPolling,
    taskStatus,
    startPollingForResult,
    checkTaskStatus
  } = useProgressTracking(taskId, handleTaskComplete);
  
  // Initialize progress tracking for running tasks
  useEffect(() => {
    if (!isFromHistory && taskId && isLoading) {
      startPollingForResult();
    }
  }, [isFromHistory, taskId, isLoading, startPollingForResult]);
  
  // Check task status when component mounts if needed
  useEffect(() => {
    // If we're in the result page and task is not from history,
    // check the current status once
    if (!isFromHistory && taskId && !currentLearningPath) {
      checkTaskStatus();
    }
  }, [isFromHistory, taskId, checkTaskStatus, currentLearningPath]);
  
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
    handleSaveConfirm,
    handleAddTag,
    handleDeleteTag,
    handleTagKeyDown,
    handleNotificationClose
  } = useLearningPathActions(
    currentLearningPath,
    isFromHistory,
    savedToHistory,
    currentEntryId,
    taskId,
    temporaryPathId
  );
  
  // Handle save confirmation with state updates
  const handleSaveConfirmWithUpdate = async () => {
    const result = await handleSaveConfirm();
    if (result && result.savedToHistory) {
      setLocalSavedToHistory(true);
      if (result.path_id) {
        setLocalEntryId(result.path_id);
      } else {
        console.error('Save confirmed but no new path_id received from backend.');
        // Potentially refresh all data as a fallback?
        // refreshData(); 
      }
    }
  };
  
  // Handle PDF download with state updates
  const handleDownloadPDFWithUpdate = async () => {
    const result = await handleDownloadPDF();
    if (result && result.savedToHistory) {
      setLocalSavedToHistory(true);
      if (result.entryId) {
        setLocalEntryId(result.entryId);
      }
    }
  };
  
  // Loading state
  if (isLoading) {
    return (
      <LoadingState 
        progressMessages={progressMessages}
        isPolling={isPolling}
      />
    );
  }
  
  // Error state
  if (currentError) {
    return (
      <ErrorState 
        error={currentError} 
        onHomeClick={handleHomeClick}
        onNewLearningPathClick={handleNewLearningPathClick}
      />
    );
  }
  
  // Success state - show learning path
  return (
    <Container maxWidth="lg" sx={{ py: { xs: 3, md: 4 } }}>
      {/* Header Section */}
      {currentLearningPath && (
        <>
          <LearningPathHeader 
            topic={currentLearningPath.topic}
            savedToHistory={savedToHistory}
            isPersisted={isPersisted}
            onDownload={handleDownloadJSON}
            onDownloadPDF={handleDownloadPDFWithUpdate}
            onSaveToHistory={handleSaveToHistory}
            onNewLearningPath={handleNewLearningPathClick}
          />
          
          {/* Modules Section - Pass derivedPathId and isTemporaryPath */}
          {derivedPathId ? (
            <ModuleSection
              modules={currentLearningPath.modules}
              pathId={derivedPathId}
              isTemporaryPath={isTemporaryPath}
            />
          ) : (
            // Optional: Render a message or placeholder if pathId is still null after loading
            !isLoading && <Typography sx={{mt: 2}}>Module ID not available yet.</Typography>
          )}
          
          {/* Learning Path Resources Section - UPDATED to use ResourcesSection */}
          <Box sx={{ mt: 6, mb: 4 }}>
            <ResourcesSection 
              resources={currentLearningPath.topic_resources} 
              title="Learning Path Resources"
              type="topic"
              isLoading={taskStatus === 'running' && progressMessages.some(msg => msg.phase === 'topic_resources')}
            />
          </Box>
        </>
      )}
      
      {/* Save to History Dialog */}
      <SaveDialog
        open={saveDialogOpen}
        onClose={handleSaveDialogClose}
        onConfirm={handleSaveConfirmWithUpdate}
        tags={tags}
        newTag={newTag}
        favorite={favorite}
        onAddTag={handleAddTag}
        onDeleteTag={handleDeleteTag}
        onTagChange={setNewTag}
        onTagKeyDown={handleTagKeyDown}
        onFavoriteChange={setFavorite}
        isMobile={isMobile}
      />
      
      {/* Notification Snackbar */}
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
    </Container>
  );
};

LearningPathView.propTypes = {
  source: PropTypes.string
};

export default LearningPathView; 