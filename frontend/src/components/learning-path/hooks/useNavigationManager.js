import { useCallback, useEffect } from 'react';
import * as apiService from '../../../services/api';
import { calculateNextNavigation } from '../utils/navigationLogic';
import { DISPLAY_TYPES } from '../constants/viewConstants';

/**
 * Comprehensive navigation management hook
 * @param {Object} params Navigation parameters
 * @returns {Object} Navigation handlers and utilities
 */
const useNavigationManager = ({
  // Navigation state
  activeModuleIndex,
  activeSubmoduleIndex,
  contentPanelDisplayType,
  setActiveModuleIndex,
  setActiveSubmoduleIndex,
  setContentPanelDisplayType,
  setActiveTab,
  selectSubmodule,
  selectModuleResources,
  scrollToTop,
  
  // Path data
  actualPathData,
  
  // Progress and persistence
  currentEntryId,
  isPublicView,
  
  // Notifications
  showNotification
}) => {
  
  // Main navigation handler
  const handleNavigation = useCallback((direction) => {
    const nextNav = calculateNextNavigation({
      direction,
      currentModuleIndex: activeModuleIndex,
      currentSubmoduleIndex: activeSubmoduleIndex,
      contentPanelDisplayType,
      pathData: actualPathData
    });

    if (!nextNav) return; // No valid navigation

    const { moduleIndex, submoduleIndex, displayType } = nextNav;
    
    // Check if target exists and navigate appropriately
    const targetModule = actualPathData.modules[moduleIndex];
    if (targetModule && targetModule.submodules && targetModule.submodules[submoduleIndex]) {
      selectSubmodule(moduleIndex, submoduleIndex);
    } else if (targetModule) {
      // Module exists but submodule doesn't, handle gracefully
      setActiveModuleIndex(moduleIndex);
      setActiveSubmoduleIndex(null);
      setContentPanelDisplayType(DISPLAY_TYPES.SUBMODULE);
      setActiveTab(0);
      scrollToTop();
    }
  }, [
    activeModuleIndex,
    activeSubmoduleIndex,
    contentPanelDisplayType,
    actualPathData,
    selectSubmodule,
    setActiveModuleIndex,
    setActiveSubmoduleIndex,
    setContentPanelDisplayType,
    setActiveTab,
    scrollToTop
  ]);

  // Update last visited position on backend
  useEffect(() => {
    if (
      !isPublicView && 
      currentEntryId && 
      activeModuleIndex !== null && 
      activeSubmoduleIndex !== null && 
      contentPanelDisplayType === DISPLAY_TYPES.SUBMODULE
    ) {
      apiService.updateLastVisited(currentEntryId, activeModuleIndex, activeSubmoduleIndex)
        .catch(error => console.warn("Failed to update last visited position:", error));
    }
  }, [currentEntryId, activeModuleIndex, activeSubmoduleIndex, isPublicView, contentPanelDisplayType]);

  // Overview mode handlers
  const handleSelectSubmoduleFromOverview = useCallback((moduleIndex, submoduleIndex) => {
    selectSubmodule(moduleIndex, submoduleIndex);
  }, [selectSubmodule]);

  const handleStartCourse = useCallback(() => {
    if (actualPathData?.modules?.length > 0) {
      const firstModule = actualPathData.modules[0];
      if (firstModule.submodules?.length > 0) {
        selectSubmodule(0, 0);
      }
    }
  }, [actualPathData, selectSubmodule]);

  // Mobile navigation handlers
  const handleSubmoduleSelectFromDrawer = useCallback(() => {
    // This is typically handled by the drawer component itself
    // Just a placeholder for consistency
  }, []);

  return {
    handleNavigation,
    handleSelectSubmoduleFromOverview,
    handleStartCourse,
    handleSubmoduleSelectFromDrawer
  };
};

export default useNavigationManager;
