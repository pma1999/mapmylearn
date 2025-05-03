import React from 'react';
import { Typography, Box, Paper, Container, useMediaQuery, useTheme } from '@mui/material';
import { styled } from '@mui/material/styles';

// Import custom hooks
import useNotification from '../../shared/hooks/useNotification';
import useProgressTracking from './hooks/useProgressTracking';
import useHistoryManagement from './hooks/useHistoryManagement';
import useGeneratorForm from './hooks/useGeneratorForm';

// Import components
import GeneratorForm from './components/GeneratorForm';
import SaveDialog from '../../components/molecules/SaveDialog';
import NotificationSystem from '../../components/molecules/NotificationSystem';
import { helpTexts } from '../../constants/helpTexts'; // Import helpTexts

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
  
  const progressTrackingState = useProgressTracking();
  
  const historyState = useHistoryManagement(showNotification);
  
  const formState = useGeneratorForm(
    progressTrackingState,
    showNotification
  );

  // Destructure explanation style from formState
  const { explanationStyle, setExplanationStyle } = formState;

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
        borderRadius: 2,
        mb: 3 // Add margin bottom to separate from subtitle
      }}>
        {/* Main Form */}
        <GeneratorForm
          formState={formState}
          historyState={historyState}
          progressState={progressTrackingState}
          explanationStyle={explanationStyle}
          setExplanationStyle={setExplanationStyle}
          isMobile={isMobile}
        />
      </Paper>
      
      {/* Add Subtitle Here */}
      <Typography 
        variant="subtitle1" 
        color="text.secondary" 
        align="center" 
        sx={{ 
          mb: 4, 
          px: { xs: 2, sm: 0 }
        }}
      >
        {helpTexts.generatorSubtitle}
      </Typography>
      
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