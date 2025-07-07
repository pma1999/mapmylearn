import { NAVIGATION_DIRECTIONS, DISPLAY_TYPES } from '../constants/viewConstants';

/**
 * Calculate next navigation position based on direction
 * @param {Object} params Navigation parameters
 * @returns {Object} Next navigation state or null if no change
 */
export const calculateNextNavigation = ({
  direction,
  currentModuleIndex,
  currentSubmoduleIndex,
  contentPanelDisplayType,
  pathData
}) => {
  if (!pathData?.modules?.length || currentModuleIndex === null) {
    return null;
  }

  const numModules = pathData.modules.length;
  const currentModuleData = pathData.modules[currentModuleIndex];
  const numSubmodulesInCurrentModule = currentModuleData?.submodules?.length || 0;

  let nextModIndex = currentModuleIndex;
  let nextSubIdx = currentSubmoduleIndex;

  switch (direction) {
    case NAVIGATION_DIRECTIONS.PREV:
      if (currentSubmoduleIndex !== null && currentSubmoduleIndex > 0) {
        nextSubIdx = currentSubmoduleIndex - 1;
      } else if (currentSubmoduleIndex === null && numSubmodulesInCurrentModule > 0) {
        // From module_resources, go to last submodule of current module
        nextSubIdx = numSubmodulesInCurrentModule - 1;
      } else if (currentModuleIndex > 0) {
        // Go to previous module
        nextModIndex = currentModuleIndex - 1;
        const prevModuleData = pathData.modules[nextModIndex];
        nextSubIdx = Math.max((prevModuleData?.submodules?.length || 1) - 1, 0);
      } else {
        return null; // Already at the beginning
      }
      break;

    case NAVIGATION_DIRECTIONS.NEXT:
      if (currentSubmoduleIndex !== null && currentSubmoduleIndex < numSubmodulesInCurrentModule - 1) {
        nextSubIdx = currentSubmoduleIndex + 1;
      } else if (currentSubmoduleIndex === null && numSubmodulesInCurrentModule > 0) {
        // From module_resources, go to first submodule of current module
        nextSubIdx = 0;
      } else if (currentModuleIndex < numModules - 1) {
        // Go to next module
        nextModIndex = currentModuleIndex + 1;
        nextSubIdx = 0;
      } else {
        return null; // Already at the end
      }
      break;

    case NAVIGATION_DIRECTIONS.NEXT_MODULE:
      if (currentModuleIndex < numModules - 1) {
        nextModIndex = currentModuleIndex + 1;
        nextSubIdx = 0;
      } else {
        return null; // Already at the last module
      }
      break;

    default:
      return null;
  }

  // Validate the target exists
  const targetModule = pathData.modules[nextModIndex];
  if (!targetModule) return null;

  if (nextSubIdx !== null && (!targetModule.submodules || !targetModule.submodules[nextSubIdx])) {
    // Target submodule doesn't exist, adjust navigation
    if (targetModule.submodules?.length > 0) {
      nextSubIdx = 0; // Go to first available submodule
    } else {
      nextSubIdx = null; // No submodules, will show module or placeholder
    }
  }

  return {
    moduleIndex: nextModIndex,
    submoduleIndex: nextSubIdx,
    displayType: nextSubIdx !== null ? DISPLAY_TYPES.SUBMODULE : DISPLAY_TYPES.SUBMODULE
  };
};

/**
 * Get current module and submodule data
 * @param {Object} params Current navigation state
 * @returns {Object} Current module and submodule data
 */
export const getCurrentNavigationData = ({
  activeModuleIndex,
  activeSubmoduleIndex,
  contentPanelDisplayType,
  pathData
}) => {
  const modules = pathData?.modules || [];
  const totalModules = modules.length;
  
  const currentModule = (
    activeModuleIndex !== null && 
    activeModuleIndex >= 0 && 
    activeModuleIndex < totalModules
  ) ? modules[activeModuleIndex] : null;
  
  const totalSubmodulesInModule = currentModule?.submodules?.length || 0;
  
  const currentSubmodule = (
    contentPanelDisplayType === DISPLAY_TYPES.SUBMODULE &&
    currentModule && 
    activeSubmoduleIndex !== null && 
    activeSubmoduleIndex >= 0 && 
    activeSubmoduleIndex < totalSubmodulesInModule
  ) ? currentModule.submodules[activeSubmoduleIndex] : null;

  return {
    modules,
    totalModules,
    currentModule,
    totalSubmodulesInModule,
    currentSubmodule
  };
};

/**
 * Extract topic resources from learning path data
 * @param {Object} learningPath Full learning path data
 * @param {Object} actualPathData Core path data
 * @returns {Array} Topic resources array
 */
export const extractTopicResources = (learningPath, actualPathData) => {
  // Priority 1: Search at root level (newly generated courses)
  if (learningPath?.topic_resources && Array.isArray(learningPath.topic_resources)) {
    return learningPath.topic_resources;
  }
  
  // Priority 2: Search within path_data (history courses)
  if (actualPathData?.topic_resources && Array.isArray(actualPathData.topic_resources)) {
    return actualPathData.topic_resources;
  }
  
  // Fallback: empty array
  return [];
};

/**
 * Determine the correct path ID for component interactions
 * @param {Object} params Path identification parameters
 * @returns {string|null} Derived path ID
 */
export const derivePathId = ({
  loading,
  learningPath,
  isTemporaryPath,
  temporaryPathId,
  currentEntryId,
  isPublicView
}) => {
  if (loading || !learningPath) return null;

  if (isTemporaryPath) {
    return temporaryPathId;
  }

  if (isPublicView && learningPath?.path_id) {
    return learningPath.path_id;
  }

  return currentEntryId;
};
