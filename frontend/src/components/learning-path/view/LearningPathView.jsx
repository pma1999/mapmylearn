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

// Import placeholder component for path resources
import PlaceholderContent from '../../shared/PlaceholderContent';
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
    refreshData
  } = useLearningPathData(source);
  
  // Combined states (from hook or local updates)
  const savedToHistory = localSavedToHistory || initialSavedToHistory;
  const currentLearningPath = localLearningPath || learningPath;
  const isLoading = localLoading !== false && loading;
  const currentError = localError || error;
  
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
    localEntryId || entryId,
    taskId
  );
  
  // Handle save confirmation with state updates
  const handleSaveConfirmWithUpdate = async () => {
    const result = await handleSaveConfirm();
    if (result && result.savedToHistory) {
      setLocalSavedToHistory(true);
      if (result.entryId) {
        setLocalEntryId(result.entryId);
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
            onDownload={handleDownloadJSON}
            onDownloadPDF={handleDownloadPDFWithUpdate}
            onSaveToHistory={handleSaveToHistory}
            onNewLearningPath={handleNewLearningPathClick}
          />
          
          {/* Modules Section */}
          <ModuleSection modules={currentLearningPath.modules} />
          
          {/* Learning Path Resources Section */}
          <Box sx={{ mt: 6, mb: 4 }}>
            <Paper 
              elevation={0} 
              sx={{ 
                p: 3, 
                borderRadius: 2,
                border: '1px solid',
                borderColor: 'divider'
              }}
            >
              <Box sx={{ mb: 3 }}>
                <Typography 
                  variant="h5" 
                  component="h2" 
                  sx={{ 
                    fontWeight: 600, 
                    color: 'primary.main',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1.5,
                    mb: 1
                  }}
                >
                  <MenuBookIcon fontSize="large" />
                  Learning Path Resources
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Comprehensive resources to support your learning journey on {currentLearningPath.topic}.
                </Typography>
                <Divider sx={{ mt: 2 }} />
              </Box>
              
              <PlaceholderContent 
                title="Additional Learning Resources Coming Soon"
                description="This section will contain curated resources for the entire learning path, including reading lists, video lectures, practice problems, and tools related to this topic."
                type="resources"
              />
              
              <Box sx={{ mt: 3, textAlign: 'center' }}>
                <Typography 
                  variant="body2" 
                  color="text.secondary" 
                  sx={{ 
                    fontStyle: 'italic',
                    maxWidth: '80%',
                    mx: 'auto'
                  }}
                >
                  Future updates will include community recommendations, expert-curated materials, and interactive reference tools to enhance your learning experience.
                </Typography>
              </Box>
            </Paper>
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