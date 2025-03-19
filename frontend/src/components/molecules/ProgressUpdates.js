import React from 'react';
import {
  Box,
  Typography,
  Paper,
  CircularProgress,
  LinearProgress,
  useTheme,
  useMediaQuery,
  Divider
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';

const ProgressUpdates = ({ progressMessages }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { duration: 0.5 }
    }
  };
  
  const progressVariants = {
    initial: { width: '0%' },
    animate: { 
      width: '100%', 
      transition: { duration: 15, ease: 'linear' } 
    }
  };

  const messageVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: 0.4,
        ease: "easeOut"
      }
    },
    exit: {
      opacity: 0,
      transition: { duration: 0.2 }
    }
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      <Paper 
        elevation={3} 
        sx={{ 
          p: { xs: 3, sm: 4 }, 
          borderRadius: 2, 
          mb: 4,
          position: 'relative',
          overflow: 'hidden',
          bgcolor: theme.palette.background.paper
        }}
      >
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            height: '4px',
            bgcolor: theme.palette.primary.main,
            zIndex: 1
          }}
          component={motion.div}
          variants={progressVariants}
          initial="initial"
          animate="animate"
        />
        
        <Box sx={{ textAlign: 'center', my: 3 }}>
          <CircularProgress 
            color="primary" 
            size={isMobile ? 48 : 56}
            thickness={4}
            sx={{ mb: 2 }} 
          />
          
          <Typography 
            variant="h5" 
            sx={{ 
              mt: 2, 
              fontWeight: 600,
              fontSize: { xs: '1.25rem', sm: '1.5rem' },
              color: theme.palette.primary.main
            }}
          >
            Generating Your Learning Path
          </Typography>
          
          <Typography 
            color="text.secondary" 
            sx={{ 
              mt: 1.5, 
              mb: 3,
              fontSize: { xs: '0.875rem', sm: '1rem' },
              maxWidth: 500,
              mx: 'auto'
            }}
          >
            We're building a personalized learning path for you. This may take a few minutes 
            depending on the complexity of the topic.
          </Typography>
          
          <LinearProgress 
            sx={{ 
              my: 3, 
              height: 6, 
              borderRadius: 3,
              maxWidth: 500,
              mx: 'auto'
            }} 
          />
        </Box>
        
        <Divider sx={{ mt: 2, mb: 3 }} />
        
        <Box sx={{ mt: 3 }}>
          <Typography 
            variant="h6" 
            gutterBottom 
            sx={{ 
              fontWeight: 600,
              fontSize: { xs: '1rem', sm: '1.25rem' },
              display: 'flex',
              alignItems: 'center'
            }}
          >
            <Box 
              component="span" 
              sx={{ 
                display: 'inline-block', 
                width: 12, 
                height: 12, 
                borderRadius: '50%', 
                bgcolor: 'primary.main',
                mr: 1.5,
                animation: 'pulse 1.5s infinite'
              }} 
            />
            Progress Updates:
          </Typography>
          
          {progressMessages.length === 0 ? (
            <Typography 
              color="text.secondary" 
              sx={{ 
                fontStyle: 'italic',
                fontSize: { xs: '0.875rem', sm: '1rem' },
                my: 2
              }}
            >
              Waiting for updates...
            </Typography>
          ) : (
            <Box 
              sx={{ 
                maxHeight: '300px', 
                overflow: 'auto', 
                p: 2, 
                mt: 2,
                bgcolor: 'grey.50', 
                borderRadius: 2,
                border: '1px solid',
                borderColor: 'grey.200'
              }}
            >
              <AnimatePresence>
                {progressMessages.map((msg, index) => (
                  <motion.div 
                    key={index}
                    variants={messageVariants}
                    initial="hidden"
                    animate="visible"
                    exit="exit"
                  >
                    <Typography 
                      sx={{ 
                        mb: 1.5, 
                        pb: 1.5,
                        fontSize: { xs: '0.875rem', sm: '0.9rem' },
                        borderBottom: index !== progressMessages.length - 1 ? '1px dashed' : 'none',
                        borderColor: 'grey.200',
                        lineHeight: 1.6
                      }}
                    >
                      <Box component="span" sx={{ 
                        color: theme.palette.primary.main, 
                        fontWeight: 'bold',
                        mr: 1
                      }}>
                        {new Date(msg.timestamp).toLocaleTimeString()}:
                      </Box> 
                      {msg.message}
                    </Typography>
                  </motion.div>
                ))}
              </AnimatePresence>
            </Box>
          )}
        </Box>
      </Paper>
    </motion.div>
  );
};

export default ProgressUpdates; 