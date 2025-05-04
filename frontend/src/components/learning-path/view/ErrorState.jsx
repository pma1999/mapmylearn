import React from 'react';
import PropTypes from 'prop-types';
import { 
  Container, 
  Paper, 
  Typography, 
  Box, 
  Button
} from '@mui/material';
import ErrorIcon from '@mui/icons-material/Error';
import HomeIcon from '@mui/icons-material/Home';
import AddIcon from '@mui/icons-material/Add';
import { motion } from 'framer-motion';

/**
 * Component to display error state for course
 * 
 * @param {Object} props Component props
 * @param {string} props.error Error message
 * @param {Function} props.onHomeClick Handler for home button click
 * @param {Function} props.onNewLearningPathClick Handler for new course button click
 * @returns {JSX.Element} Error state component
 */
const ErrorState = ({ error, onHomeClick, onNewLearningPathClick }) => {
  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0, scale: 0.95 },
    visible: { 
      opacity: 1,
      scale: 1,
      transition: { 
        duration: 0.5
      }
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: { xs: 3, md: 4 } }}>
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            textAlign: 'center',
            maxWidth: '600px',
            mx: 'auto',
            mt: 4,
            borderRadius: 2
          }}
        >
          <ErrorIcon color="error" sx={{ fontSize: 60, mb: 2 }} />
          
          <Typography variant="h5" component="h2" gutterBottom fontWeight="bold">
            Error Generating Course
          </Typography>
          
          <Typography variant="body1" sx={{ mb: 3 }}>
            {error.includes("not found") 
              ? "The course you're looking for couldn't be found. It may have been deleted or not properly migrated from your local storage."
              : error
            }
          </Typography>
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
            We recommend trying one of the following options:
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
            <Button 
              variant="contained" 
              color="primary" 
              startIcon={<HomeIcon />}
              onClick={onHomeClick}
            >
              Go to Home
            </Button>
            
            <Button 
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={onNewLearningPathClick}
            >
              Create New Path
            </Button>
          </Box>
        </Paper>
      </motion.div>
    </Container>
  );
};

ErrorState.propTypes = {
  error: PropTypes.string.isRequired,
  onHomeClick: PropTypes.func.isRequired,
  onNewLearningPathClick: PropTypes.func.isRequired
};

export default ErrorState; 