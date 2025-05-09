import React from 'react';
import PropTypes from 'prop-types';
import { 
  Container, 
  Paper, 
  Typography, 
  Box, 
  LinearProgress,
  // CircularProgress,
  // Chip,
  // List,
  // ListItem,
  // ListItemIcon,
  // ListItemText,
  // Collapse,
  // Button,
  useTheme
} from '@mui/material';
import { motion } from 'framer-motion';
// import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
// import ExpandLessIcon from '@mui/icons-material/ExpandLess';
// import ModuleIcon from '@mui/icons-material/AccountTree';
// import SubdirectoryArrowRightIcon from '@mui/icons-material/SubdirectoryArrowRight';

/**
 * Simplified component to display a loading state for course generation.
 * Shows a generic loading message and an indeterminate progress bar.
 * 
 * @param {Object} props Component props
 * @param {string|null} props.topic - The topic of the course being generated (optional)
 * @returns {JSX.Element} Loading state component
 */
const LoadingState = ({ topic = null }) => {
  const theme = useTheme();
  
  let displayTopic = topic;
  if (!displayTopic) {
    const sessionTopic = sessionStorage.getItem('currentTopic');
    if (sessionTopic) {
      displayTopic = sessionTopic;
    }
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { duration: 0.5 } }
  };
  
  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.4, delay: 0.1 } }
  };

  return (
    <Container maxWidth="md" sx={{ py: { xs: 3, md: 4 }, display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '70vh' }}> 
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        style={{ width: '100%' }} // Ensure motion div takes width for Paper centering
      >
        <motion.div variants={itemVariants}>
          <Paper
            elevation={3} 
            sx={{
              p: { xs: 3, sm: 4, md: 5 },
              borderRadius: 3,
              textAlign: 'center',
              mx: 'auto',
              maxWidth: '500px',
            }}
          >
            <Typography variant="h5" component="h2" gutterBottom fontWeight="bold">
              {displayTopic ? `Generating Your Course: "${displayTopic}"` : 'Loading Course...'}
            </Typography>
            
            <Typography variant="body1" color="text.secondary" paragraph sx={{ mb: 3 }}>
              Please wait a moment while we prepare everything for you.
            </Typography>
            
            <Box sx={{ width: '100%', my: 3 }}>
                <LinearProgress 
                    variant="indeterminate"
                    sx={{ 
                        height: 8, 
                        borderRadius: 4,
                        backgroundColor: theme.palette.grey[300],
                        '& .MuiLinearProgress-bar': {
                            background: `linear-gradient(90deg, ${theme.palette.primary.light}, ${theme.palette.primary.main})`,
                            borderRadius: 4,
                        }
                    }} 
                />
            </Box>

            <Typography variant="caption" color="text.disabled">
                This may take a few minutes depending on the topic complexity.
            </Typography>

          </Paper>
        </motion.div>
      </motion.div>
    </Container>
  );
};

LoadingState.propTypes = {
  topic: PropTypes.string, 
};

export default LoadingState; 