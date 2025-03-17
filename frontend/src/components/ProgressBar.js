import React from 'react';
import { Box, LinearProgress, Typography } from '@mui/material';

/**
 * A component that shows a progress bar with a label.
 * 
 * @param {Object} props - Component props
 * @param {string} props.label - Text to display above the progress bar
 * @param {number} props.value - Current progress value (0-100), use null for indeterminate
 * @param {string} props.color - The color of the progress bar (primary, secondary, success, etc.)
 * @param {Object} props.sx - Additional Material UI sx prop styles
 */
function ProgressBar({ label, value = null, color = 'primary', sx = {} }) {
  return (
    <Box sx={{ width: '100%', mt: 2, mb: 2, ...sx }}>
      {label && (
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {label}
        </Typography>
      )}
      {value !== null ? (
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Box sx={{ width: '100%', mr: 1 }}>
            <LinearProgress variant="determinate" value={value} color={color} />
          </Box>
          <Box sx={{ minWidth: 35 }}>
            <Typography variant="body2" color="text.secondary">{`${Math.round(value)}%`}</Typography>
          </Box>
        </Box>
      ) : (
        <LinearProgress color={color} />
      )}
    </Box>
  );
}

export default ProgressBar; 