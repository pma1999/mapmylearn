import { useMemo } from 'react';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import CollectionsBookmarkIcon from '@mui/icons-material/CollectionsBookmark';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import GraphicEqIcon from '@mui/icons-material/GraphicEq';
import VisibilityIcon from '@mui/icons-material/Visibility';
import { helpTexts } from '../../../constants/helpTexts';
import { AUDIO_CREDIT_COST, VISUALIZATION_CREDIT_COST, TAB_TYPES } from '../constants/viewConstants';

/**
 * Custom hook to calculate available tabs for a submodule
 * @param {Object} submodule Current submodule data
 * @param {Object} options Configuration options
 * @returns {Array} Array of available tabs
 */
const useTabConfiguration = (submodule, options = {}) => {
  const { includeVisualization = true } = options;

  const availableTabs = useMemo(() => {
    if (!submodule) return [];

    const hasQuiz = submodule.quiz_questions && submodule.quiz_questions.length > 0;
    const hasResources = submodule.resources && submodule.resources.length > 0;

    let tabIndexCounter = 0;
    const tabs = [
      {
        index: tabIndexCounter++,
        type: TAB_TYPES.CONTENT,
        label: 'Content',
        icon: <MenuBookIcon />,
        tooltip: "View submodule content",
        dataTut: 'content-panel-tab-content'
      }
    ];

    if (hasQuiz) {
      tabs.push({
        index: tabIndexCounter++,
        type: TAB_TYPES.QUIZ,
        label: 'Quiz',
        icon: <FitnessCenterIcon />,
        tooltip: helpTexts.submoduleTabQuiz,
        dataTut: 'content-panel-tab-quiz'
      });
    }

    if (hasResources) {
      tabs.push({
        index: tabIndexCounter++,
        type: TAB_TYPES.RESOURCES,
        label: 'Resources',
        icon: <CollectionsBookmarkIcon />,
        tooltip: "View submodule resources",
        dataTut: 'content-panel-tab-resources'
      });
    }

    tabs.push({
      index: tabIndexCounter++,
      type: TAB_TYPES.CHAT,
      label: 'Chat',
      icon: <QuestionAnswerIcon />,
      tooltip: helpTexts.submoduleTabChat,
      dataTut: 'content-panel-tab-chat'
    });

    tabs.push({
      index: tabIndexCounter++,
      type: TAB_TYPES.AUDIO,
      label: 'Audio',
      icon: <GraphicEqIcon />,
      tooltip: helpTexts.submoduleTabAudio(AUDIO_CREDIT_COST),
      dataTut: 'content-panel-tab-audio'
    });

    if (includeVisualization) {
      tabs.push({
        index: tabIndexCounter++,
        type: TAB_TYPES.VISUALIZATION,
        label: 'Visualization',
        icon: <VisibilityIcon />,
        tooltip: helpTexts.submoduleTabVisualization(VISUALIZATION_CREDIT_COST),
        dataTut: 'content-panel-tab-visualization'
      });
    }

    return tabs;
  }, [submodule, includeVisualization]);

  // Helper to find tab index by type or dataTut
  const findTabIndex = useMemo(() => {
    return (identifier) => {
      if (typeof identifier === 'string') {
        // Search by type first, then by dataTut
        const byType = availableTabs.findIndex(t => t.type === identifier);
        if (byType !== -1) return byType;
        
        const byDataTut = availableTabs.findIndex(t => t.dataTut === identifier);
        return byDataTut !== -1 ? byDataTut : 0;
      }
      return 0;
    };
  }, [availableTabs]);

  // Get tab by type
  const getTabByType = useMemo(() => {
    return (type) => availableTabs.find(tab => tab.type === type);
  }, [availableTabs]);

  return {
    availableTabs,
    findTabIndex,
    getTabByType,
    hasQuiz: availableTabs.some(tab => tab.type === TAB_TYPES.QUIZ),
    hasResources: availableTabs.some(tab => tab.type === TAB_TYPES.RESOURCES),
    hasVisualization: availableTabs.some(tab => tab.type === TAB_TYPES.VISUALIZATION)
  };
};

export default useTabConfiguration;
