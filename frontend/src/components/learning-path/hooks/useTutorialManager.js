import { useState, useEffect, useCallback, useMemo } from 'react';
import { ACTIONS, EVENTS, STATUS } from 'react-joyride';
import { TUTORIAL_STORAGE_KEY } from '../constants/viewConstants';

/**
 * Custom hook to manage tutorial state and logic
 * @param {Object} params Tutorial configuration
 * @returns {Object} Tutorial state and handlers
 */
const useTutorialManager = ({
  loading,
  isMobileLayout,
  availableTabs,
  actualPathData,
  topicResources,
  contentPanelDisplayType,
  selectSubmodule,
  handleSelectModuleResources,
  setActiveModuleIndex,
  setActiveTab,
  setMobileNavOpen,
  findTabIndex,
  enabled = true
}) => {
  const [runTutorial, setRunTutorial] = useState(false);
  const [tutorialStepIndex, setTutorialStepIndex] = useState(0);

  // Check for first visit and start tutorial
  useEffect(() => {
    if (!enabled) return;
    const tutorialCompleted = localStorage.getItem(TUTORIAL_STORAGE_KEY);
    if (!loading && !tutorialCompleted) {
      setTimeout(() => setRunTutorial(true), 500);
    }
  }, [loading, enabled]);

  // Start tutorial manually
  const startTutorial = useCallback(() => {
    if (!enabled) return;
    setTutorialStepIndex(0);
    setRunTutorial(true);
  }, [enabled]);

  // Handle Joyride callback
  const handleJoyrideCallback = useCallback((data) => {
    const { action, index, status, type } = data;

    if ([EVENTS.STEP_AFTER, EVENTS.TARGET_NOT_FOUND].includes(type)) {
      setTutorialStepIndex(index + (action === ACTIONS.PREV ? -1 : 1));
    } else if ([STATUS.FINISHED, STATUS.SKIPPED].includes(status)) {
      setRunTutorial(false);
      setTutorialStepIndex(0);
      localStorage.setItem(TUTORIAL_STORAGE_KEY, 'true');
    }
  }, []);

  // Generate tutorial steps
  const tutorialSteps = useMemo(() => {
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
        callback: () => setActiveModuleIndex(0),
      },
      // Conditional steps based on data availability
      ...(actualPathData?.modules?.[0]?.submodules?.length > 0 ? [{
        target: '[data-tut="submodule-item-0-0"]',
        content: 'Now click the first submodule to view its content.',
        placement: 'right',
        disableBeacon: true,
        callback: () => selectSubmodule(0, 0)
      }] : []),
      ...(actualPathData?.modules?.[0]?.resources?.length > 0 ? [{
        target: '[data-tut="module-resources-item-0"]',
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
        preStepCallback: () => {
          if (contentPanelDisplayType === 'module_resources' && actualPathData?.modules?.[0]?.submodules?.length > 0) {
            selectSubmodule(0, 0);
          }
        }
      },
      {
        target: '[data-tut="content-panel-tabs"]',
        content: 'If viewing a submodule, use these tabs to explore different aspects of it.',
        placement: 'bottom',
        disableBeacon: true,
        condition: () => contentPanelDisplayType === 'submodule' && availableTabs.length > 0,
      },
      // Dynamic tab steps
      ...generateTabSteps(availableTabs, findTabIndex, setActiveTab, contentPanelDisplayType),
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
      {
        target: '[data-tut="content-panel"]',
        content: 'The main content for the selected item is shown here.',
        placement: 'top',
        disableBeacon: true,
        preStepCallback: () => {
          if (contentPanelDisplayType === 'module_resources' && actualPathData?.modules?.[0]?.submodules?.length > 0) {
            selectSubmodule(0, 0);
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
        target: '[data-tut="content-panel-progress-checkbox-container"]',
        content: 'Mark the submodule complete here when you\'re done.',
        placement: 'top',
        disableBeacon: true,
        condition: () => contentPanelDisplayType === 'submodule',
      },
      {
        target: '[data-tut="mobile-prev-button"]',
        content: 'Tap these buttons to navigate to the previous or next submodule.',
        placement: 'top',
        disableBeacon: true,
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

    return isMobileLayout ? mobileSteps : desktopSteps;
  }, [
    isMobileLayout,
    availableTabs,
    actualPathData,
    topicResources,
    contentPanelDisplayType,
    selectSubmodule,
    handleSelectModuleResources,
    setActiveModuleIndex,
    setActiveTab,
    setMobileNavOpen,
    findTabIndex
  ]);

  return {
    runTutorial,
    tutorialStepIndex,
    tutorialSteps,
    startTutorial,
    handleJoyrideCallback
  };
};

// Helper function to generate tab steps
const generateTabSteps = (availableTabs, findTabIndex, setActiveTab, contentPanelDisplayType) => {
  const steps = [];
  
  const tabConfigs = [
    { dataTut: 'content-panel-tab-content', content: 'This is the main learning material for the submodule.' },
    { dataTut: 'content-panel-tab-quiz', content: 'Test your understanding with a short quiz.' },
    { dataTut: 'content-panel-tab-resources', content: 'Find additional resources like articles or videos here.' },
    { dataTut: 'content-panel-tab-chat', content: 'Chat with an AI assistant about this specific submodule.' },
    { dataTut: 'content-panel-tab-audio', content: 'Generate an audio version of the submodule content (costs credits!).' },
    { dataTut: 'content-panel-tab-visualization', content: 'Generate an interactive diagram visualization of the submodule content (costs credits!).' }
  ];

  tabConfigs.forEach(config => {
    if (availableTabs.some(t => t.dataTut === config.dataTut)) {
      steps.push({
        target: `[data-tut="${config.dataTut}"]`,
        content: config.content,
        placement: 'top',
        disableBeacon: true,
        condition: () => contentPanelDisplayType === 'submodule',
        callback: () => setActiveTab(findTabIndex(config.dataTut))
      });
    }
  });

  return steps;
};

export default useTutorialManager;
