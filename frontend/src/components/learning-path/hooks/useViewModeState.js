import { useState, useCallback } from 'react';
import { VIEW_MODES } from '../constants/viewConstants';

/**
 * Custom hook to manage view mode state (overview vs focus)
 * @param {string} initialMode Initial view mode
 * @returns {Object} View mode state and handlers
 */
const useViewModeState = (initialMode = VIEW_MODES.OVERVIEW) => {
  const [viewMode, setViewMode] = useState(initialMode);

  // Switch to overview mode
  const switchToOverview = useCallback(() => {
    setViewMode(VIEW_MODES.OVERVIEW);
  }, []);

  // Switch to focus mode
  const switchToFocus = useCallback(() => {
    setViewMode(VIEW_MODES.FOCUS);
  }, []);

  // Toggle between modes
  const toggleViewMode = useCallback(() => {
    setViewMode(current => 
      current === VIEW_MODES.OVERVIEW ? VIEW_MODES.FOCUS : VIEW_MODES.OVERVIEW
    );
  }, []);

  // Check if in specific mode
  const isOverviewMode = viewMode === VIEW_MODES.OVERVIEW;
  const isFocusMode = viewMode === VIEW_MODES.FOCUS;

  return {
    viewMode,
    setViewMode,
    switchToOverview,
    switchToFocus,
    toggleViewMode,
    isOverviewMode,
    isFocusMode
  };
};

export default useViewModeState;
