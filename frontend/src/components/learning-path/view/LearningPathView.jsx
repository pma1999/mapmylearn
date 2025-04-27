import React, { useEffect, useState, useCallback, useRef, useMemo } from 'react';
import PropTypes from 'prop-types';
import { useParams } from 'react-router';
import { Container, Snackbar, Alert, AlertTitle, useMediaQuery, useTheme, Box, Typography, Grid, Drawer } from '@mui/material';
import { helpTexts } from '../../../constants/helpTexts'; // Corrected path

// Import API service
import * as apiService from '../../../services/api'; 

// Import necessary icons for availableTabs calculation
import MenuBookIcon from '@mui/icons-material/MenuBook';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import CollectionsBookmarkIcon from '@mui/icons-material/CollectionsBookmark';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import GraphicEqIcon from '@mui/icons-material/GraphicEq';

// Custom hooks
import useLearningPathData from '../hooks/useLearningPathData';
import useLearningPathActions from '../hooks/useLearningPathActions';

// View components
import LearningPathHeader from './LearningPathHeader';
import LoadingState from './LoadingState';
import ErrorState from './ErrorState';
import SaveDialog from './SaveDialog';

// Import the new ResourcesSection component instead of PlaceholderContent
import ResourcesSection from '../../shared/ResourcesSection';

// Import the new layout components
import ModuleNavigationColumn from './ModuleNavigationColumn';
import ContentPanel from './ContentPanel';
import MobileBottomNavigation from './MobileBottomNavigation.jsx';

const DRAWER_WIDTH = 300; // Define a width for the mobile drawer
const AUDIO_CREDIT_COST = 1; // Define or import this

/**
 * Main component for viewing a learning path using the Focus Flow layout.
 * 
 * @param {Object} props Component props
 * @param {string} props.source Source of the learning path ('history' or null/undefined for generation)
 * @returns {JSX.Element} Learning path view component
 */
const LearningPathView = ({ source }) => {
  const { taskId, entryId } = useParams();
  const theme = useTheme();
  const isMobileLayout = useMediaQuery(theme.breakpoints.down('md'));
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [showFirstViewAlert, setShowFirstViewAlert] = useState(false);
  
  // Mobile drawer state
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  // Load learning path data using the hook
  const {
    learningPath, 
    loading,      
    error,        
    isFromHistory,
    initialDetailsWereSet,
    persistentPathId, 
    temporaryPathId,
    progressMessages, 
    isReconnecting, 
    retryAttempt,   
    refreshData, 
    progressMap,
    setProgressMap,
    lastVisitedModuleIdx,
    lastVisitedSubmoduleIdx
  } = useLearningPathData(source); 
  
  // State for Focus Flow navigation
  const [activeModuleIndex, setActiveModuleIndex] = useState(null);
  const [activeSubmoduleIndex, setActiveSubmoduleIndex] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [initialLoadComplete, setInitialLoadComplete] = useState(false);

  // Local state for tracking if details (tags/favorites) have been set via dialog
  const [localDetailsHaveBeenSet, setLocalDetailsHaveBeenSet] = useState(false);
  const [localEntryId, setLocalEntryId] = useState(null);

  // Ref for ContentPanel scrolling
  const contentPanelRef = useRef(null);

  // Effect to initialize local state once loading is done and we have initial data
  useEffect(() => {
    if (!loading) {
        setInitialLoadComplete(true);
        setLocalDetailsHaveBeenSet(initialDetailsWereSet || false);
        if (isFromHistory && persistentPathId) {
            setLocalEntryId(persistentPathId);
        } else {
            setLocalEntryId(null);
        }
    }
  }, [loading, initialDetailsWereSet, isFromHistory, persistentPathId]);
  
  // Derived states based on hook values and local actions
  const isPdfReady = !loading && !!persistentPathId;
  const isPersisted = isFromHistory || localDetailsHaveBeenSet || isPdfReady;
  const isTemporaryPath = !loading && !!temporaryPathId && !persistentPathId;
  
  // Determine the correct pathId to use for component interactions
  let derivedPathId = null;
  const currentEntryId = localEntryId || entryId || persistentPathId;
  
  if (!loading && learningPath) { 
    if (isTemporaryPath) {
      derivedPathId = temporaryPathId;
    } else {
      derivedPathId = currentEntryId; 
    }
    if (!derivedPathId) {
      console.warn('Could not reliably determine pathId for LearningPathView interactions.');
    }
  }
  
  // Extract the actual path data object
  const actualPathData = isFromHistory
    ? (learningPath?.path_data ? learningPath.path_data : learningPath)
    : learningPath;

  // Effect to set initial active module/submodule from last visited or default
  useEffect(() => {
      // Only run once after the initial load is complete
      if (initialLoadComplete && actualPathData && actualPathData.modules && actualPathData.modules.length > 0) {
          // Check if last visited indices are valid
          const isValidLastVisited = 
              lastVisitedModuleIdx !== null && lastVisitedModuleIdx >= 0 && lastVisitedModuleIdx < actualPathData.modules.length &&
              lastVisitedSubmoduleIdx !== null && lastVisitedSubmoduleIdx >= 0 && 
              actualPathData.modules[lastVisitedModuleIdx]?.submodules?.length > lastVisitedSubmoduleIdx;

          if (isValidLastVisited) {
              console.log('Setting initial navigation from last visited:', lastVisitedModuleIdx, lastVisitedSubmoduleIdx);
              setActiveModuleIndex(lastVisitedModuleIdx);
              setActiveSubmoduleIndex(lastVisitedSubmoduleIdx);
          } else if (activeModuleIndex === null) {
              // Default to first module/submodule if last visited is invalid or not set
              console.log('Setting initial navigation to default (0, 0)');
              setActiveModuleIndex(0);
              if (actualPathData.modules[0]?.submodules?.length > 0) {
                  setActiveSubmoduleIndex(0);
              }
          }
      } else if (initialLoadComplete && (!actualPathData || !actualPathData.modules || actualPathData.modules.length === 0)) {
          setActiveModuleIndex(null);
          setActiveSubmoduleIndex(null);
      }
  // Run ONLY when initial load completes, or if path data/last visited changes AFTER initial load
  }, [initialLoadComplete, actualPathData, lastVisitedModuleIdx, lastVisitedSubmoduleIdx]);

  // Effect to update the last visited position on the backend when navigation changes
  useEffect(() => {
    // Only run if the path is persisted and navigation indices are valid
    if (currentEntryId && activeModuleIndex !== null && activeSubmoduleIndex !== null) {
      // Debounce or throttle this call if needed, but for now, call directly
      console.log(`Updating last visited API: M ${activeModuleIndex}, S ${activeSubmoduleIndex}`);
      apiService.updateLastVisited(currentEntryId, activeModuleIndex, activeSubmoduleIndex)
        .catch(warn => console.warn("Failed to update last visited position:", warn)); // Log warning on failure
    }
  // Depend on the navigation indices and the persisted ID
  }, [currentEntryId, activeModuleIndex, activeSubmoduleIndex]);

  // Callback for when save is confirmed in the action hook
  const handleSaveSuccess = useCallback((result) => {
    if (result?.entryId) {
      setLocalDetailsHaveBeenSet(true);
      setLocalEntryId(result.entryId);
    }
  }, []);

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
    handleNotificationClose,
    showNotification
  } = useLearningPathActions(
    actualPathData, 
    isFromHistory,
    localDetailsHaveBeenSet,
    currentEntryId, 
    taskId,         
    temporaryPathId, 
    handleSaveSuccess
  );
  
  // Handler to toggle progress state
  const handleToggleProgress = useCallback(async (modIndex, subIndex) => {
    if (!currentEntryId) {
      console.warn('Cannot toggle progress: Path is not persisted yet.');
      // Optionally show a notification to save the path first
      showNotification('Please save the learning path to track progress.', 'warning');
      return;
    }

    const progressKey = `${modIndex}_${subIndex}`;
    const currentCompletionStatus = progressMap[progressKey] || false;
    const newCompletionStatus = !currentCompletionStatus;

    // Optimistic UI Update
    setProgressMap(prevMap => ({
      ...prevMap,
      [progressKey]: newCompletionStatus
    }));

    // API Call
    try {
      await apiService.updateSubmoduleProgress(currentEntryId, modIndex, subIndex, newCompletionStatus);
      console.log(`Progress updated successfully for ${progressKey} to ${newCompletionStatus}`);
      // Optional: Success notification
      // showNotification(`Submodule ${modIndex + 1}.${subIndex + 1} marked as ${newCompletionStatus ? 'complete' : 'incomplete'}.`, 'success');
    } catch (error) {
      console.error(`Failed to update progress for ${progressKey}:`, error);
      // Revert Optimistic Update on error
      setProgressMap(prevMap => ({
        ...prevMap,
        [progressKey]: currentCompletionStatus // Revert to original state
      }));
      // Show error notification
      showNotification(`Failed to update progress for submodule ${modIndex + 1}.${subIndex + 1}.`, 'error');
    }
  }, [currentEntryId, progressMap, setProgressMap, showNotification]);

  // Adjust action handlers
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

  // Navigation Handler for ContentPanel and MobileBottomNavigation
  const handleNavigation = useCallback((direction) => {
      if (!actualPathData || activeModuleIndex === null || activeSubmoduleIndex === null) return;

      const currentModule = actualPathData.modules[activeModuleIndex];
      const numSubmodules = currentModule?.submodules?.length || 0;
      const numModules = actualPathData.modules.length;

      if (direction === 'prev') {
          if (activeSubmoduleIndex > 0) {
              setActiveSubmoduleIndex(prev => prev - 1);
          } else if (activeModuleIndex > 0) {
              const prevModuleIndex = activeModuleIndex - 1;
              const prevModule = actualPathData.modules[prevModuleIndex];
              const lastSubmoduleIndex = (prevModule?.submodules?.length || 1) - 1; // Handle modules with 0 submodules gracefully? Needs data structure assumption. Defaulting to 0.
              setActiveModuleIndex(prevModuleIndex);
              setActiveSubmoduleIndex(lastSubmoduleIndex >= 0 ? lastSubmoduleIndex : 0); // Ensure non-negative index
          }
      } else if (direction === 'next') {
          if (activeSubmoduleIndex < numSubmodules - 1) {
              setActiveSubmoduleIndex(prev => prev + 1);
          } else if (activeModuleIndex < numModules - 1) {
              const nextModuleIndex = activeModuleIndex + 1;
              setActiveModuleIndex(nextModuleIndex);
              setActiveSubmoduleIndex(0); // Go to first submodule of next module
          }
      } else if (direction === 'nextModule') {
          if (activeModuleIndex < numModules - 1) {
              const nextModuleIndex = activeModuleIndex + 1;
              setActiveModuleIndex(nextModuleIndex);
              setActiveSubmoduleIndex(0); // Go to first submodule of next module
          }
      }
  }, [actualPathData, activeModuleIndex, activeSubmoduleIndex, setActiveModuleIndex, setActiveSubmoduleIndex]);

  // Mobile Navigation Handlers
  const handleMobileNavToggle = () => {
    setMobileNavOpen(!mobileNavOpen);
  };

  const handleMobileNavClose = () => {
    setMobileNavOpen(false);
  };

  const handleSubmoduleSelectFromDrawer = (modIndex, subIndex) => {
     // No need to setActiveModuleIndex/setActiveSubmoduleIndex, 
     // as the component itself already did that onClick.
     // Just close the drawer.
     handleMobileNavClose();
  };

  // Calculate current submodule and available tabs
  const modules = actualPathData?.modules || [];
  const totalModules = modules.length;
  const currentModule = (activeModuleIndex !== null && activeModuleIndex >= 0 && activeModuleIndex < totalModules)
                        ? modules[activeModuleIndex]
                        : null;
  const totalSubmodulesInModule = currentModule?.submodules?.length || 0;
  const currentSubmodule = (currentModule && activeSubmoduleIndex !== null && activeSubmoduleIndex >= 0 && activeSubmoduleIndex < totalSubmodulesInModule)
                         ? currentModule.submodules[activeSubmoduleIndex]
                         : null;

  const availableTabs = useMemo(() => {
    if (!currentSubmodule) return [];

    const hasQuiz = currentSubmodule.quiz_questions && currentSubmodule.quiz_questions.length > 0;
    const hasResources = currentSubmodule.resources && currentSubmodule.resources.length > 0;

    let tabIndexCounter = 0;
    const tabs = [
        // Match the structure expected by MobileBottomNavigation (index, label, icon)
        { index: tabIndexCounter++, label: 'Content', icon: <MenuBookIcon />, tooltip: "View submodule content" },
        ...(hasQuiz ? [{ index: tabIndexCounter++, label: 'Quiz', icon: <FitnessCenterIcon />, tooltip: helpTexts.submoduleTabQuiz }] : []),
        ...(hasResources ? [{ index: tabIndexCounter++, label: 'Resources', icon: <CollectionsBookmarkIcon />, tooltip: "View submodule resources" }] : []),
        { index: tabIndexCounter++, label: 'Chat', icon: <QuestionAnswerIcon />, tooltip: helpTexts.submoduleTabChat },
        { index: tabIndexCounter++, label: 'Audio', icon: <GraphicEqIcon />, tooltip: helpTexts.submoduleTabAudio(AUDIO_CREDIT_COST) },
    ];
    return tabs;
  }, [currentSubmodule]);

  // Effect to reset activeTab if it becomes invalid
  useEffect(() => {
      // Only reset if the current tab index is out of bounds for the *new* set of available tabs
      if (availableTabs.length > 0 && activeTab >= availableTabs.length) {
          setActiveTab(0); // Reset to the first tab (Content)
      }
      // If there are no tabs (e.g., no submodule selected), also reset (though activeTab=0 is fine)
      else if (availableTabs.length === 0 && activeTab !== 0) {
          setActiveTab(0);
      }
  // Depend on availableTabs array (which depends on currentSubmodule) and the current activeTab index itself.
  }, [availableTabs, activeTab]);

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
  
  // Success state - Render Focus Flow Layout
  return (
    // Use theme background implicitly via CssBaseline
    <Container maxWidth="xl" sx={{ pt: { xs: 2, md: 3 }, pb: { xs: theme.spacing(8), md: 4 }, display: 'flex', flexDirection: 'column', flexGrow: 1 }}> 
      {/* Render the dismissible alert */}
      {showFirstViewAlert && (
        <Alert 
          severity="info" 
          // Use theme alert styling
          sx={{ mb: 2, flexShrink: 0 }} 
          onClose={handleDismissFirstViewAlert}
        >
          <AlertTitle>Your Learning Path is Ready!</AlertTitle>
          {helpTexts.lpFirstViewAlert}
        </Alert>
      )}

      {/* Use actualPathData for rendering */} 
      {actualPathData && (
        <>
          {/* Header: Pass mobile nav props */}
          {/* Use theme spacing */} 
          <Box sx={{ flexShrink: 0, mb: { xs: 2, md: 3 } }}> 
             <LearningPathHeader 
               topic={actualPathData.topic} 
               detailsHaveBeenSet={localDetailsHaveBeenSet} 
               isPdfReady={isPdfReady} 
               onDownload={handleDownloadJSONAdjusted} 
               onDownloadPDF={handleDownloadPDFWithUpdate}
               onSaveToHistory={handleSaveToHistory} 
               onNewLearningPath={handleNewLearningPathClick}
               onOpenMobileNav={handleMobileNavToggle} // Pass handler
               showMobileNavButton={isMobileLayout} // Show button only on mobile layout
               progressMap={progressMap}
               actualPathData={actualPathData}
             />
             {/* Optional: Add overall progress bar here */}
             {/* Optional: Add Topic Resources link/button here */}
              {actualPathData.topic_resources && actualPathData.topic_resources.length > 0 && (
                <Box sx={{ mt: 2 }}>
                   {/* Simple link for now, could be a button opening a modal/drawer */}
                   <Typography variant="caption">
                      {/* Maybe link to a dedicated section/modal */}
                      {actualPathData.topic_resources.length} topic resource(s) available. 
                   </Typography>
                </Box>
              )}
          </Box>

          {/* Main Content Area: Conditional Layout */} 
          <Box sx={{ flexGrow: 1, overflow: 'hidden', position: 'relative' }}> 
            {isMobileLayout ? (
               // --- Mobile Layout (Content Panel + Drawer for Nav + Bottom Nav) --- 
               <> 
                  {/* Content Panel fills available space */} 
                  <Box sx={{ height: '100%' }}> 
                      <ContentPanel
                         ref={contentPanelRef}
                         sx={{ height: '100%' }}
                         module={currentModule}
                         moduleIndex={activeModuleIndex}
                         submodule={currentSubmodule}
                         submoduleIndex={activeSubmoduleIndex}
                         pathId={derivedPathId}
                         isTemporaryPath={isTemporaryPath}
                         actualPathData={actualPathData}
                         onNavigate={handleNavigation}
                         totalModules={totalModules}
                         totalSubmodulesInModule={totalSubmodulesInModule}
                         isMobileLayout={isMobileLayout}
                         activeTab={activeTab}
                         setActiveTab={setActiveTab}
                         progressMap={progressMap}
                         onToggleProgress={handleToggleProgress}
                      />
                  </Box>

                  {/* Drawer for Module Navigation */}
                  <Drawer
                     anchor="left"
                     open={mobileNavOpen}
                     onClose={handleMobileNavClose}
                     ModalProps={{
                       keepMounted: true, // Better open performance on mobile.
                     }}
                     PaperProps={{ 
                       sx: { width: DRAWER_WIDTH }
                     }}
                  >
                     <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
                         <Typography variant="h6">Modules</Typography>
                     </Box>
                     <ModuleNavigationColumn
                         modules={modules}
                         activeModuleIndex={activeModuleIndex}
                         setActiveModuleIndex={setActiveModuleIndex}
                         activeSubmoduleIndex={activeSubmoduleIndex}
                         setActiveSubmoduleIndex={setActiveSubmoduleIndex}
                         progressMap={progressMap}
                         onToggleProgress={handleToggleProgress}
                      />
                  </Drawer>
                  
                  {/* Render Mobile Bottom Navigation */} 
                  <MobileBottomNavigation 
                     onNavigate={handleNavigation}
                     activeModuleIndex={activeModuleIndex}
                     activeSubmoduleIndex={activeSubmoduleIndex}
                     totalModules={totalModules}
                     totalSubmodulesInModule={totalSubmodulesInModule}
                     activeTab={activeTab}
                     setActiveTab={setActiveTab}
                     availableTabs={availableTabs}
                     onOpenMobileNav={handleMobileNavToggle}
                  />
               </>
            ) : (
               // --- Desktop Layout (Two Columns Grid) ---
               // Use theme spacing 
               <Grid container spacing={{ xs: 0, md: 2 }} sx={{ height: '100%', flexGrow: 1 }}> 
                  <Grid item xs={12} md={4} sx={{ 
                     height: { xs: 'auto', md: '100%' }, // Allow natural height on mobile, full height on desktop
                     pb: { xs: 2, md: 0 } // Add bottom padding on mobile
                  }}> 
                     <ModuleNavigationColumn
                        modules={modules}
                        activeModuleIndex={activeModuleIndex}
                        setActiveModuleIndex={setActiveModuleIndex}
                        activeSubmoduleIndex={activeSubmoduleIndex}
                        setActiveSubmoduleIndex={setActiveSubmoduleIndex}
                        progressMap={progressMap}
                        onToggleProgress={handleToggleProgress}
                     />
                  </Grid>
                  <Grid item xs={12} md={8} sx={{ 
                     // No height/overflow needed here, ContentPanel handles it
                   }}> 
                     <ContentPanel
                        ref={contentPanelRef}
                        sx={{ height: '100%' }}
                        module={currentModule}
                        moduleIndex={activeModuleIndex}
                        submodule={currentSubmodule}
                        submoduleIndex={activeSubmoduleIndex}
                        pathId={derivedPathId}
                        isTemporaryPath={isTemporaryPath}
                        actualPathData={actualPathData}
                        onNavigate={handleNavigation}
                        totalModules={totalModules}
                        totalSubmodulesInModule={totalSubmodulesInModule}
                        isMobileLayout={isMobileLayout}
                        activeTab={activeTab}
                        setActiveTab={setActiveTab}
                        progressMap={progressMap}
                        onToggleProgress={handleToggleProgress}
                     />
                  </Grid>
               </Grid>
            )}
          </Box>
          
          {/* Old Topic Resources Section (can be removed if handled above) */}
          {/* Commented out as requested in previous step 
          {actualPathData.topic_resources && actualPathData.topic_resources.length > 0 && (
            <Box sx={{ mt: 4, flexShrink: 0 }}>
              <ResourcesSection 
                resources={actualPathData.topic_resources} 
                title="Learning Path Resources"
                type="topic"
              />
            </Box>
          )} 
          */}
        </>
      )}
      
      {/* Save Dialog and Snackbar remain outside the main layout */} 
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
        isMobile={isMobile} // Keep for dialog responsiveness
      />
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
              // Use theme spacing
              bottom: { xs: theme.spacing(2), sm: theme.spacing(3) }, 
              // Adjust width if needed
              // width: { xs: `calc(100% - ${theme.spacing(4)})`, sm: 'auto' },
              // left: { xs: theme.spacing(2), sm: 'auto' },
              // right: { xs: theme.spacing(2), sm: theme.spacing(3) }
            }}
          >
            {/* Alert uses theme styling */} 
            <Alert 
              onClose={handleNotificationClose} 
              severity={notification.severity}
              elevation={6} // Add elevation for snackbar alert
              variant="filled" // Use filled variant for snackbar
              sx={{ width: '100%' }} // Ensure it takes full width in snackbar
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