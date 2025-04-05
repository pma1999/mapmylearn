import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { useParams } from 'react-router-dom';
import { Container, Snackbar, Alert, useMediaQuery, useTheme } from '@mui/material';

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
  
  // Load learning path data from appropriate source
  const {
    learningPath,
    loading,
    error,
    isFromHistory,
    savedToHistory: initialSavedToHistory
  } = useLearningPathData(source);
  
  // Combined saved state (from hook or local updates)
  const savedToHistory = localSavedToHistory || initialSavedToHistory;
  
  // Track generation progress for new learning paths
  const {
    progressMessages,
    isPolling,
    startPollingForResult
  } = useProgressTracking(taskId);
  
  // Initialize progress tracking for running tasks
  useEffect(() => {
    if (!isFromHistory && taskId && loading) {
      startPollingForResult();
    }
  }, [isFromHistory, taskId, loading, startPollingForResult]);
  
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
    learningPath,
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
  if (loading) {
    return (
      <LoadingState 
        progressMessages={progressMessages}
        isPolling={isPolling}
      />
    );
  }
  
  // Error state
  if (error) {
    return (
      <ErrorState 
        error={error} 
        onHomeClick={handleHomeClick}
        onNewLearningPathClick={handleNewLearningPathClick}
      />
    );
  }
  
  // Success state - show learning path
  return (
    <Container maxWidth="lg" sx={{ py: { xs: 3, md: 4 } }}>
      {/* Header Section */}
      <LearningPathHeader 
        topic={learningPath.topic}
        savedToHistory={savedToHistory}
        onDownload={handleDownloadJSON}
        onDownloadPDF={handleDownloadPDFWithUpdate}
        onSaveToHistory={handleSaveToHistory}
        onNewLearningPath={handleNewLearningPathClick}
      />
      
      {/* Modules Section */}
      <ModuleSection modules={learningPath.modules} />
      
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