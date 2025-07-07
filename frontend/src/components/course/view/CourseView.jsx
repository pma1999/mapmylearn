import React from 'react';
import PropTypes from 'prop-types';

// Import the refactored LearningPathView
import LearningPathView from '../../learning-path/view/LearningPathView';

/**
 * CourseView component - now simply wraps LearningPathView
 * This maintains backward compatibility while using the new architecture
 * 
 * @param {Object} props Component props
 * @param {string} props.source Source of the course
 * @returns {JSX.Element} Course view component
 */
const CourseView = ({ source }) => {
  return <LearningPathView source={source} />;
};

CourseView.propTypes = {
  source: PropTypes.oneOf(['history', 'public', 'offline', null, undefined]),
};

export default CourseView;
