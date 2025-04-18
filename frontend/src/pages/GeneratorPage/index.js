import React from 'react';
import { Typography, Box, Paper, Container, useMediaQuery, useTheme } from '@mui/material';
import { styled } from '@mui/material/styles';

// Import custom hooks
import useNotification from '../../shared/hooks/useNotification';
import useApiKeyManagement from './hooks/useApiKeyManagement';
import useProgressTracking from './hooks/useProgressTracking';
import useHistoryManagement from './hooks/useHistoryManagement';
import useGeneratorForm from './hooks/useGeneratorForm';

// Import components
import GeneratorForm from './components/GeneratorForm';
import SaveDialog from '../../components/molecules/SaveDialog';
import NotificationSystem from '../../components/molecules/NotificationSystem';

const StyledChip = styled(Box)(({ theme }) => ({
  margin: theme.spacing(0.5),
}));

const ResponsiveContainer = styled(Container)(({ theme }) => ({
  [theme.breakpoints.down('sm')]: {
    padding: theme.spacing(1),
  },
}));

/**
 * Main GeneratorPage component that orchestrates the learning path generation
 * @returns {JSX.Element} Generator page component
 */
const GeneratorPage = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  // Initialize custom hooks with necessary dependencies
  const { notification, showNotification, closeNotification } = useNotification();
  
  const apiKeyState = useApiKeyManagement(showNotification);
  
  const progressTrackingState = useProgressTracking();
  
  const historyState = useHistoryManagement(showNotification);
  
  const formState = useGeneratorForm(
    apiKeyState,
    progressTrackingState,
    historyState,
    showNotification
  );

  // Destructure necessary props for the save dialog
  const { 
    saveDialogOpen, 
    saveDialogTags, 
    saveDialogFavorite, 
    saveDialogNewTag,
    setSaveDialogNewTag,
    handleAddDialogTag,
    handleDeleteDialogTag,
    handleDialogTagKeyDown,
    closeSaveDialog,
    handleSaveConfirm
  } = historyState;

  // Handle save dialog cancellation with potential navigation
  const handleSaveCancel = () => {
    closeSaveDialog();
    
    // Navigate to result page without saving
    if (progressTrackingState.taskId) {
      window.location.href = `/result/${progressTrackingState.taskId}`;
    }
  };

  return (
    <ResponsiveContainer maxWidth="md">
      <Paper elevation={3} sx={{ 
        p: { xs: 2, sm: 3, md: 4 }, 
        borderRadius: 2 
      }}>
        {/* Main Form */}
        <GeneratorForm
          formState={formState}
          apiKeyState={apiKeyState}
          historyState={historyState}
          progressState={progressTrackingState}
          isMobile={isMobile}
        />
      </Paper>
      
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary" sx={{
          fontSize: { xs: '0.75rem', sm: '0.875rem' },
          px: { xs: 2, sm: 0 }
        }}>
          Our AI will research your topic and create a comprehensive learning path
          with modules and submodules to help you master the subject efficiently.
        </Typography>
      </Box>
      
      {/* Save Dialog */}
      <SaveDialog 
        open={saveDialogOpen}
        onClose={handleSaveCancel}
        onSave={handleSaveConfirm}
        onCancel={handleSaveCancel}
        tags={saveDialogTags}
        setTags={saveDialogTags}
        favorite={saveDialogFavorite}
        setFavorite={saveDialogFavorite}
        newTag={saveDialogNewTag}
        setNewTag={setSaveDialogNewTag}
        handleAddTag={handleAddDialogTag}
        handleDeleteTag={handleDeleteDialogTag}
        handleTagKeyDown={handleDialogTagKeyDown}
        isMobile={isMobile}
      />
      
      {/* Notification System */}
      <NotificationSystem 
        notification={notification}
        onClose={closeNotification}
      />
    </ResponsiveContainer>
  );
};

export default GeneratorPage; 