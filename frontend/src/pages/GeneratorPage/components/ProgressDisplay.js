import React from 'react';
import {
  Box,
  Stack,
  Typography,
  Paper,
  CircularProgress
} from '@mui/material';
import AutorenewIcon from '@mui/icons-material/Autorenew';
import ProgressBar from '../../../components/ProgressBar';

/**
 * Component to display progress information during learning path generation
 * @param {Object} props - Component props
 * @param {Array} props.progressUpdates - List of progress update objects
 * @param {number} props.progressPercentage - Current progress percentage (0-100)
 * @param {boolean} props.isMobile - Whether the display is in mobile viewport
 * @returns {JSX.Element} Progress display component
 */
const ProgressDisplay = ({ progressUpdates, progressPercentage, isMobile }) => {
  return (
    <Box sx={{ mt: 4, textAlign: 'center' }}>
      <Stack 
        direction={isMobile ? "column" : "row"} 
        spacing={isMobile ? 1 : 2} 
        alignItems="center" 
        justifyContent="center"
        sx={{ mb: 2 }}
      >
        <AutorenewIcon sx={{ animation: 'spin 2s linear infinite' }} />
        <Typography>
          Researching your topic and creating your personalized learning path...
        </Typography>
      </Stack>
      
      {/* Progress Bar */}
      <ProgressBar 
        label="Generation Progress" 
        value={progressPercentage} 
        color="primary" 
      />
      
      {/* Progress Updates */}
      <Paper 
        elevation={1}
        sx={{ 
          p: 2, 
          mt: 2, 
          maxHeight: '200px', 
          overflow: 'auto',
          bgcolor: 'background.paper'
        }}
      >
        <Typography variant="subtitle2" gutterBottom>
          Progress Updates:
        </Typography>
        {progressUpdates.length > 0 ? (
          progressUpdates.map((update, index) => (
            <Typography 
              key={index} 
              variant="body2" 
              color="text.secondary"
              sx={{ mb: 0.5, fontSize: '0.8rem' }}
            >
              {update.message}
            </Typography>
          ))
        ) : (
          <Typography variant="body2" color="text.secondary">
            Waiting for updates...
          </Typography>
        )}
      </Paper>
      
      <Typography variant="body2" color="text.secondary" sx={{ 
        mt: 2,
        fontSize: { xs: '0.75rem', sm: '0.875rem' }
      }}>
        This may take a few minutes depending on the complexity of the topic.
      </Typography>
    </Box>
  );
};

export default ProgressDisplay; 