import { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router';
import { useMediaQuery, useTheme } from '@mui/material';
import { useAuth } from '../../../services/authContext';
import * as apiService from '../../../services/api';

// Custom hooks
import useLearningPathData from './useLearningPathData';
import useLearningPathActions from './useLearningPathActions';
import usePathSharingActions from '../../../hooks/usePathSharingActions';
import useNavigationState from './useNavigationState';
import useViewModeState from './useViewModeState';
import useTabConfiguration from './useTabConfiguration';
import useNavigationManager from './useNavigationManager';
import useTutorialManager from './useTutorialManager';

// Utils
import { getCurrentNavigationData, extractTopicResources, derivePathId } from '../utils/navigationLogic';
import { VIEW_MODES } from '../constants/viewConstants';

/**
 * Main hook that orchestrates all learning path view functionality
 * @param {string} source Source of the learning path
 * @param {Object} options Configuration options
 * @returns {Object} Complete state and handlers for learning path view
 */
const useLearningPathView = (source, options = {}) => {
  const { 
    includeVisualization = true,
    initialViewMode = VIEW_MODES.OVERVIEW,
    enableTutorial = true
  } = options;

  // Router and theme
  const { taskId, entryId, shareId } = useParams();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobileLayout = useMediaQuery(theme.breakpoints.down('md'));
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Auth
  const { user, isAuthenticated } = useAuth();

  // Local state
  const [showFirstViewAlert, setShowFirstViewAlert] = useState(false);
  const [isCopying, setIsCopying] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [initialLoadComplete, setInitialLoadComplete] = useState(false);
  const [localDetailsHaveBeenSet, setLocalDetailsHaveBeenSet] = useState(false);
  const [localEntryId, setLocalEntryId] = useState(null);

  // Load learning path data
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
    isPublicView,
    // CourseView specific fields
    progressMessages,
    isReconnecting,
    retryAttempt
  } = useLearningPathData(source);

  // View mode management
  const viewModeState = useViewModeState(initialViewMode);

  // Navigation state management
  const navigationState = useNavigationState();

  // Initialize local state once loading is done
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

  // Set initial navigation when data loads
  useEffect(() => {
    if (initialLoadComplete && learningPath) {
      const actualPathData = learningPath?.path_data || learningPath || {};
      navigationState.setInitialNavigation(actualPathData, lastVisitedModuleIdx, lastVisitedSubmoduleIdx);
    }
  }, [initialLoadComplete, learningPath, lastVisitedModuleIdx, lastVisitedSubmoduleIdx, navigationState]);

  // Derived data
  const actualPathData = learningPath?.path_data || learningPath || {};
  const topic = learningPath?.topic || 'Loading Topic...';
  const topicResources = useMemo(() => 
    extractTopicResources(learningPath, actualPathData), 
    [learningPath, actualPathData]
  );

  // Current navigation data
  const {
    modules,
    totalModules,
    currentModule,
    totalSubmodulesInModule,
    currentSubmodule
  } = getCurrentNavigationData({
    activeModuleIndex: navigationState.activeModuleIndex,
    activeSubmoduleIndex: navigationState.activeSubmoduleIndex,
    contentPanelDisplayType: navigationState.contentPanelDisplayType,
    pathData: actualPathData
  });

  // Tab configuration
  const tabConfig = useTabConfiguration(currentSubmodule, { includeVisualization });

  // Reset active tab if it becomes invalid
  useEffect(() => {
    if (tabConfig.availableTabs.length > 0 && navigationState.activeTab >= tabConfig.availableTabs.length) {
      navigationState.setActiveTab(0);
    } else if (tabConfig.availableTabs.length === 0 && navigationState.activeTab !== 0) {
      navigationState.setActiveTab(0);
    }
  }, [tabConfig.availableTabs, navigationState.activeTab, navigationState.setActiveTab]);

  // Path identification
  const isPublic = learningPath?.is_public || false;
  const loadedShareId = learningPath?.share_id || null;
  const currentEntryId = localEntryId || entryId || persistentPathId;
  const relevantShareIdForHeader = isPublicView ? shareId : loadedShareId;

  // Derived states
  const isPdfReady = !loading && !!persistentPathId && !isPublicView;
  const isPersisted = (isFromHistory || localDetailsHaveBeenSet || isPdfReady) && !isPublicView;
  const isTemporaryPath = !loading && !!temporaryPathId && !persistentPathId && !isPublicView;
  
  const derivedPathId = derivePathId({
    loading,
    learningPath,
    isTemporaryPath,
    temporaryPathId,
    currentEntryId,
    isPublicView
  });

  // Save success callback
  const handleSaveSuccess = useCallback((result) => {
    if (result?.entryId) {
      setLocalDetailsHaveBeenSet(true);
      setLocalEntryId(result.entryId);
    }
  }, []);

  // Learning path actions
  const learningPathActions = useLearningPathActions(
    actualPathData,
    isFromHistory,
    localDetailsHaveBeenSet,
    currentEntryId,
    taskId,
    temporaryPathId,
    handleSaveSuccess
  );

  // Sharing actions
  const sharingActions = usePathSharingActions(learningPathActions.showNotification, refreshData);

  // Navigation manager
  const navigationManager = useNavigationManager({
    ...navigationState,
    actualPathData,
    currentEntryId,
    isPublicView,
    showNotification: learningPathActions.showNotification
  });

  // Tutorial manager - always call the hook but conditionally use its values
  const tutorialManager = useTutorialManager({
    loading,
    isMobileLayout,
    availableTabs: tabConfig.availableTabs,
    actualPathData,
    topicResources,
    contentPanelDisplayType: navigationState.contentPanelDisplayType,
    selectSubmodule: navigationState.selectSubmodule,
    handleSelectModuleResources: navigationState.selectModuleResources,
    setActiveModuleIndex: navigationState.setActiveModuleIndex,
    setActiveTab: navigationState.setActiveTab,
    setMobileNavOpen,
    findTabIndex: tabConfig.findTabIndex,
    enabled: enableTutorial // Pass enabled flag to the hook
  });

  // Progress management
  const handleToggleProgress = useCallback(async (modIndex, subIndex) => {
    if (isPublicView) {
      console.warn('Cannot toggle progress in public view.');
      return;
    }

    if (!currentEntryId) {
      learningPathActions.showNotification('Please save the course to track progress.', 'warning');
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
    } catch (error) {
      console.error(`Failed to update progress for ${progressKey}:`, error);
      setProgressMap(prevMap => ({
        ...prevMap,
        [progressKey]: currentCompletionStatus
      }));
      learningPathActions.showNotification(`Failed to update progress for submodule ${modIndex + 1}.${subIndex + 1}.`, 'error');
    }
  }, [currentEntryId, progressMap, setProgressMap, learningPathActions.showNotification, isPublicView]);

  // Public path copying
  const handleCopyToHistory = useCallback(async () => {
    const publicShareId = shareId;
    if (!publicShareId) {
      learningPathActions.showNotification('Cannot copy course: Missing share ID.', 'error');
      return;
    }
    if (!isAuthenticated) {
      learningPathActions.showNotification('Please log in to save this course to your history.', 'warning');
      return;
    }

    setIsCopying(true);
    learningPathActions.showNotification('Copying course to your history...', 'info');
    try {
      const newPathData = await apiService.copyPublicPath(publicShareId);
      if (newPathData && newPathData.path_id) {
        learningPathActions.showNotification('Course successfully copied to your history!', 'success');
        navigate(`/history/${newPathData.path_id}`);
      } else {
        throw new Error('Copy operation response did not contain a new path ID.');
      }
    } catch (error) {
      console.error("Failed to copy public course:", error);
      if (error.response?.status === 409) {
        learningPathActions.showNotification(error.message || 'You already have a copy of this course.', 'warning');
      } else {
        learningPathActions.showNotification(`Failed to copy course: ${error.message || 'Please try again.'}`, 'error');
      }
    } finally {
      setIsCopying(false);
    }
  }, [shareId, isAuthenticated, learningPathActions.showNotification, navigate]);

  // First view alert
  useEffect(() => {
    const alertDismissedKey = `mapmylearn_alert_dismissed_${taskId}`;
    if (!isPublicView && !loading && !error && taskId && !isFromHistory && !sessionStorage.getItem(alertDismissedKey)) {
      setShowFirstViewAlert(true);
    }
  }, [loading, error, taskId, isFromHistory, isPublicView]);

  const handleDismissFirstViewAlert = useCallback(() => {
    const alertDismissedKey = `mapmylearn_alert_dismissed_${taskId}`;
    sessionStorage.setItem(alertDismissedKey, 'true');
    setShowFirstViewAlert(false);
  }, [taskId]);

  // Mobile navigation handlers
  const handleMobileNavToggle = useCallback(() => {
    setMobileNavOpen(!mobileNavOpen);
  }, [mobileNavOpen]);

  const handleMobileNavClose = useCallback(() => {
    setMobileNavOpen(false);
  }, []);

  const handleSubmoduleSelectFromDrawer = useCallback(() => {
    handleMobileNavClose();
  }, [handleMobileNavClose]);

  // Overview mode handlers
  const handleSelectSubmoduleFromOverview = useCallback((moduleIndex, submoduleIndex) => {
    navigationState.selectSubmodule(moduleIndex, submoduleIndex);
    viewModeState.switchToFocus();
  }, [navigationState.selectSubmodule, viewModeState.switchToFocus]);

  const handleStartCourse = useCallback(() => {
    if (actualPathData?.modules?.length > 0) {
      const firstModule = actualPathData.modules[0];
      if (firstModule.submodules?.length > 0) {
        navigationState.selectSubmodule(0, 0);
        viewModeState.switchToFocus();
      }
    }
  }, [actualPathData, navigationState.selectSubmodule, viewModeState.switchToFocus]);

  return {
    // Core data
    learningPath,
    actualPathData,
    topic,
    topicResources,
    loading,
    error,

    // Navigation data
    modules,
    totalModules,
    currentModule,
    totalSubmodulesInModule,
    currentSubmodule,
    derivedPathId,

    // State
    ...navigationState,
    ...viewModeState,
    ...tabConfig,
    progressMap,
    setProgressMap,

    // Flags
    isFromHistory,
    isPublicView,
    isTemporaryPath,
    isPdfReady,
    isPersisted,
    isPublic,
    isAuthenticated,
    isMobileLayout,
    isMobile,
    showFirstViewAlert,
    isCopying,
    mobileNavOpen,
    localDetailsHaveBeenSet,

    // IDs
    currentEntryId,
    relevantShareIdForHeader,

    // Actions
    ...learningPathActions,
    ...sharingActions,
    ...navigationManager,
    ...(tutorialManager || {}),

    // Handlers
    selectSubmodule: navigationState.selectSubmodule,
    selectModuleResources: navigationState.selectModuleResources,
    toggleModule: navigationState.toggleModule,
    handleToggleProgress,
    handleCopyToHistory,
    handleDismissFirstViewAlert,
    handleMobileNavToggle,
    handleMobileNavClose,
    handleSubmoduleSelectFromDrawer,
    handleSelectSubmoduleFromOverview,
    handleStartCourse,

    // Theme
    theme,

    // CourseView specific (for compatibility)
    progressMessages,
    isReconnecting,
    retryAttempt
  };
};

export default useLearningPathView;
