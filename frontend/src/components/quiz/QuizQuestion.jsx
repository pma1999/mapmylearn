import React, { useEffect, useRef } from 'react';
import { Box, Typography, Paper, useTheme, alpha } from '@mui/material';
import { motion } from 'framer-motion';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';

/**
 * Component to display a quiz question with selectable options
 * 
 * @param {Object} props Component props
 * @param {Object} props.question The current question object with options
 * @param {number|null} props.selectedOption Index of the selected option
 * @param {Function} props.onSelectOption Callback when an option is selected
 * @param {boolean} props.showFeedback Whether to show correct/incorrect styling
 * @returns {JSX.Element} Quiz question component
 */
const QuizQuestion = ({ question, selectedOption, onSelectOption, showFeedback }) => {
  const theme = useTheme();
  const questionRef = useRef(null);
  
  // Scroll to question when it changes
  useEffect(() => {
    if (questionRef.current) {
      questionRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [question]);
  
  if (!question || !question.options) {
    return (
      <Box sx={{ py: 2 }}>
        <Typography variant="body1" color="text.secondary">
          Question not available
        </Typography>
      </Box>
    );
  }
  
  // Check if an option is the correct answer
  const isCorrectOption = (optionIndex) => {
    return question.options[optionIndex]?.is_correct || false;
  };
  
  // Animation for options
  const optionVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: i => ({ 
      opacity: 1, 
      y: 0, 
      transition: { 
        delay: i * 0.1,
        duration: 0.3
      }
    }),
  };
  
  // Get option background color based on selection and correctness
  const getOptionBackgroundColor = (index) => {
    if (!showFeedback) {
      // Pre-submission styling
      return index === selectedOption 
        ? alpha(theme.palette.primary.main, 0.1) 
        : theme.palette.background.paper;
    } else {
      // Post-submission styling
      if (isCorrectOption(index)) {
        return alpha(theme.palette.success.main, 0.1);
      } else if (index === selectedOption && !isCorrectOption(index)) {
        return alpha(theme.palette.error.main, 0.1);
      }
      return theme.palette.background.paper;
    }
  };
  
  // Get option border color based on selection and correctness
  const getOptionBorderColor = (index) => {
    if (!showFeedback) {
      // Pre-submission styling
      return index === selectedOption 
        ? theme.palette.primary.main 
        : theme.palette.divider;
    } else {
      // Post-submission styling
      if (isCorrectOption(index)) {
        return theme.palette.success.main;
      } else if (index === selectedOption && !isCorrectOption(index)) {
        return theme.palette.error.main;
      }
      return theme.palette.divider;
    }
  };
  
  return (
    <Box ref={questionRef} sx={{ mb: 3 }}>
      {/* Question text */}
      <Typography 
        variant="h6" 
        component="div" 
        gutterBottom
        sx={{ 
          fontWeight: 500,
          mb: 3,
          color: theme.palette.text.primary
        }}
      >
        {question.question}
      </Typography>
      
      {/* Answer options */}
      <Box 
        role="radiogroup" 
        aria-labelledby="question-text"
        sx={{ mt: 2 }}
      >
        {question.options.map((option, index) => (
          <motion.div
            key={index}
            custom={index}
            variants={optionVariants}
            initial="hidden"
            animate="visible"
          >
            <Paper
              elevation={0}
              onClick={() => !showFeedback && onSelectOption(index)}
              sx={{
                p: 2,
                mb: 2,
                display: 'flex',
                alignItems: 'center',
                borderRadius: 2,
                cursor: showFeedback ? 'default' : 'pointer',
                border: '1px solid',
                borderColor: getOptionBorderColor(index),
                backgroundColor: getOptionBackgroundColor(index),
                transition: 'all 0.2s ease',
                '&:hover': {
                  backgroundColor: !showFeedback 
                    ? alpha(theme.palette.primary.main, 0.05)
                    : getOptionBackgroundColor(index),
                },
                position: 'relative',
                pl: showFeedback ? 4 : 2
              }}
              role="radio"
              aria-checked={selectedOption === index}
              tabIndex={showFeedback ? -1 : 0}
            >
              {/* Show correct/incorrect icon when feedback is visible */}
              {showFeedback && (
                <Box 
                  sx={{ 
                    position: 'absolute',
                    left: 10,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  {isCorrectOption(index) ? (
                    <CheckCircleIcon color="success" />
                  ) : (
                    index === selectedOption && <CancelIcon color="error" />
                  )}
                </Box>
              )}
              
              <Typography variant="body1">
                {option.text}
              </Typography>
            </Paper>
          </motion.div>
        ))}
      </Box>
    </Box>
  );
};

export default QuizQuestion; 