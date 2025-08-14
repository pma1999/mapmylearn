import React from 'react';
import PropTypes from 'prop-types';
import CuriosityCard from './CuriosityCard';
import InteractiveQuestionCard from './InteractiveQuestionCard';

/**
 * Wrapper component that renders the appropriate content type
 * (curiosity or interactive question) based on the content item type
 */
const EngagementContent = ({ item, onCopy, onInteract }) => {
  if (!item || !item.type || !item.data) {
    return null;
  }

  switch (item.type) {
    case 'curiosity':
      return (
        <CuriosityCard
          text={item.data.text}
          category={item.data.category}
          onCopy={onCopy}
        />
      );
    
    case 'question':
      return (
        <InteractiveQuestionCard
          data={item.data}
          onInteract={onInteract}
        />
      );
    
    default:
      console.warn('Unknown engagement content type:', item.type);
      return null;
  }
};

EngagementContent.propTypes = {
  item: PropTypes.shape({
    type: PropTypes.oneOf(['curiosity', 'question']).isRequired,
    data: PropTypes.object.isRequired,
  }).isRequired,
  onCopy: PropTypes.func,
  onInteract: PropTypes.func,
};

export default EngagementContent;
