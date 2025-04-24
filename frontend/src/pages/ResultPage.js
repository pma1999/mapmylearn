import React from 'react';
import { useParams } from 'react-router';

// Import the new shared LearningPathView component
import LearningPathView from '../components/learning-path/view/LearningPathView';

/**
 * ResultPage component for displaying a learning path
 * This is now a thin wrapper around the shared LearningPathView component
 * 
 * @param {Object} props Component props
 * @param {string} props.source Optional source identifier ('history' or null)
 * @returns {JSX.Element} Result page component
 */
function ResultPage({ source }) {
  const { taskId, entryId } = useParams();
  
  return (
    <LearningPathView source={source} />
  );
}

export default ResultPage; 