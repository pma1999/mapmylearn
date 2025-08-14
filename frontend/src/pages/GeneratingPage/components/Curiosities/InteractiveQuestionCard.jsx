import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { Box, Paper, Typography, Button, IconButton, Tooltip, alpha } from '@mui/material';
import { styled, useTheme } from '@mui/material/styles';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import QuizIcon from '@mui/icons-material/Quiz';
import { motion } from 'framer-motion';
import QuestionCategoryChip from './QuestionCategoryChip';

const Container = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2.5),
  borderRadius: theme.shape.borderRadius * 1.5,
  border: `1px solid ${theme.palette.divider}`,
  background:
    theme.palette.mode === 'dark'
      ? 'linear-gradient(180deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.02) 100%)'
      : 'linear-gradient(180deg, rgba(0,0,0,0.02) 0%, rgba(0,0,0,0.00) 100%)',
}));

const OptionButton = styled(Button)(({ theme, selected, correct, incorrect }) => ({
  justifyContent: 'flex-start',
  textAlign: 'left',
  padding: theme.spacing(1.5),
  marginBottom: theme.spacing(1),
  borderRadius: theme.shape.borderRadius,
  textTransform: 'none',
  color: theme.palette.text.primary,
  backgroundColor: 
    incorrect ? alpha(theme.palette.error.main, 0.1) :
    correct ? alpha(theme.palette.success.main, 0.1) :
    selected ? alpha(theme.palette.primary.main, 0.1) : 
    theme.palette.background.paper,
  border: `1px solid ${
    incorrect ? theme.palette.error.main :
    correct ? theme.palette.success.main :
    selected ? theme.palette.primary.main : 
    theme.palette.divider
  }`,
  '&:hover': {
    backgroundColor: 
      incorrect ? alpha(theme.palette.error.main, 0.1) :
      correct ? alpha(theme.palette.success.main, 0.1) :
      alpha(theme.palette.primary.main, 0.05),
  },
  '&:disabled': {
    color: theme.palette.text.primary,
    backgroundColor: 
      incorrect ? alpha(theme.palette.error.main, 0.1) :
      correct ? alpha(theme.palette.success.main, 0.1) :
      selected ? alpha(theme.palette.primary.main, 0.1) : 
      theme.palette.background.paper,
  }
}));

const FeedbackBox = styled(Box)(({ theme, correct }) => ({
  marginTop: theme.spacing(2),
  padding: theme.spacing(2),
  borderRadius: theme.shape.borderRadius,
  backgroundColor: correct 
    ? alpha(theme.palette.success.main, 0.1)
    : alpha(theme.palette.info.main, 0.1),
  border: `1px solid ${correct ? theme.palette.success.main : theme.palette.info.main}`,
}));

const InteractiveQuestionCard = ({ data, onInteract }) => {
  const theme = useTheme();
  const [selectedAnswer, setSelectedAnswer] = useState(data.userAnswer);
  const [showFeedback, setShowFeedback] = useState(data.showFeedback || false);

  const handleAnswerSelect = (optionIndex) => {
    if (showFeedback) return; // Prevent changing answer after feedback
    
    setSelectedAnswer(optionIndex);
    if (onInteract) {
      onInteract({ type: 'answer_selected', questionId: data.question, selectedIndex: optionIndex });
    }
  };

  const handleSubmit = () => {
    if (selectedAnswer === null || selectedAnswer === undefined || showFeedback) return;
    
    setShowFeedback(true);
    if (onInteract) {
      onInteract({ 
        type: 'answer_submitted', 
        questionId: data.question, 
        selectedIndex: selectedAnswer,
        correct: selectedAnswer === data.correct_option_index 
      });
    }
  };

  const isCorrect = selectedAnswer === data.correct_option_index;

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { 
      opacity: 1, 
      y: 0, 
      transition: { duration: 0.3 } 
    }
  };

  const optionVariants = {
    hidden: { opacity: 0, x: -10 },
    visible: i => ({ 
      opacity: 1, 
      x: 0, 
      transition: { 
        delay: i * 0.1,
        duration: 0.2
      }
    }),
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <Container elevation={0}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <QuestionCategoryChip category={data.category} />
          <Box sx={{ flexGrow: 1 }} />
          {showFeedback && (
            <Tooltip title={isCorrect ? "Correct!" : "Incorrect"}>
              {isCorrect ? (
                <CheckCircleIcon sx={{ color: theme.palette.success.main }} />
              ) : (
                <CancelIcon sx={{ color: theme.palette.error.main }} />
              )}
            </Tooltip>
          )}
        </Box>

        <Typography variant="h6" sx={{ fontWeight: 500, mb: 2, lineHeight: 1.4 }}>
          {data.question}
        </Typography>

        <Box sx={{ mb: 2 }}>
          {data.options.map((option, index) => (
            <motion.div
              key={index}
              custom={index}
              variants={optionVariants}
              initial="hidden"
              animate="visible"
            >
              <OptionButton
                fullWidth
                variant="outlined"
                selected={selectedAnswer === index}
                correct={showFeedback && index === data.correct_option_index}
                incorrect={showFeedback && selectedAnswer === index && index !== data.correct_option_index}
                disabled={showFeedback}
                onClick={() => handleAnswerSelect(index)}
                startIcon={
                  showFeedback && index === data.correct_option_index ? (
                    <CheckCircleIcon fontSize="small" />
                  ) : showFeedback && selectedAnswer === index && index !== data.correct_option_index ? (
                    <CancelIcon fontSize="small" />
                  ) : null
                }
              >
                {option}
              </OptionButton>
            </motion.div>
          ))}
        </Box>

        {!showFeedback && selectedAnswer !== null && selectedAnswer !== undefined && (
          <Box sx={{ textAlign: 'center' }}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleSubmit}
              sx={{ px: 3 }}
            >
              Submit Answer
            </Button>
          </Box>
        )}

        {showFeedback && (
          <FeedbackBox correct={isCorrect}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              {isCorrect ? (
                <CheckCircleIcon sx={{ color: theme.palette.success.main }} />
              ) : (
                <CancelIcon sx={{ color: theme.palette.error.main }} />
              )}
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                {isCorrect ? 'Correct!' : 'Not quite right'}
              </Typography>
            </Box>
            <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
              {data.explanation}
            </Typography>
          </FeedbackBox>
        )}
      </Container>
    </motion.div>
  );
};

InteractiveQuestionCard.propTypes = {
  data: PropTypes.shape({
    question: PropTypes.string.isRequired,
    options: PropTypes.arrayOf(PropTypes.string).isRequired,
    correct_option_index: PropTypes.number.isRequired,
    explanation: PropTypes.string.isRequired,
    category: PropTypes.string.isRequired,
    userAnswer: PropTypes.number,
    showFeedback: PropTypes.bool,
  }).isRequired,
  onInteract: PropTypes.func,
};

export default InteractiveQuestionCard;
