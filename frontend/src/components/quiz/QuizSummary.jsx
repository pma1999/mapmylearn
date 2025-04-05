import React from 'react';
import { Box, Typography, Button, Paper, useTheme, alpha } from '@mui/material';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import { motion } from 'framer-motion';

/**
 * Component to display quiz summary after completion
 * 
 * @param {Object} props Component props
 * @param {number} props.correctAnswers Number of correct answers
 * @param {number} props.totalQuestions Total number of questions
 * @param {Function} props.onReset Function to restart the quiz
 * @returns {JSX.Element} Quiz summary component
 */
const QuizSummary = ({ correctAnswers, totalQuestions, onReset }) => {
  const theme = useTheme();
  
  // Calculate score percentage
  const scorePercentage = Math.round((correctAnswers / totalQuestions) * 100);
  
  // Determine result category based on score
  const getResultCategory = () => {
    if (scorePercentage >= 90) return {
      title: 'Excellent!',
      message: 'You have mastered this topic!',
      color: theme.palette.success.dark,
      icon: <EmojiEventsIcon sx={{ fontSize: 60, mb: 1 }} />
    };
    if (scorePercentage >= 75) return {
      title: 'Great Job!',
      message: 'You have a strong understanding of this topic.',
      color: theme.palette.success.main,
      icon: <EmojiEventsIcon sx={{ fontSize: 50, mb: 1 }} />
    };
    if (scorePercentage >= 60) return {
      title: 'Good Work!',
      message: 'You understand the basics, but could use more practice.',
      color: theme.palette.warning.main,
      icon: <EmojiEventsIcon sx={{ fontSize: 40, mb: 1 }} />
    };
    return {
      title: 'Keep Learning!',
      message: 'Review the content and try again to improve your score.',
      color: theme.palette.error.main,
      icon: <RestartAltIcon sx={{ fontSize: 40, mb: 1 }} />
    };
  };
  
  const result = getResultCategory();
  
  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: { 
      opacity: 1, 
      scale: 1,
      transition: { 
        duration: 0.5,
        delayChildren: 0.2,
        staggerChildren: 0.1
      }
    }
  };
  
  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.3 } }
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <Paper
        elevation={0}
        sx={{
          p: 4,
          borderRadius: 2,
          border: '1px solid',
          borderColor: alpha(result.color, 0.5),
          textAlign: 'center',
          bgcolor: alpha(result.color, 0.05)
        }}
      >
        <motion.div variants={itemVariants}>
          <Box 
            sx={{ 
              color: result.color,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center'
            }}
          >
            {result.icon}
          </Box>
        </motion.div>
        
        <motion.div variants={itemVariants}>
          <Typography 
            variant="h4" 
            component="h2"
            gutterBottom
            sx={{ 
              color: result.color,
              fontWeight: 700,
              mt: 1
            }}
          >
            {result.title}
          </Typography>
        </motion.div>
        
        <motion.div variants={itemVariants}>
          <Typography 
            variant="h5" 
            component="div"
            gutterBottom
            sx={{ 
              fontWeight: 600,
              mt: 2
            }}
          >
            Your Score: {scorePercentage}%
          </Typography>
        </motion.div>
        
        <motion.div variants={itemVariants}>
          <Typography 
            variant="h6" 
            component="div"
            sx={{ 
              mb: 3,
              color: theme.palette.text.secondary
            }}
          >
            {correctAnswers} correct out of {totalQuestions} questions
          </Typography>
        </motion.div>
        
        <motion.div variants={itemVariants}>
          <Typography 
            variant="body1"
            sx={{ 
              mb: 4,
              maxWidth: 500,
              mx: 'auto'
            }}
          >
            {result.message}
          </Typography>
        </motion.div>
        
        <motion.div variants={itemVariants}>
          <Button
            variant="contained"
            color="primary"
            size="large"
            startIcon={<RestartAltIcon />}
            onClick={onReset}
            sx={{ 
              mt: 2,
              minWidth: 200,
              fontWeight: 600
            }}
          >
            Try Again
          </Button>
        </motion.div>
      </Paper>
    </motion.div>
  );
};

export default QuizSummary; 