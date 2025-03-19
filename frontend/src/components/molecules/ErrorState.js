import React from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Alert,
  Stack,
  useTheme,
  useMediaQuery,
  Divider
} from '@mui/material';
import ErrorIcon from '@mui/icons-material/Error';
import HomeIcon from '@mui/icons-material/Home';
import RefreshIcon from '@mui/icons-material/Refresh';
import { motion } from 'framer-motion';

const ErrorState = ({ error, onHomeClick, onTryAgainClick }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: 0.4,
        ease: "easeOut"
      }
    }
  };
  
  const iconVariants = {
    hidden: { scale: 0.8, opacity: 0 },
    visible: { 
      scale: 1, 
      opacity: 1,
      transition: { 
        delay: 0.2,
        type: "spring",
        stiffness: 200,
        damping: 10
      }
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
          p: { xs: 3, sm: 4, md: 5 }, 
          borderRadius: 2, 
          mb: 4, 
          textAlign: 'center',
          border: `1px solid ${theme.palette.error.light}`,
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '8px',
            bgcolor: theme.palette.error.main
          }}
        />
        
        <Box sx={{ my: 3 }}>
          <motion.div variants={iconVariants}>
            <ErrorIcon 
              color="error" 
              sx={{ 
                fontSize: { xs: 60, sm: 72, md: 80 },
                mb: 2
              }} 
            />
          </motion.div>
          
          <Typography 
            variant="h4" 
            color="error" 
            sx={{ 
              mt: 2, 
              mb: 3,
              fontWeight: 600,
              fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' }
            }}
          >
            Error Generating Learning Path
          </Typography>
          
          <Alert 
            severity="error" 
            variant="outlined"
            sx={{ 
              mt: 1, 
              mb: 4,
              mx: 'auto',
              maxWidth: 600,
              '& .MuiAlert-message': {
                fontSize: { xs: '0.9rem', sm: '1rem' }
              }
            }}
          >
            {error}
          </Alert>
          
          <Divider sx={{ mb: 4, width: '80%', mx: 'auto' }} />
          
          <Typography 
            color="text.secondary" 
            paragraph
            sx={{ 
              mb: 4,
              maxWidth: 600,
              mx: 'auto',
              fontSize: { xs: '0.9rem', sm: '1rem' }
            }}
          >
            We encountered an error while generating your learning path. 
            This could be due to a server issue, network problem, or API limitation. 
            Please try again or return to the homepage.
          </Typography>
          
          <Stack 
            direction={isMobile ? "column" : "row"} 
            spacing={isMobile ? 2 : 3} 
            justifyContent="center"
            sx={{ mt: 3 }}
          >
            <Button
              variant="outlined"
              startIcon={<HomeIcon />}
              onClick={onHomeClick}
              size={isMobile ? "medium" : "large"}
              sx={{ minWidth: isMobile ? "100%" : 180 }}
            >
              Go to Homepage
            </Button>
            <Button
              variant="contained"
              color="primary"
              startIcon={<RefreshIcon />}
              onClick={onTryAgainClick}
              size={isMobile ? "medium" : "large"}
              sx={{ minWidth: isMobile ? "100%" : 180 }}
            >
              Try Again
            </Button>
          </Stack>
        </Box>
      </Paper>
    </motion.div>
  );
};

export default ErrorState; 