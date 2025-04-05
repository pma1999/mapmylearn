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
 * 
 * @param {Object} props Component props
 * @param {Array} props.progressMessages Progress messages from SSE
 * @param {boolean} props.isPolling Whether the component is polling for updates
 * @returns {JSX.Element} Loading state component
 */
const LoadingState = ({ progressMessages = [], isPolling = false }) => {
  const theme = useTheme();
  
  // Retrieve the topic from sessionStorage (for new generations)
  const storedTopic = sessionStorage.getItem('currentTopic') || 'your topic';
  
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
        {progressMessages.length > 0 ? (
          <Box>
            <motion.div variants={itemVariants}>
              <Paper
                elevation={0}
                sx={{
                  p: { xs: 2, sm: 3, md: 3 },
                  borderRadius: 3,
                  bgcolor: 'background.paper',
                  mb: 3
                }}
              >
                <Typography variant="h4" component="h1" gutterBottom color="primary" fontWeight="500">
                  Generating Learning Path
                </Typography>
                <Typography variant="body1" color="text.secondary" paragraph>
                  We're creating a comprehensive learning path for "{storedTopic}". 
                  The AI is analyzing the topic, researching content, and structuring the perfect learning journey for you.
                </Typography>
                
                {isPolling && (
                  <Box sx={{ width: '100%', mt: 2 }}>
                    <LinearProgress 
                      sx={{ 
                        height: 6, 
                        borderRadius: 3,
                        '& .MuiLinearProgress-bar': {
                          background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`
                        }
                      }} 
                    />
                  </Box>
                )}
              </Paper>
            </motion.div>
            
            <Box sx={{ mt: 3 }}>
              {progressMessages.map((message, index) => (
                <motion.div 
                  key={index} 
                  variants={itemVariants}
                  initial="hidden"
                  animate="visible"
                  transition={{ delay: index * 0.1 }}
                >
                  <Paper
                    elevation={1}
                    sx={{
                      p: { xs: 2, sm: 2 },
                      mb: 2,
                      borderRadius: 2,
                      borderLeft: `4px solid ${theme.palette.primary.main}`
                    }}
                  >
                    <Typography variant="body1">
                      {message.message}
                    </Typography>
                    {message.timestamp && (
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </Typography>
                    )}
                  </Paper>
                </motion.div>
              ))}
            </Box>
          </Box>
        ) : (
          // If no progress messages yet, show a simpler loading state
          <motion.div variants={itemVariants}>
            <Paper
              elevation={2}
              sx={{
                p: { xs: 3, sm: 4 },
                borderRadius: 3,
                textAlign: 'center',
                maxWidth: 600,
                mx: 'auto',
                mt: 8
              }}
            >
              <Typography variant="h5" component="h2" gutterBottom fontWeight="bold">
                Loading Learning Path
              </Typography>
              
              <Typography variant="body1" paragraph>
                Please wait while we retrieve your learning path...
              </Typography>
              
              <Box sx={{ width: '100%', mt: 4, mb: 2 }}>
                <LinearProgress 
                  sx={{ 
                    height: 6, 
                    borderRadius: 3,
                    '& .MuiLinearProgress-bar': {
                      background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`
                    }
                  }} 
                />
              </Box>
            </Paper>
          </motion.div>
        )}
      </motion.div>
    </Container>
  );
};

LoadingState.propTypes = {
  progressMessages: PropTypes.arrayOf(PropTypes.shape({
    message: PropTypes.string.isRequired,
    timestamp: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    type: PropTypes.string
  })),
  isPolling: PropTypes.bool
};

export default LoadingState; 