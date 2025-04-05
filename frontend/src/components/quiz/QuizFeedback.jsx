import React from 'react';
import { Box, Typography, Paper, useTheme, alpha } from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import HighlightOffIcon from '@mui/icons-material/HighlightOff';
import MarkdownRenderer from '../../components/MarkdownRenderer';
import { motion } from 'framer-motion';

/**
 * Component to display feedback after answering a question
 * 
 * @param {Object} props Component props
 * @param {boolean} props.isCorrect Whether the answer was correct
 * @param {string} props.explanation Explanation text for the answer
 * @returns {JSX.Element} Quiz feedback component
 */
const QuizFeedback = ({ isCorrect, explanation }) => {
  const theme = useTheme();
  
  // Animation for the feedback component
  const feedbackVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0, 
      transition: { 
        type: 'spring', 
        stiffness: 200, 
        damping: 20,
        duration: 0.5 
      } 
    }
  };
  
  return (
    <motion.div
      variants={feedbackVariants}
      initial="hidden"
      animate="visible"
    >
      <Paper
        elevation={0}
        sx={{
          p: 2.5,
          mt: 3,
          mb: 2,
          borderRadius: 2,
          border: '1px solid',
          borderColor: isCorrect 
            ? theme.palette.success.main 
            : theme.palette.error.main,
          bgcolor: isCorrect
            ? alpha(theme.palette.success.main, 0.05)
            : alpha(theme.palette.error.main, 0.05)
        }}
      >
        {/* Correct/Incorrect header */}
        <Box 
          sx={{ 
            display: 'flex', 
            alignItems: 'center',
            mb: 1.5
          }}
        >
          {isCorrect ? (
            <>
              <CheckCircleOutlineIcon 
                color="success" 
                sx={{ mr: 1, fontSize: 24 }}
              />
              <Typography 
                variant="subtitle1" 
                color="success.main"
                sx={{ fontWeight: 600 }}
              >
                Correct!
              </Typography>
            </>
          ) : (
            <>
              <HighlightOffIcon 
                color="error" 
                sx={{ mr: 1, fontSize: 24 }}
              />
              <Typography 
                variant="subtitle1" 
                color="error.main"
                sx={{ fontWeight: 600 }}
              >
                Incorrect
              </Typography>
            </>
          )}
        </Box>
        
        {/* Explanation content */}
        <Box sx={{ mt: 1 }}>
          <Typography 
            variant="subtitle2" 
            component="h4"
            gutterBottom
            sx={{ 
              fontWeight: 600, 
              color: theme.palette.text.primary 
            }}
          >
            Explanation:
          </Typography>
          
          <Box 
            sx={{ 
              mt: 1, 
              p: 1.5, 
              bgcolor: alpha(theme.palette.background.paper, 0.7),
              borderRadius: 1,
              border: '1px solid',
              borderColor: theme.palette.divider,
            }}
          >
            <MarkdownRenderer>
              {explanation}
            </MarkdownRenderer>
          </Box>
        </Box>
      </Paper>
    </motion.div>
  );
};

export default QuizFeedback; 