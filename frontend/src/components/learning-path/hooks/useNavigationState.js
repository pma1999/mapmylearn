import { useState, useCallback, useRef } from 'react';
import { DISPLAY_TYPES } from '../constants/viewConstants';

/**
 * Custom hook to manage navigation state (active module, submodule, tab)
 * @param {Object} options Configuration options
 * @returns {Object} Navigation state and handlers
 */
const useNavigationState = (options = {}) => {
  const { 
    initialModuleIndex = null, 
    initialSubmoduleIndex = null,
    initialTab = 0,
    initialDisplayType = DISPLAY_TYPES.SUBMODULE
  } = options;

  // Core navigation state
  const [activeModuleIndex, setActiveModuleIndex] = useState(initialModuleIndex);
  const [activeSubmoduleIndex, setActiveSubmoduleIndex] = useState(initialSubmoduleIndex);
  const [activeTab, setActiveTab] = useState(initialTab);
  const [contentPanelDisplayType, setContentPanelDisplayType] = useState(initialDisplayType);

  // Ref for content panel scrolling
  const contentPanelRef = useRef(null);

  // Scroll to top helper
  const scrollToTop = useCallback(() => {
    if (contentPanelRef.current) {
      contentPanelRef.current.scrollTop = 0;
    }
  }, []);

  // Select submodule with proper state updates
  const selectSubmodule = useCallback((moduleIndex, submoduleIndex) => {
    setActiveModuleIndex(moduleIndex);
    setActiveSubmoduleIndex(submoduleIndex);
    setContentPanelDisplayType(DISPLAY_TYPES.SUBMODULE);
    setActiveTab(0); // Reset to first tab
    scrollToTop();
  }, [scrollToTop]);

  // Select module resources
  const selectModuleResources = useCallback((moduleIndex) => {
    setActiveModuleIndex(moduleIndex);
    setActiveSubmoduleIndex(null);
    setContentPanelDisplayType(DISPLAY_TYPES.MODULE_RESOURCES);
    setActiveTab(0);
    scrollToTop();
  }, [scrollToTop]);

  // Toggle module expansion
  const toggleModule = useCallback((moduleIndex) => {
    setActiveModuleIndex(prevIndex => (prevIndex === moduleIndex ? null : moduleIndex));
  }, []);

  // Reset navigation state
  const resetNavigation = useCallback(() => {
    setActiveModuleIndex(null);
    setActiveSubmoduleIndex(null);
    setActiveTab(0);
    setContentPanelDisplayType(DISPLAY_TYPES.SUBMODULE);
  }, []);

  // Set initial navigation from last visited or default
  const setInitialNavigation = useCallback((pathData, lastVisitedModuleIdx, lastVisitedSubmoduleIdx) => {
    if (!pathData?.modules?.length) {
      resetNavigation();
      return;
    }

    const isValidLastVisited = 
      lastVisitedModuleIdx !== null && 
      lastVisitedModuleIdx >= 0 && 
      lastVisitedModuleIdx < pathData.modules.length &&
      lastVisitedSubmoduleIdx !== null && 
      lastVisitedSubmoduleIdx >= 0 && 
      pathData.modules[lastVisitedModuleIdx]?.submodules?.length > lastVisitedSubmoduleIdx;

    if (isValidLastVisited) {
      selectSubmodule(lastVisitedModuleIdx, lastVisitedSubmoduleIdx);
    } else if (activeModuleIndex === null && activeSubmoduleIndex === null) {
      const firstModule = pathData.modules[0];
      if (firstModule?.submodules?.length > 0) {
        selectSubmodule(0, 0);
      } else if (firstModule) {
        setActiveModuleIndex(0);
        setActiveSubmoduleIndex(null);
        setContentPanelDisplayType(
          firstModule.resources?.length > 0 ? DISPLAY_TYPES.MODULE_RESOURCES : DISPLAY_TYPES.SUBMODULE
        );
      }
    }
  }, [activeModuleIndex, activeSubmoduleIndex, selectSubmodule, resetNavigation]);

  return {
    // State
    activeModuleIndex,
    activeSubmoduleIndex,
    activeTab,
    contentPanelDisplayType,
    contentPanelRef,

    // Setters
    setActiveModuleIndex,
    setActiveSubmoduleIndex,
    setActiveTab,
    setContentPanelDisplayType,

    // Actions
    selectSubmodule,
    selectModuleResources,
    toggleModule,
    resetNavigation,
    setInitialNavigation,
    scrollToTop
  };
};

export default useNavigationState;
