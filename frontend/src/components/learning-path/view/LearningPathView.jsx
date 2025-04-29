import React, { useEffect, useState, useCallback, useRef, useMemo } from 'react';
import PropTypes from 'prop-types';
import { useParams } from 'react-router';
import { Container, Snackbar, Alert, AlertTitle, useMediaQuery, useTheme, Box, Typography, Grid, Drawer } from '@mui/material';
import { helpTexts } from '../../../constants/helpTexts'; // Corrected path
import Joyride, { ACTIONS, EVENTS, STATUS } from 'react-joyride'; // Import Joyride

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
const TUTORIAL_STORAGE_KEY = 'learniTutorialCompleted'; // Key for localStorage

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

  // Tutorial State
  const [runTutorial, setRunTutorial] = useState(false);
  const [tutorialStepIndex, setTutorialStepIndex] = useState(0);

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
        { index: tabIndexCounter++, label: 'Content', icon: <MenuBookIcon />, tooltip: "View submodule content", dataTut: 'content-panel-tab-content' },
        ...(hasQuiz ? [{ index: tabIndexCounter++, label: 'Quiz', icon: <FitnessCenterIcon />, tooltip: helpTexts.submoduleTabQuiz, dataTut: 'content-panel-tab-quiz' }] : []),
        ...(hasResources ? [{ index: tabIndexCounter++, label: 'Resources', icon: <CollectionsBookmarkIcon />, tooltip: "View submodule resources", dataTut: 'content-panel-tab-resources' }] : []),
        { index: tabIndexCounter++, label: 'Chat', icon: <QuestionAnswerIcon />, tooltip: helpTexts.submoduleTabChat, dataTut: 'content-panel-tab-chat' },
        { index: tabIndexCounter++, label: 'Audio', icon: <GraphicEqIcon />, tooltip: helpTexts.submoduleTabAudio(AUDIO_CREDIT_COST), dataTut: 'content-panel-tab-audio' },
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

  // Effect to check for first visit and start tutorial
  useEffect(() => {
    const tutorialCompleted = localStorage.getItem(TUTORIAL_STORAGE_KEY);
    if (!loading && !tutorialCompleted) {
      // Delay slightly to allow layout to settle?
      setTimeout(() => setRunTutorial(true), 500); 
    }
  }, [loading]); // Run only when loading status changes

  // --- Tutorial Logic ---
  const startTutorial = () => {
    setTutorialStepIndex(0);
    setRunTutorial(true);
  };

  const handleJoyrideCallback = (data) => {
    const { action, index, status, type } = data;

    if ([EVENTS.STEP_AFTER, EVENTS.TARGET_NOT_FOUND].includes(type)) {
      // Update the step index
      setTutorialStepIndex(index + (action === ACTIONS.PREV ? -1 : 1));
    } else if ([STATUS.FINISHED, STATUS.SKIPPED].includes(status)) {
      // Tutorial finished or skipped
      setRunTutorial(false);
      setTutorialStepIndex(0);
      localStorage.setItem(TUTORIAL_STORAGE_KEY, 'true');
    }

    console.log('Joyride callback:', data);
  };

  // Define Tutorial Steps
  const getTutorialSteps = (isMobile) => {
    // Helper to find tab index by dataTut attribute
    const findTabIndex = (dataTut) => availableTabs.findIndex(t => t.dataTut === dataTut);

    const commonSteps = [
      {
        target: '[data-tut="lp-header"]',
        content: 'Welcome to your Learning Path! This header shows the main topic.',
        placement: 'bottom',
        disableBeacon: true,
      },
    ];

    const desktopSteps = [
      ...commonSteps,
      {
        target: '[data-tut="module-navigation-column"]',
        content: 'On the left, you have the modules. Click a module to see its submodules.',
        placement: 'right',
        disableBeacon: true,
      },
      {
        target: '[data-tut="module-item-0"]',
        content: 'Click here to expand the first module.',
        placement: 'right',
        disableBeacon: true,
        // Callback to expand the first module before showing next step
        callback: () => setActiveModuleIndex(0),
      },
      {
        target: '[data-tut="submodule-item-0-0"]',
        content: 'Now click the first submodule to view its content.',
        placement: 'right',
        disableBeacon: true,
        // Callback to select the first submodule
        callback: () => {
          setActiveModuleIndex(0);
          setActiveSubmoduleIndex(0);
        }
      },
      {
        target: '[data-tut="content-panel"]',
        content: 'The main content area shows details for the selected submodule.',
        placement: 'left',
        disableBeacon: true,
      },
      {
        target: '[data-tut="content-panel-tabs"]',
        content: 'Use these tabs to explore different aspects of the submodule.',
        placement: 'bottom',
        disableBeacon: true,
      },
      {
        target: '[data-tut="content-panel-tab-content"]',
        content: 'This is the main learning material for the submodule.',
        placement: 'top',
        disableBeacon: true,
        callback: () => setActiveTab(findTabIndex('content-panel-tab-content') ?? 0)
      },
      // Add steps for other tabs if they exist, using callbacks to switch activeTab
      ...(availableTabs.some(t => t.dataTut === 'content-panel-tab-quiz') ? [{
        target: '[data-tut="content-panel-tab-quiz"]',
        content: 'Test your understanding with a short quiz.',
        placement: 'top',
        disableBeacon: true,
        callback: () => setActiveTab(findTabIndex('content-panel-tab-quiz'))
      }] : []),
      ...(availableTabs.some(t => t.dataTut === 'content-panel-tab-resources') ? [{
        target: '[data-tut="content-panel-tab-resources"]',
        content: 'Find additional resources like articles or videos here.',
        placement: 'top',
        disableBeacon: true,
        callback: () => setActiveTab(findTabIndex('content-panel-tab-resources'))
      }] : []),
       {
        target: '[data-tut="content-panel-tab-chat"]',
        content: 'Chat with an AI assistant about this specific submodule.',
        placement: 'top',
        disableBeacon: true,
        callback: () => setActiveTab(findTabIndex('content-panel-tab-chat'))
      },
       {
        target: '[data-tut="content-panel-tab-audio"]',
        content: 'Generate an audio version of the submodule content (costs credits!).',
        placement: 'top',
        disableBeacon: true,
        callback: () => setActiveTab(findTabIndex('content-panel-tab-audio'))
      },
      {
        target: '[data-tut="content-panel-progress-checkbox-container"]',
        content: 'Once you\'ve finished a submodule, check this box to mark it complete!',
        placement: 'top',
        disableBeacon: true,
        callback: () => setActiveTab(findTabIndex('content-panel-tab-content') ?? 0) // Switch back to content tab
      },
      {
        target: '[data-tut="progress-checkbox-0-0"]',
        content: 'You can also mark submodules complete directly in the navigation list.',
        placement: 'right',
        disableBeacon: true,
      },
      {
        target: '[data-tut="content-panel-prev-button"]',
        content: 'Use these buttons to navigate between submodules...',
        placement: 'bottom',
        disableBeacon: true,
      },
      {
        target: '[data-tut="content-panel-next-module-button"]',
        content: '...or jump to the next module entirely.',
        placement: 'bottom',
        disableBeacon: true,
      },
      {
        target: '[data-tut="save-path-button"]',
        content: 'Remember to save your path to track progress and access it later!',
        placement: 'bottom',
        disableBeacon: true,
      },
      {
        target: '[data-tut="help-icon"]',
        content: 'Click this icon anytime to see this tutorial again.',
        placement: 'bottom',
        disableBeacon: true,
      },
    ];

    const mobileSteps = [
      ...commonSteps,
      {
        target: '[data-tut="mobile-nav-open-button"]',
        content: 'Tap here to open the module navigation drawer.',
        placement: 'top',
        disableBeacon: true,
        callback: () => setMobileNavOpen(true) // Open drawer for next step
      },
      {
        target: '[data-tut="module-navigation-column"]',
        content: 'Select modules and submodules here. Tap the first module.',
        placement: 'right',
        isFixed: true, // Important for elements inside drawers/modals
        disableBeacon: true,
        callback: () => setActiveModuleIndex(0) // Expand module
      },
      {
        target: '[data-tut="submodule-item-0-0"]',
        content: 'Now tap the first submodule to view it and close the drawer.',
        placement: 'right',
        isFixed: true,
        disableBeacon: true,
        callback: () => { // Select submodule and close drawer
          setActiveModuleIndex(0);
          setActiveSubmoduleIndex(0);
          setMobileNavOpen(false);
        }
      },
      {
        target: '[data-tut="content-panel"]',
        content: 'The main content for the selected submodule is shown here.',
        placement: 'top',
        disableBeacon: true,
      },
      {
        target: '[data-tut="mobile-tab-buttons"]',
        content: 'Use these icons to switch between Content, Quiz, Resources, Chat, and Audio for this submodule.',
        placement: 'top',
        disableBeacon: true,
      },
      // Add steps for mobile tabs if needed, similar to desktop, using setActiveTab callback
      // ... (example: focus on content tab first)
      {
        target: '[data-tut="content-panel-tab-content"]',
        content: 'This is the main learning material.',
        placement: 'top',
        disableBeacon: true,
        callback: () => setActiveTab(findTabIndex('content-panel-tab-content') ?? 0)
      },
      // Add step for mobile progress checkbox (inside content)
      {
        target: '[data-tut="content-panel-progress-checkbox-container"]',
        content: 'Mark the submodule complete here when you\'re done.',
        placement: 'top',
        disableBeacon: true,
      },
      {
        target: '[data-tut="mobile-prev-button"]',
        content: 'Tap these buttons to navigate to the previous or next submodule.',
        placement: 'top',
        disableBeacon: true,
      },
       {
        target: '[data-tut="save-path-button"]',
        content: 'Remember to save your path to track progress and access it later!',
        placement: 'bottom',
        disableBeacon: true,
      },
       {
        target: '[data-tut="help-icon"]',
        content: 'Tap the help icon in the header anytime to see this tutorial again.',
        placement: 'bottom',
        disableBeacon: true,
      },
    ];

    return isMobile ? mobileSteps : desktopSteps;
  };

  const tutorialSteps = useMemo(() => getTutorialSteps(isMobileLayout), [isMobileLayout, availableTabs, actualPathData]);

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
               onStartTutorial={startTutorial} // Pass tutorial trigger
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
      
      {/* Joyride Component */}
      <Joyride 
        steps={tutorialSteps}
        run={runTutorial}
        stepIndex={tutorialStepIndex}
        callback={handleJoyrideCallback}
        continuous={true}
        showProgress={true}
        showSkipButton={true}
        scrollToFirstStep={true}
        // Styling to somewhat match MUI
        styles={{
          options: {
            arrowColor: theme.palette.background.paper,
            backgroundColor: theme.palette.background.paper,
            overlayColor: 'rgba(0, 0, 0, 0.6)',
            primaryColor: theme.palette.primary.main,
            textColor: theme.palette.text.primary,
            zIndex: theme.zIndex.tooltip + 1, // Ensure it's above most elements
          },
          buttonNext: {
            backgroundColor: theme.palette.primary.main,
            borderRadius: theme.shape.borderRadius,
          },
          buttonBack: {
            color: theme.palette.primary.main,
          },
           buttonSkip: {
             color: theme.palette.text.secondary,
           },
          tooltip: {
             borderRadius: theme.shape.borderRadius,
          },
          tooltipContent: {
             padding: theme.spacing(2),
          },
        }}
      />

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