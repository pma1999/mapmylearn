import React, { useEffect, useState, useCallback, useRef, useMemo } from 'react';
import PropTypes from 'prop-types';
import { useParams, useNavigate } from 'react-router';
import { Container, Snackbar, Alert, AlertTitle, useMediaQuery, useTheme, Box, Typography, Grid, Drawer, Button } from '@mui/material';
import { helpTexts } from '../../../constants/helpTexts'; // Corrected path
import Joyride, { ACTIONS, EVENTS, STATUS } from 'react-joyride'; // Import Joyride
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import { motion } from 'framer-motion';

// Import API service
import * as apiService from '../../../services/api';

// Import necessary icons for availableTabs calculation
import MenuBookIcon from '@mui/icons-material/MenuBook';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import CollectionsBookmarkIcon from '@mui/icons-material/CollectionsBookmark';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import GraphicEqIcon from '@mui/icons-material/GraphicEq';
import LoginIcon from '@mui/icons-material/Login';
import BookmarkAddIcon from '@mui/icons-material/BookmarkAdd'; // Import needed for header prop pass potentially

// Custom hooks
import useLearningPathData from '../hooks/useLearningPathData';
import useLearningPathActions from '../hooks/useLearningPathActions';
import usePathSharingActions from '../../../hooks/usePathSharingActions';
import { useAuth } from '../../../services/authContext';

// View components
import LearningPathHeader from './LearningPathHeader';
import LoadingState from './LoadingState';
import ErrorState from './ErrorState';
import SaveDialog from './SaveDialog';

// Import the new ResourcesSection component
import ResourcesSection from '../../shared/ResourcesSection';

// Import the new layout components
import ModuleNavigationColumn from './ModuleNavigationColumn';
import ContentPanel from './ContentPanel';
import MobileBottomNavigation from './MobileBottomNavigation.jsx';

const DRAWER_WIDTH = 300; // Define a width for the mobile drawer
const AUDIO_CREDIT_COST = 1; // Define or import this
const TUTORIAL_STORAGE_KEY = 'learniTutorialCompleted'; // Key for localStorage

/**
 * Main component for viewing a course using the Focus Flow layout.
 * 
 * @param {Object} props Component props
 * @param {string} props.source Source of the course ('history', 'public' or null/undefined for generation)
 * @returns {JSX.Element} course view component
 */
const LearningPathView = ({ source }) => {
  const { taskId, entryId, shareId } = useParams();
  const theme = useTheme();
  const isMobileLayout = useMediaQuery(theme.breakpoints.down('md'));
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [showFirstViewAlert, setShowFirstViewAlert] = useState(false);
  
  // --- State for Copying Action ---
  const [isCopying, setIsCopying] = useState(false);
  
  // Mobile drawer state
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  // Tutorial State
  const [runTutorial, setRunTutorial] = useState(false);
  const [tutorialStepIndex, setTutorialStepIndex] = useState(0);

  // --- NEW: Get auth state --- 
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate(); // For login/register buttons and copy redirect

  // Load course data using the hook
  const {
    learningPath, 
    loading,      
    error,        
    isFromHistory,
    initialDetailsWereSet,
    persistentPathId, 
    temporaryPathId,
    refreshData, 
    progressMap,
    setProgressMap,
    lastVisitedModuleIdx,
    lastVisitedSubmoduleIdx,
    isPublicView, // Get public view status from hook
  } = useLearningPathData(source); 
  
  // State for Focus Flow navigation
  const [activeModuleIndex, setActiveModuleIndex] = useState(null);
  const [activeSubmoduleIndex, setActiveSubmoduleIndex] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [initialLoadComplete, setInitialLoadComplete] = useState(false);

  // --- NEW: State for ContentPanel display type ---
  const [contentPanelDisplayType, setContentPanelDisplayType] = useState('submodule'); // 'submodule' or 'module_resources'

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
  const isPdfReady = !loading && !!persistentPathId && !isPublicView; // PDF might not be ready/allowed in public view initially
  const isPersisted = (isFromHistory || localDetailsHaveBeenSet || isPdfReady) && !isPublicView; // Public views are not persisted *for the viewer*
  const isTemporaryPath = !loading && !!temporaryPathId && !persistentPathId && !isPublicView; // Public views aren't temporary generation results
  
  // Determine the correct pathId to use for component interactions
  let derivedPathId = null;
  const currentEntryId = localEntryId || entryId || persistentPathId;
  
  if (!loading && learningPath) { 
    if (isTemporaryPath) {
      derivedPathId = temporaryPathId;
    } else {
      derivedPathId = currentEntryId; 
    }
    // For public view, derivedPathId will be the persistentPathId from the loaded data
    if (isPublicView && learningPath?.path_id) {
      derivedPathId = learningPath.path_id;
    }
    if (!derivedPathId) {
      console.warn('Could not reliably determine pathId for LearningPathView interactions.');
    }
  }
  
  // Extract the actual path data object (core content: modules, submodules, etc.)
  // The top-level learningPath state holds the full response (topic, is_public, share_id, path_data, etc.)
  const actualPathData = learningPath?.path_data || learningPath || {}; 

  // Extract top-level info directly from learningPath state
  const topic = learningPath?.topic || 'Loading Topic...'; // Use directly from learningPath
  const topicResources = learningPath?.topic_resources || []; // Use directly from learningPath
  const isPublic = learningPath?.is_public || false;
  // Rename to avoid conflict with shareId from useParams
  const loadedShareId = learningPath?.share_id || null; 
  
  // --- NEW: Determine correct shareId for header copy button ---
  const { shareId: shareIdFromParams } = useParams(); // Get shareId specifically from params
  const relevantShareIdForHeader = isPublicView ? shareIdFromParams : loadedShareId;
  // --- End NEW ---

  // --- NEW: Callback to select a submodule and update display type ---
  const selectSubmodule = useCallback((modIdx, subIdx) => {
    setActiveModuleIndex(modIdx);
    setActiveSubmoduleIndex(subIdx);
    setContentPanelDisplayType('submodule');
    setActiveTab(0); // Default to content tab
    if (contentPanelRef.current) {
      contentPanelRef.current.scrollTop = 0;
    }
  }, [setActiveModuleIndex, setActiveSubmoduleIndex, setContentPanelDisplayType, setActiveTab]);

  // --- NEW: Callback to select module resources ---
  const handleSelectModuleResources = useCallback((moduleIndex) => {
    setActiveModuleIndex(moduleIndex);
    setActiveSubmoduleIndex(null); // No specific submodule
    setContentPanelDisplayType('module_resources');
    setActiveTab(0); // Reset tab, ContentPanel will adapt
    if (contentPanelRef.current) {
      contentPanelRef.current.scrollTop = 0;
    }
  }, [setActiveModuleIndex, setActiveSubmoduleIndex, setContentPanelDisplayType, setActiveTab]);


  // Effect to set initial active module/submodule from last visited or default
  useEffect(() => {
      if (initialLoadComplete && actualPathData && actualPathData.modules && actualPathData.modules.length > 0) {
          const isValidLastVisited = 
              lastVisitedModuleIdx !== null && lastVisitedModuleIdx >= 0 && lastVisitedModuleIdx < actualPathData.modules.length &&
              lastVisitedSubmoduleIdx !== null && lastVisitedSubmoduleIdx >= 0 && 
              actualPathData.modules[lastVisitedModuleIdx]?.submodules?.length > lastVisitedSubmoduleIdx;

          if (isValidLastVisited) {
              console.log('Setting initial navigation from last visited:', lastVisitedModuleIdx, lastVisitedSubmoduleIdx);
              selectSubmodule(lastVisitedModuleIdx, lastVisitedSubmoduleIdx);
          } else if (activeModuleIndex === null && activeSubmoduleIndex === null) { // Only if not already set by other means (e.g. tutorial) and nothing is active
              console.log('Setting initial navigation to default (0, 0)');
              const firstModuleSubmodules = actualPathData.modules[0]?.submodules;
              if (firstModuleSubmodules && firstModuleSubmodules.length > 0) {
                  selectSubmodule(0, 0);
              } else if (actualPathData.modules[0]) { // If first module exists but no submodules
                  setActiveModuleIndex(0);
                  setActiveSubmoduleIndex(null); 
                  // Check if module has resources and set display type accordingly
                  setContentPanelDisplayType(actualPathData.modules[0].resources?.length > 0 ? 'module_resources' : 'submodule');
              }
          }
      } else if (initialLoadComplete && (!actualPathData || !actualPathData.modules || actualPathData.modules.length === 0)) {
          setActiveModuleIndex(null);
          setActiveSubmoduleIndex(null);
          setContentPanelDisplayType('submodule'); // Reset display type
      }
  // Depend on selectSubmodule to avoid stale closures. activeModuleIndex removed to prevent re-running on user navigation.
  }, [initialLoadComplete, actualPathData, lastVisitedModuleIdx, lastVisitedSubmoduleIdx, selectSubmodule, setActiveModuleIndex, setActiveSubmoduleIndex, setContentPanelDisplayType]);

  // Effect to update the last visited position on the backend when navigation changes
  useEffect(() => {
    // Only run if the path is persisted, navigation indices are valid, and we are viewing a submodule
    if (!isPublicView && currentEntryId && activeModuleIndex !== null && activeSubmoduleIndex !== null && contentPanelDisplayType === 'submodule') {
      console.log(`Updating last visited API: M ${activeModuleIndex}, S ${activeSubmoduleIndex}`);
      apiService.updateLastVisited(currentEntryId, activeModuleIndex, activeSubmoduleIndex)
        .catch(warn => console.warn("Failed to update last visited position:", warn));
    }
  }, [currentEntryId, activeModuleIndex, activeSubmoduleIndex, isPublicView, contentPanelDisplayType]);

  // Callback for when save is confirmed in the action hook
  const handleSaveSuccess = useCallback((result) => {
    if (result?.entryId) {
      setLocalDetailsHaveBeenSet(true);
      setLocalEntryId(result.entryId);
    }
  }, []);

  // Setup actions for the course
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
  
  // --- NEW: Setup sharing actions --- 
  const { 
    handleTogglePublic, 
    handleCopyShareLink 
  } = usePathSharingActions(showNotification, refreshData);

  // --- NEW: Handler for Copying Public Path ---
  const handleCopyToHistory = async () => {
    const publicShareId = shareId; 
    if (!publicShareId) {
      showNotification('Cannot copy course: Missing share ID.', 'error');
      return;
    }
    if (!isAuthenticated) {
       showNotification('Please log in to save this course to your history.', 'warning');
       return;
    }

    setIsCopying(true); 
    showNotification('Copying course to your history...', 'info');
    try {
      const newPathData = await apiService.copyPublicPath(publicShareId);
      if (newPathData && newPathData.path_id) {
        showNotification('Course successfully copied to your history!', 'success');
        navigate(`/history/${newPathData.path_id}`); 
      } else {
        throw new Error('Copy operation response did not contain a new path ID.');
      }
    } catch (error) {
      console.error("Failed to copy public course:", error);
      if (error.response?.status === 409) {
          showNotification(error.message || 'You already have a copy of this course.', 'warning');
      } else {
          showNotification(`Failed to copy course: ${error.message || 'Please try again.'}`, 'error');
      }
    }
    finally {
      setIsCopying(false); 
    }
  };

  // Handler to toggle progress state
  const handleToggleProgress = useCallback(async (modIndex, subIndex) => {
    if (isPublicView) {
      console.warn('Cannot toggle progress in public view.');
      return;
    }

    if (!currentEntryId) {
      showNotification('Please save the course to track progress.', 'warning');
      return;
    }

    const progressKey = `${modIndex}_${subIndex}`;
    const currentCompletionStatus = progressMap[progressKey] || false;
    const newCompletionStatus = !currentCompletionStatus;

    setProgressMap(prevMap => ({
      ...prevMap,
      [progressKey]: newCompletionStatus
    }));

    try {
      await apiService.updateSubmoduleProgress(currentEntryId, modIndex, subIndex, newCompletionStatus);
      console.log(`Progress updated successfully for ${progressKey} to ${newCompletionStatus}`);
    } catch (error) {
      console.error(`Failed to update progress for ${progressKey}:`, error);
      setProgressMap(prevMap => ({
        ...prevMap,
        [progressKey]: currentCompletionStatus 
      }));
      showNotification(`Failed to update progress for submodule ${modIndex + 1}.${subIndex + 1}.`, 'error');
    }
  }, [currentEntryId, progressMap, setProgressMap, showNotification, isPublicView]);

  // Adjust action handlers
  const handleDownloadJSONAdjusted = () => {
      if (!actualPathData) return; 
      try {
          const json = JSON.stringify(actualPathData, null, 2);
          const blob = new Blob([json], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          const fileName = topic 
              ? `course_${topic.replace(/\s+/g, '_').substring(0, 30)}.json`
              : 'course.json';
          a.download = fileName;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
          if (showNotification) {
              showNotification('Course downloaded successfully', 'success');
          } else {
              console.log('Course downloaded successfully');
          }
      } catch (err) {
          console.error('Error downloading JSON:', err);
          if (showNotification) {
              showNotification('Failed to download course', 'error');
          } else {
              console.error('Failed to download course');
          }
      }
  };

  const handleDownloadPDFWithUpdate = async () => {
    await handleDownloadPDF(); 
  };

  // Show dismissible alert on first view of a newly generated path
  useEffect(() => {
    const alertDismissedKey = `mapmylearn_alert_dismissed_${taskId}`;
    if (!isPublicView && !loading && !error && taskId && !isFromHistory && !sessionStorage.getItem(alertDismissedKey)) {
      setShowFirstViewAlert(true);
    }
  }, [loading, error, taskId, isFromHistory, isPublicView]);

  const handleDismissFirstViewAlert = () => {
    const alertDismissedKey = `mapmylearn_alert_dismissed_${taskId}`;
    sessionStorage.setItem(alertDismissedKey, 'true');
    setShowFirstViewAlert(false);
  };

  // Navigation Handler for ContentPanel and MobileBottomNavigation
  const handleNavigation = useCallback((direction) => {
    if (!actualPathData || !actualPathData.modules || actualPathData.modules.length === 0 || activeModuleIndex === null) {
        return;
    }

    let currentModIndex = activeModuleIndex;
    let currentSubIdx = activeSubmoduleIndex; // Can be null if coming from module_resources

    const numModules = actualPathData.modules.length;
    const currentModuleData = actualPathData.modules[currentModIndex];
    const numSubmodulesInCurrentModule = currentModuleData?.submodules?.length || 0;

    let nextModIndex = currentModIndex;
    let nextSubIdx = currentSubIdx;

    if (direction === 'prev') {
        if (currentSubIdx !== null && currentSubIdx > 0) {
            nextSubIdx = currentSubIdx - 1;
        } else if (currentSubIdx === null && numSubmodulesInCurrentModule > 0) { // From module_resources, go to last submodule of current module
            nextSubIdx = numSubmodulesInCurrentModule - 1;
        } else if (currentModIndex > 0) { // Go to previous module
            nextModIndex = currentModIndex - 1;
            const prevModuleData = actualPathData.modules[nextModIndex];
            nextSubIdx = (prevModuleData?.submodules?.length || 1) - 1;
            if (nextSubIdx < 0) nextSubIdx = 0; // Ensure non-negative for modules with 0 submodules
        } else {
            return; // Already at the very beginning
        }
    } else if (direction === 'next') {
        if (currentSubIdx !== null && currentSubIdx < numSubmodulesInCurrentModule - 1) {
            nextSubIdx = currentSubIdx + 1;
        } else if (currentSubIdx === null && numSubmodulesInCurrentModule > 0) { // From module_resources, go to first submodule of current module
            nextSubIdx = 0;
        } else if (currentModIndex < numModules - 1) { // Go to next module
            nextModIndex = currentModIndex + 1;
            nextSubIdx = 0;
        } else {
            return; // Already at the very end
        }
    } else if (direction === 'nextModule') {
        if (currentModIndex < numModules - 1) {
            nextModIndex = currentModIndex + 1;
            nextSubIdx = 0;
        } else {
            return; // Already at the last module
        }
    }

    // Check if the target submodule exists
    const targetModule = actualPathData.modules[nextModIndex];
    if (targetModule && targetModule.submodules && targetModule.submodules[nextSubIdx]) {
        selectSubmodule(nextModIndex, nextSubIdx);
    } else if (targetModule) { // Target module exists, but submodule doesn't (e.g. module with 0 submodules)
        // In this case, maybe we should navigate to the module's resources if available?
        // For now, this will result in ContentPanel showing its placeholder for missing submodule.
        // Or we can call handleSelectModuleResources if the target module has resources.
        // This part needs careful consideration of desired UX.
        // Let's stick to selecting the module and letting ContentPanel decide.
        setActiveModuleIndex(nextModIndex);
        setActiveSubmoduleIndex(null); // No valid submodule to select
        setContentPanelDisplayType('submodule'); // ContentPanel will show placeholder
        setActiveTab(0);
        if (contentPanelRef.current) contentPanelRef.current.scrollTop = 0;
    }

  }, [actualPathData, activeModuleIndex, activeSubmoduleIndex, selectSubmodule, setActiveModuleIndex, setActiveSubmoduleIndex, setContentPanelDisplayType, setActiveTab]);


  // Mobile Navigation Handlers
  const handleMobileNavToggle = () => {
    setMobileNavOpen(!mobileNavOpen);
  };

  const handleMobileNavClose = () => {
    setMobileNavOpen(false);
  };

  const handleSubmoduleSelectFromDrawer = (modIndex, subIndex) => {
     // selectSubmodule is called by ModuleNavigationColumn's item click
     handleMobileNavClose();
  };

  // Calculate current submodule and available tabs
  const modules = actualPathData?.modules || [];
  const totalModules = modules.length;
  const currentModule = (activeModuleIndex !== null && activeModuleIndex >= 0 && activeModuleIndex < totalModules)
                        ? modules[activeModuleIndex]
                        : null;
  const totalSubmodulesInModule = currentModule?.submodules?.length || 0;
  
  // Current submodule is only valid if displayType is 'submodule'
  const currentSubmodule = (contentPanelDisplayType === 'submodule' && currentModule && activeSubmoduleIndex !== null && activeSubmoduleIndex >= 0 && activeSubmoduleIndex < totalSubmodulesInModule)
                         ? currentModule.submodules[activeSubmoduleIndex]
                         : null;

  const availableTabs = useMemo(() => {
    if (!currentSubmodule) return []; // No tabs if no submodule is active (e.g. viewing module resources)

    const hasQuiz = currentSubmodule.quiz_questions && currentSubmodule.quiz_questions.length > 0;
    const hasResources = currentSubmodule.resources && currentSubmodule.resources.length > 0;

    let tabIndexCounter = 0;
    const tabs = [
        { index: tabIndexCounter++, label: 'Content', icon: <MenuBookIcon />, tooltip: "View submodule content", dataTut: 'content-panel-tab-content' },
        ...(hasQuiz ? [{ index: tabIndexCounter++, label: 'Quiz', icon: <FitnessCenterIcon />, tooltip: helpTexts.submoduleTabQuiz, dataTut: 'content-panel-tab-quiz' }] : []),
        ...(hasResources ? [{ index: tabIndexCounter++, label: 'Resources', icon: <CollectionsBookmarkIcon />, tooltip: "View submodule resources", dataTut: 'content-panel-tab-resources' }] : []),
        { index: tabIndexCounter++, label: 'Chat', icon: <QuestionAnswerIcon />, tooltip: helpTexts.submoduleTabChat, dataTut: 'content-panel-tab-chat' },
        { index: tabIndexCounter++, label: 'Audio', icon: <GraphicEqIcon />, tooltip: helpTexts.submoduleTabAudio(AUDIO_CREDIT_COST), dataTut: 'content-panel-tab-audio' },
    ];
    return tabs;
  }, [currentSubmodule]); // Depends only on currentSubmodule

  // Effect to reset activeTab if it becomes invalid
  useEffect(() => {
      if (availableTabs.length > 0 && activeTab >= availableTabs.length) {
          setActiveTab(0); 
      }
      else if (availableTabs.length === 0 && activeTab !== 0) {
          setActiveTab(0);
      }
  }, [availableTabs, activeTab]);

  // Effect to check for first visit and start tutorial
  useEffect(() => {
    const tutorialCompleted = localStorage.getItem(TUTORIAL_STORAGE_KEY);
    if (!loading && !tutorialCompleted) {
      setTimeout(() => setRunTutorial(true), 500); 
    }
  }, [loading]); 

  // --- Tutorial Logic ---
  const startTutorial = () => {
    setTutorialStepIndex(0);
    setRunTutorial(true);
  };

  const handleJoyrideCallback = (data) => {
    const { action, index, status, type } = data;

    if ([EVENTS.STEP_AFTER, EVENTS.TARGET_NOT_FOUND].includes(type)) {
      setTutorialStepIndex(index + (action === ACTIONS.PREV ? -1 : 1));
    } else if ([STATUS.FINISHED, STATUS.SKIPPED].includes(status)) {
      setRunTutorial(false);
      setTutorialStepIndex(0);
      localStorage.setItem(TUTORIAL_STORAGE_KEY, 'true');
    }
    console.log('Joyride callback:', data);
  };

  // Define Tutorial Steps
  const getTutorialSteps = (isMobile) => {
    const findTabIndex = (dataTut) => availableTabs.findIndex(t => t.dataTut === dataTut);

    const commonSteps = [
      {
        target: '[data-tut="lp-header"]',
        content: 'Welcome to your Course! This header shows the main topic.',
        placement: 'bottom',
        disableBeacon: true,
      },
      // Add step for topic resources if they exist
      ...(topicResources && topicResources.length > 0 ? [{
        target: '[data-tut="topic-resources-section"]',
        content: 'Global resources for the entire course are listed here. You can expand or collapse this section.',
        placement: 'bottom',
        disableBeacon: true,
      }] : []),
    ];

    const desktopSteps = [
      ...commonSteps,
      {
        target: '[data-tut="module-navigation-column"]',
        content: 'On the left, you have the modules. Click a module to see its submodules and any module-specific resources.',
        placement: 'right',
        disableBeacon: true,
      },
      {
        target: '[data-tut="module-item-0"]',
        content: 'Click here to expand the first module.',
        placement: 'right',
        disableBeacon: true,
        callback: () => setActiveModuleIndex(0), // Just expand, don't select submodule yet.
      },
      // Assuming module 0 has submodules for this step
      ...(actualPathData?.modules?.[0]?.submodules?.length > 0 ? [{
        target: '[data-tut="submodule-item-0-0"]',
        content: 'Now click the first submodule to view its content.',
        placement: 'right',
        disableBeacon: true,
        callback: () => selectSubmodule(0, 0)
      }] : []),
      // Assuming module 0 has resources for this step (can be combined or conditional)
      ...(actualPathData?.modules?.[0]?.resources?.length > 0 ? [{
        target: '[data-tut="module-resources-item-0"]', // Ensure this data-tut is added in ModuleNavigationColumn
        content: 'Modules can also have their own resources. Click here to view them.',
        placement: 'right',
        disableBeacon: true,
        callback: () => handleSelectModuleResources(0)
      }] : []),
      {
        target: '[data-tut="content-panel"]',
        content: 'The main content area shows details for the selected submodule or module resources.',
        placement: 'left',
        disableBeacon: true,
         // Add a delay or ensure submodule is selected before this step if needed
        preStepCallback: () => { // Ensure a submodule is selected if previous step was module resources
          if (contentPanelDisplayType === 'module_resources' && actualPathData?.modules?.[0]?.submodules?.length > 0) {
            selectSubmodule(0,0);
          }
        }
      },
      {
        target: '[data-tut="content-panel-tabs"]',
        content: 'If viewing a submodule, use these tabs to explore different aspects of it.',
        placement: 'bottom',
        disableBeacon: true,
        // Condition: Only show if a submodule is active and tabs are present
        condition: () => contentPanelDisplayType === 'submodule' && availableTabs.length > 0,
      },
      {
        target: '[data-tut="content-panel-tab-content"]',
        content: 'This is the main learning material for the submodule.',
        placement: 'top',
        disableBeacon: true,
        condition: () => contentPanelDisplayType === 'submodule' && availableTabs.some(t => t.dataTut === 'content-panel-tab-content'),
        callback: () => setActiveTab(findTabIndex('content-panel-tab-content') ?? 0)
      },
      ...(availableTabs.some(t => t.dataTut === 'content-panel-tab-quiz') ? [{
        target: '[data-tut="content-panel-tab-quiz"]',
        content: 'Test your understanding with a short quiz.',
        placement: 'top',
        disableBeacon: true,
        condition: () => contentPanelDisplayType === 'submodule',
        callback: () => setActiveTab(findTabIndex('content-panel-tab-quiz'))
      }] : []),
      ...(availableTabs.some(t => t.dataTut === 'content-panel-tab-resources') ? [{
        target: '[data-tut="content-panel-tab-resources"]',
        content: 'Find additional resources like articles or videos here.',
        placement: 'top',
        disableBeacon: true,
        condition: () => contentPanelDisplayType === 'submodule',
        callback: () => setActiveTab(findTabIndex('content-panel-tab-resources'))
      }] : []),
       {
        target: '[data-tut="content-panel-tab-chat"]',
        content: 'Chat with an AI assistant about this specific submodule.',
        placement: 'top',
        disableBeacon: true,
        condition: () => contentPanelDisplayType === 'submodule',
        callback: () => setActiveTab(findTabIndex('content-panel-tab-chat'))
      },
       {
        target: '[data-tut="content-panel-tab-audio"]',
        content: 'Generate an audio version of the submodule content (costs credits!).',
        placement: 'top',
        disableBeacon: true,
        condition: () => contentPanelDisplayType === 'submodule',
        callback: () => setActiveTab(findTabIndex('content-panel-tab-audio'))
      },
      {
        target: '[data-tut="content-panel-progress-checkbox-container"]',
        content: 'Once you\'ve finished a submodule, check this box to mark it complete!',
        placement: 'top',
        disableBeacon: true,
        condition: () => contentPanelDisplayType === 'submodule',
        callback: () => setActiveTab(findTabIndex('content-panel-tab-content') ?? 0) 
      },
      {
        target: '[data-tut="progress-checkbox-0-0"]',
        content: 'You can also mark submodules complete directly in the navigation list.',
        placement: 'right',
        disableBeacon: true,
        condition: () => actualPathData?.modules?.[0]?.submodules?.length > 0,
      },
      {
        target: '[data-tut="content-panel-prev-button"]',
        content: 'Use these buttons to navigate between submodules...',
        placement: 'bottom',
        disableBeacon: true,
        condition: () => contentPanelDisplayType === 'submodule',
      },
      {
        target: '[data-tut="content-panel-next-module-button"]',
        content: '...or jump to the next module entirely.',
        placement: 'bottom',
        disableBeacon: true,
        condition: () => contentPanelDisplayType === 'submodule',
      },
      {
        target: '[data-tut="save-path-button"]',
        content: 'Remember to save your course to track progress and access it later!',
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
        callback: () => setMobileNavOpen(true) 
      },
      {
        target: '[data-tut="module-navigation-column"]',
        content: 'Select modules, submodules, or module resources here. Tap the first module to expand it.',
        placement: 'right',
        isFixed: true, 
        disableBeacon: true,
        callback: () => setActiveModuleIndex(0) 
      },
      // Assuming module 0 has submodules
      ...(actualPathData?.modules?.[0]?.submodules?.length > 0 ? [{
        target: '[data-tut="submodule-item-0-0"]',
        content: 'Now tap the first submodule to view it and close the drawer.',
        placement: 'right',
        isFixed: true,
        disableBeacon: true,
        callback: () => { 
          selectSubmodule(0, 0);
          setMobileNavOpen(false);
        }
      }] : []),
      // Assuming module 0 has resources
      ...(actualPathData?.modules?.[0]?.resources?.length > 0 && !(actualPathData?.modules?.[0]?.submodules?.length > 0) ? [{ // Show if no submodules but has resources
        target: '[data-tut="module-resources-item-0"]',
        content: 'This module has resources. Tap to view them and close the drawer.',
        placement: 'right',
        isFixed: true,
        disableBeacon: true,
        callback: () => {
          handleSelectModuleResources(0);
          setMobileNavOpen(false);
        }
      }] : []),
      {
        target: '[data-tut="content-panel"]',
        content: 'The main content for the selected item is shown here.',
        placement: 'top',
        disableBeacon: true,
         preStepCallback: () => { 
          if (contentPanelDisplayType === 'module_resources' && actualPathData?.modules?.[0]?.submodules?.length > 0) {
            selectSubmodule(0,0);
          }
        }
      },
      {
        target: '[data-tut="mobile-tab-buttons"]',
        content: 'If viewing a submodule, use these icons to switch between Content, Quiz, etc.',
        placement: 'top',
        disableBeacon: true,
        condition: () => contentPanelDisplayType === 'submodule' && availableTabs.length > 0,
      },
      {
        target: '[data-tut="content-panel-tab-content"]', // This is inside ContentPanel, but for mobile, tabs are at bottom
        content: 'This is the main learning material (when a submodule is selected).',
        placement: 'top',
        disableBeacon: true,
        condition: () => contentPanelDisplayType === 'submodule' && availableTabs.some(t => t.dataTut === 'content-panel-tab-content'),
        callback: () => setActiveTab(findTabIndex('content-panel-tab-content') ?? 0)
      },
      {
        target: '[data-tut="content-panel-progress-checkbox-container"]',
        content: 'Mark the submodule complete here when you\'re done.',
        placement: 'top',
        disableBeacon: true,
        condition: () => contentPanelDisplayType === 'submodule',
      },
      {
        target: '[data-tut="mobile-prev-button"]', // Actually wraps both prev/next
        content: 'Tap these buttons to navigate to the previous or next submodule.',
        placement: 'top',
        disableBeacon: true,
        // condition: () => contentPanelDisplayType === 'submodule', // Navigation should work even from module_resources view
      },
       {
        target: '[data-tut="save-path-button"]',
        content: 'Remember to save your course to track progress and access it later!',
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

  const tutorialSteps = useMemo(() => getTutorialSteps(isMobileLayout), [isMobileLayout, availableTabs, actualPathData, topicResources, contentPanelDisplayType, selectSubmodule, handleSelectModuleResources, setActiveModuleIndex]);

  if (loading) {
    return (
      <LoadingState 
        topic={learningPath?.topic || sessionStorage.getItem('currentTopic')} 
      /> 
    );
  }
  
  if (error) {
    return (
      <ErrorState 
        error={error || 'An error occurred'} 
        onHomeClick={handleHomeClick}
        onNewLearningPathClick={handleNewLearningPathClick}
      />
    );
  }
  
  return (
    <Container 
      maxWidth="xl" 
      sx={{ 
        pt: { xs: 2, md: 3 }, 
        pb: { 
          xs: `calc(${theme.spacing(8)} + env(safe-area-inset-bottom, 0px))`, // 8 for bottom nav
          md: theme.spacing(4) 
        }, 
        display: 'flex', 
        flexDirection: 'column', 
        flexGrow: 1 
      }}
    > 
      {showFirstViewAlert && (
        <Alert 
          severity="info" 
          sx={{ mb: 2, flexShrink: 0 }} 
          onClose={handleDismissFirstViewAlert}
        >
          <AlertTitle>Your Course is Ready!</AlertTitle>
          {helpTexts.lpFirstViewAlert}
        </Alert>
      )}

      {isPublicView && !isAuthenticated && (
        <Alert 
          severity="info" 
          sx={{ mb: 2, flexShrink: 0 }} 
          action={
            <Box>
              <Button color="inherit" size="small" onClick={() => navigate('/login')} startIcon={<LoginIcon/>}>
                Log In
              </Button>
              <Button color="inherit" size="small" onClick={() => navigate('/register')}>
                Sign Up
              </Button>
            </Box>
          }
        >
          <AlertTitle>Explore More!</AlertTitle>
          Log in or sign up to save this course, track your progress, and create your own learning journeys.
        </Alert>
      )}
      
      {learningPath && (
        <>
          <Box sx={{ flexShrink: 0, mb: { xs: 2, md: 3 } }}> 
             <LearningPathHeader 
               topic={topic} 
               detailsHaveBeenSet={localDetailsHaveBeenSet} 
               isPdfReady={isPdfReady} 
               onDownload={handleDownloadJSONAdjusted} 
               onDownloadPDF={handleDownloadPDFWithUpdate}
               onSaveToHistory={handleSaveToHistory} 
               onNewLearningPath={handleNewLearningPathClick}
               onOpenMobileNav={handleMobileNavToggle} 
               showMobileNavButton={isMobileLayout} 
               progressMap={progressMap}
               actualPathData={actualPathData} 
               onStartTutorial={startTutorial} 
               isPublicView={isPublicView} 
               isPublic={isPublic} 
               shareId={relevantShareIdForHeader} 
               entryId={currentEntryId} 
               isLoggedIn={isAuthenticated} 
               onTogglePublic={() => handleTogglePublic(currentEntryId, !isPublic)} 
               onCopyShareLink={handleCopyShareLink} 
               onCopyToHistory={handleCopyToHistory} 
               isCopying={isCopying} 
             />
             {/* --- NEW: Topic Resources Section --- */}
              {topicResources && topicResources.length > 0 && (
                <Box sx={{ mt: 2 }} data-tut="topic-resources-section">
                  <ResourcesSection
                    resources={topicResources}
                    title="Overall Course Resources"
                    type="topic"
                    collapsible={true}
                    expanded={false} // Default to collapsed
                    compact={false}
                  />
                </Box>
              )}
          </Box>

          <Box sx={{ flexGrow: 1, overflow: 'hidden', position: 'relative' }}> 
            {isMobileLayout ? (
               <> 
                  <Box sx={{ height: '100%' }}> 
                      <ContentPanel
                         ref={contentPanelRef}
                         sx={{ height: '100%' }}
                         displayType={contentPanelDisplayType} // Pass new prop
                         module={currentModule}
                         moduleIndex={activeModuleIndex}
                         submodule={currentSubmodule} // Will be null if displayType is 'module_resources'
                         submoduleIndex={activeSubmoduleIndex} // Will be null if displayType is 'module_resources'
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
                         isPublicView={isPublicView} 
                      />
                  </Box>

                  <Drawer
                     anchor="left"
                     open={mobileNavOpen}
                     onClose={handleMobileNavClose}
                     ModalProps={{ keepMounted: true }}
                     PaperProps={{ sx: { width: DRAWER_WIDTH } }}
                  >
                     <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
                         <Typography variant="h6">Modules</Typography>
                     </Box>
                     <ModuleNavigationColumn
                         modules={actualPathData?.modules || []} 
                         activeModuleIndex={activeModuleIndex}
                         setActiveModuleIndex={setActiveModuleIndex}
                         activeSubmoduleIndex={activeSubmoduleIndex}
                         selectSubmodule={selectSubmodule}
                         onSelectModuleResources={handleSelectModuleResources}
                         contentPanelDisplayType={contentPanelDisplayType}
                         progressMap={progressMap}
                         onToggleProgress={handleToggleProgress}
                         isPublicView={isPublicView}
                         onSubmoduleSelect={handleSubmoduleSelectFromDrawer} 
                      />
                  </Drawer>
                  
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
                     // Pass display type to potentially adjust its behavior if needed (e.g. disable nav buttons)
                     contentPanelDisplayType={contentPanelDisplayType}
                  />
               </>
            ) : (
               <Grid container spacing={{ xs: 0, md: 2 }} sx={{ height: '100%', flexGrow: 1 }}> 
                  <Grid item xs={12} md={4} sx={{ 
                     height: { xs: 'auto', md: '100%' }, 
                     pb: { xs: 2, md: 0 } 
                  }}> 
                     <ModuleNavigationColumn
                        modules={actualPathData?.modules || []} 
                        activeModuleIndex={activeModuleIndex}
                        setActiveModuleIndex={setActiveModuleIndex}
                        activeSubmoduleIndex={activeSubmoduleIndex}
                        selectSubmodule={selectSubmodule}
                        onSelectModuleResources={handleSelectModuleResources}
                        contentPanelDisplayType={contentPanelDisplayType}
                        progressMap={progressMap}
                        onToggleProgress={handleToggleProgress}
                        isPublicView={isPublicView}
                     />
                  </Grid>
                  <Grid item xs={12} md={8} sx={{ /* No height/overflow needed here */ }}> 
                     <ContentPanel
                        ref={contentPanelRef}
                        sx={{ height: '100%' }}
                        displayType={contentPanelDisplayType} // Pass new prop
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
                        isPublicView={isPublicView}
                     />
                  </Grid>
               </Grid>
            )}
          </Box>
        </>
      )}
      
      <Joyride 
        steps={tutorialSteps}
        run={runTutorial}
        stepIndex={tutorialStepIndex}
        callback={handleJoyrideCallback}
        continuous={true}
        showProgress={true}
        showSkipButton={true}
        scrollToFirstStep={true}
        styles={{
          options: {
            arrowColor: theme.palette.background.paper,
            backgroundColor: theme.palette.background.paper,
            overlayColor: 'rgba(0, 0, 0, 0.6)',
            primaryColor: theme.palette.primary.main,
            textColor: theme.palette.text.primary,
            zIndex: theme.zIndex.tooltip + 1, 
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

      {!isPublicView && (
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
      )}
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
              bottom: { xs: `calc(${theme.spacing(2)} + env(safe-area-inset-bottom, 0px))`, sm: theme.spacing(3) }, // Adjust for bottom nav on mobile
            }}
          >
            <Alert 
              onClose={handleNotificationClose} 
              severity={notification.severity}
              elevation={6} 
              variant="filled" 
              sx={{ width: '100%' }} 
            >
              {notification.message}
            </Alert>
          </Snackbar>
      )}
    </Container>
  );
}

LearningPathView.propTypes = {
  source: PropTypes.oneOf(['history', 'public', null, undefined]),
};

export default LearningPathView;