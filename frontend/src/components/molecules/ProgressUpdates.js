import React from 'react';
import { Box, Typography, LinearProgress, Paper, Stack, Alert } from '@mui/material';
import ProgressTracker from '../organisms/ProgressTracker';

/**
 * A component to display updates about a learning path's generation progress.
 * This is a wrapper around the new ProgressTracker component for backward compatibility.
 */
const ProgressUpdates = ({ progressMessages = [] }) => {
  return (
    <Box sx={{ width: '100%', my: 2 }}>
      <ProgressTracker progressMessages={progressMessages} estimatedTotalTime={300} />
    </Box>
  );
};

export default ProgressUpdates; 