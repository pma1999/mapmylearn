import React, { useEffect, useState, useCallback } from 'react';
import PropTypes from 'prop-types';
import { useParams } from 'react-router-dom';
import { Container, Snackbar, Alert, useMediaQuery, useTheme, Box, Typography, Paper, Divider } from '@mui/material';

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
  
  // States for tracking ACTIONS (like save completion), keep these for now
  const [localSavedToHistory, setLocalSavedToHistory] = useState(false);
  const [localEntryId, setLocalEntryId] = useState(null);
  
  // Load learning path data using the hook - rely solely on this for data/loading/error state
  const {
    learningPath, // This holds the data object (full entry for history, result for generation)
    loading,      // Loading state from the hook
    error,        // Error state from the hook
    isFromHistory,
    savedToHistory: initialSavedToHistory,
    temporaryPathId,
    refreshData // Keep refresh function if needed elsewhere
  } = useLearningPathData(source);
  
  // Use derived state based ONLY on hook values and local ACTION results
  const savedToHistory = localSavedToHistory || initialSavedToHistory;
  const isPersisted = isFromHistory || savedToHistory;
  const isTemporaryPath = !isPersisted && !!temporaryPathId;
  
  // Determine the correct pathId to use (logic seems okay, but adapt to direct learningPath use)
  let derivedPathId = null;
  const currentEntryId = localEntryId || entryId;
  // Use loading directly, access path_id from learningPath if !isFromHistory
  if (!loading && learningPath) { 
    if (isTemporaryPath) {
      derivedPathId = temporaryPathId;
    } else if (currentEntryId) {
      derivedPathId = currentEntryId;
    } else if (!isFromHistory && learningPath.path_id) { 
      // If from generation, path_id might be top-level in the result
      derivedPathId = learningPath.path_id;
    } else if (isFromHistory && learningPath.path_id) {
      // If from history, path_id is top-level in the full entry object
      derivedPathId = learningPath.path_id;
    } else if (isFromHistory && !learningPath.path_id && entryId) {
       // Fallback for history view if somehow path_id is missing in object but we have entryId
       derivedPathId = entryId;
       console.warn('Using entryId as derivedPathId because learningPath.path_id was missing in history view.');
    } else {
      console.warn('Could not determine pathId for LearningPathView');
    }
  }
  
  // Extract the actual path data object, handling both history and generation cases
  // Based on logs, when isFromHistory=true, learningPath is the full entry, data is in learningPath.path_data
  // When isFromHistory=false, learningPath is the result object (assumed to be the path data itself)
  const actualPathData = isFromHistory ? learningPath?.path_data : learningPath;

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
    // Pass the correct data structure to the actions hook
    actualPathData, // Pass the extracted path data
    isFromHistory,
    savedToHistory,
    currentEntryId, // Use the most reliable ID (entry or local override)
    taskId,         // Pass taskId for generation context
    temporaryPathId // Pass temporaryId for potential save action
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
          showNotification('Learning path downloaded successfully', 'success');
      } catch (err) {
          console.error('Error downloading JSON:', err);
          showNotification('Failed to download learning path', 'error');
      }
  };

  // Adjust handleDownloadPDF if it relied on top-level props of learningPath
  // It seems handleDownloadPDF mainly uses `entryId` and `learningPath.topic`
  // `useLearningPathActions` needs `actualPathData` to get the topic correctly.
  const handleDownloadPDFWithUpdate = async () => {
    // The action hook `useLearningPathActions` now receives `actualPathData`,
    // so its internal `handleDownloadPDF` should get the topic correctly.
    // We still need to update local state based on the action result.
    const result = await handleDownloadPDF(); // Call original function from hook
    if (result && result.savedToHistory) {
      setLocalSavedToHistory(true);
      if (result.entryId) {
        setLocalEntryId(result.entryId);
      }
    }
  };

  // Use `loading` directly from hook
  if (loading) {
    return (
      // Keep LoadingState, but remove progressMessages/isPolling if generation logic removed
      <LoadingState /> 
    );
  }
  
  // Use `error` directly from hook
  if (error) {
    return (
      <ErrorState 
        error={error.message || 'An error occurred'} // Use error message
        onHomeClick={handleHomeClick}
        onNewLearningPathClick={handleNewLearningPathClick}
      />
    );
  }
  
  // Success state - show learning path
  return (
    <Container maxWidth="lg" sx={{ py: { xs: 3, md: 4 } }}>
      {/* Use actualPathData for rendering */} 
      {actualPathData && (
        <>
          <LearningPathHeader 
            topic={actualPathData.topic} // Use topic from actualPathData
            savedToHistory={savedToHistory}
            isPersisted={isPersisted}
            onDownload={handleDownloadJSONAdjusted} // Use adjusted download handler
            onDownloadPDF={handleDownloadPDFWithUpdate}
            onSaveToHistory={handleSaveToHistory}
            onNewLearningPath={handleNewLearningPathClick}
          />
          
          {/* Modules Section */} 
          {derivedPathId ? (
            <ModuleSection
              // Access modules correctly based on actualPathData structure
              modules={actualPathData.modules} 
              pathId={derivedPathId}
              isTemporaryPath={isTemporaryPath}
            />
          ) : (
            // Use loading directly here
            !loading && <Typography sx={{mt: 2}}>Module ID not available yet.</Typography>
          )}
          
          {/* Learning Path Resources Section */} 
          <Box sx={{ mt: 6, mb: 4 }}>
            <ResourcesSection 
              // Access resources correctly based on actualPathData structure
              resources={actualPathData.topic_resources} 
              title="Learning Path Resources"
              type="topic"
              // Remove isLoading prop or adjust based on removed polling state
              // isLoading={taskStatus === 'running' && progressMessages.some(msg => msg.phase === 'topic_resources')}
            />
          </Box>
        </>
      )}
      
      {/* Keep Save Dialog and Snackbar as they use actions/state */} 
      <SaveDialog
        open={saveDialogOpen}
        onClose={handleSaveDialogClose}
        onConfirm={handleSaveConfirm}
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