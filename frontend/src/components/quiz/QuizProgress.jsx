import React from 'react';
import { Box, LinearProgress, Typography, useTheme } from '@mui/material';

/**
 * Component to display quiz progress
 * 
 * @param {Object} props Component props
 * @param {number} props.current Current question number
 * @param {number} props.total Total number of questions
 * @param {number} props.correct Number of correct answers so far
 * @returns {JSX.Element} Quiz progress component
 */
const QuizProgress = ({ current, total, correct = 0 }) => {
  const theme = useTheme();
  
  // Calculate progress percentage
  const progressPercentage = (current / total) * 100;
  
  // Calculate score percentage if any questions have been answered
  const scorePercentage = current > 1 ? (correct / (current - 1)) * 100 : 0;
  
  return (
    <Box sx={{ mb: 3, width: '100%' }}>
      {/* Progress bar with gradient */}
      <Box 
        sx={{ 
          height: 8, 
          borderRadius: 4, 
          mb: 1.5, 
          width: '100%', 
          bgcolor: theme.palette.grey[100],
          overflow: 'hidden'
        }}
      >
        <LinearProgress
          variant="determinate"
          value={progressPercentage}
          sx={{
            height: '100%',
            borderRadius: 4,
            bgcolor: theme.palette.grey[100],
            '& .MuiLinearProgress-bar': {
              background: `linear-gradient(90deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.light} 100%)`,
              transition: 'transform 0.5s ease'
            }
          }}
        />
      </Box>
      
      {/* Stats display */}
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        {/* Progress counter */}
        <Typography 
          variant="body2" 
          color="text.secondary"
          sx={{ fontWeight: 500 }}
        >
          Progress: {current}/{total} questions
        </Typography>
        
        {/* Score counter - only show if at least one question has been answered */}
        {current > 1 && (
          <Typography 
            variant="body2" 
            sx={{ 
              fontWeight: 500,
              color: scorePercentage >= 70 
                ? theme.palette.success.main 
                : scorePercentage >= 40 
                  ? theme.palette.warning.main
                  : theme.palette.error.main
            }}
          >
            Score: {correct}/{current - 1} ({Math.round(scorePercentage)}%)
          </Typography>
        )}
      </Box>
    </Box>
  );
};

export default QuizProgress; 