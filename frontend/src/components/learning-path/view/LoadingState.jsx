import React from 'react';
import PropTypes from 'prop-types';
import { 
  Container, 
  Paper, 
  Typography, 
  Box, 
  LinearProgress,
  useTheme
} from '@mui/material';
import { motion } from 'framer-motion';

/**
 * Component to display loading and progress updates for learning path generation
 * Now uses progress percentage if available.
 * 
 * @param {Object} props Component props
 * @param {Array} props.progressMessages Progress messages from SSE (potentially with progress percentage)
 * @returns {JSX.Element} Loading state component
 */
const LoadingState = ({ progressMessages = [] }) => {
  const theme = useTheme();
  
  // Retrieve the topic from sessionStorage (for new generations)
  const storedTopic = sessionStorage.getItem('currentTopic') || 'your topic';

  // Get the latest progress percentage, default to null if none available
  const latestProgress = progressMessages.length > 0 
      ? progressMessages[progressMessages.length - 1].progress 
      : null;
  // Convert progress (0.0 to 1.0) to percentage (0 to 100) if available
  const progressPercent = latestProgress !== null && !isNaN(latestProgress) ? latestProgress * 100 : null;

  // Get the latest message to display prominently
  const latestMessage = progressMessages.length > 0 
      ? progressMessages[progressMessages.length - 1].message 
      : 'Initializing generation...';
  
  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { 
        staggerChildren: 0.1,
        when: "beforeChildren"
      }
    }
  };
  
  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.5 }
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: { xs: 3, md: 4 } }}>
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Main Loading Box */}
        <motion.div variants={itemVariants}>
          <Paper
            elevation={2} // Use elevation like the simpler loading state
            sx={{
              p: { xs: 3, sm: 4 },
              borderRadius: 3,
              textAlign: 'center',
              maxWidth: 700, // Slightly wider for progress text
              mx: 'auto',
              mt: { xs: 4, md: 8 } // Adjust top margin
            }}
          >
            <Typography variant="h5" component="h2" gutterBottom fontWeight="bold">
              Generating Learning Path for "{storedTopic}"
            </Typography>
            
            <Typography variant="body1" color="text.secondary" paragraph sx={{ minHeight: '3em', mb: 3 }}> 
              {/* Display the latest message */}
              {latestMessage || 'Please wait while we prepare your learning journey...'}
            </Typography>
            
            {/* Progress Bar */}
            <Box sx={{ width: '100%', mt: 2, mb: 2 }}>
              <LinearProgress 
                variant={progressPercent !== null ? "determinate" : "indeterminate"}
                value={progressPercent !== null ? progressPercent : undefined} // Use value only when determinate
                sx={{ 
                  height: 8, // Slightly thicker
                  borderRadius: 4,
                  // Keep gradient for indeterminate, use solid for determinate for clarity
                  backgroundColor: theme.palette.grey[300], // Background for determinate
                  '& .MuiLinearProgress-bar': {
                    background: progressPercent !== null 
                      ? theme.palette.primary.main // Solid color for determinate
                      : `linear-gradient(90deg, ${theme.palette.primary.light}, ${theme.palette.primary.main})`, // Gradient for indeterminate
                    borderRadius: 4,
                    transition: progressPercent !== null ? 'transform .4s linear' : 'none', // Smooth transition for determinate
                  }
                }} 
              />
              {/* Optional: Display percentage text */}
              {progressPercent !== null && (
                 <Typography variant="caption" display="block" sx={{ mt: 1, color: 'text.secondary' }}>
                   {Math.round(progressPercent)}% Complete
                 </Typography>
              )}
            </Box>
          </Paper>
        </motion.div>

        {/* Detailed Progress Message History (Optional - keep if useful) */}
        {progressMessages.length > 1 && ( // Show history only if more than the initial message
          <Box sx={{ mt: 4, maxWidth: 700, mx: 'auto' }}> 
             <Typography variant="h6" sx={{ mb: 2, textAlign: 'center', color: 'text.secondary' }}>
                Generation Steps:
             </Typography>
            {progressMessages.slice(0, -1).reverse().map((message, index) => ( // Show older messages, reversed
              <motion.div 
                key={message.timestamp || index} // Use timestamp if available
                variants={itemVariants}
                initial="hidden"
                animate="visible"
                transition={{ delay: index * 0.05 }} // Faster delay for history
              >
                <Paper
                  elevation={0} // Less emphasis for history
                  variant="outlined" // Use outlined variant
                  sx={{
                    p: { xs: 1.5, sm: 2 },
                    mb: 1.5,
                    borderRadius: 2,
                    // borderLeft: `3px solid ${theme.palette.grey[400]}`, // Subtle indicator
                    opacity: 0.8 // Slightly faded
                  }}
                >
                  <Typography variant="body2" color="text.secondary"> 
                    {message.message}
                  </Typography>
                  {/* Optional: Show timestamp for history */}
                  {/* {message.timestamp && (
                    <Typography variant="caption" color="text.disabled" sx={{ display: 'block', mt: 0.5 }}>
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </Typography>
                  )} */}
                </Paper>
              </motion.div>
            ))}
          </Box>
        )}

      </motion.div>
    </Container>
  );
};

LoadingState.propTypes = {
  progressMessages: PropTypes.arrayOf(PropTypes.shape({
    message: PropTypes.string.isRequired,
    timestamp: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    phase: PropTypes.string, // Added phase if available
    progress: PropTypes.number, // Added progress percentage if available
  })),
  // isPolling prop is no longer used or needed
  // isPolling: PropTypes.bool 
};

export default LoadingState; 