import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Button, Alert } from '@mui/material';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import { motion, AnimatePresence } from 'framer-motion';

import QuizProgress from './QuizProgress';
import QuizQuestion from './QuizQuestion';
import QuizFeedback from './QuizFeedback';
import QuizSummary from './QuizSummary';

/**
 * Main container component for quiz functionality
 * Manages quiz state and orchestrates the quiz flow
 * 
 * @param {Object} props Component props
 * @param {Array} props.quizQuestions Array of quiz questions
 * @returns {JSX.Element} Quiz container component
 */
const QuizContainer = ({ quizQuestions }) => {
  // Quiz state
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [showFeedback, setShowFeedback] = useState(false);
  const [quizCompleted, setQuizCompleted] = useState(false);
  const [correctAnswers, setCorrectAnswers] = useState(0);

  // Ensure quizQuestions is an array
  const questions = Array.isArray(quizQuestions) ? quizQuestions : [];

  // Get current question
  const currentQuestion = questions[currentQuestionIndex];
  
  // Determine if there are any questions to display
  const hasQuestions = questions.length > 0;

  // Reset the quiz - clear all answers and start from the beginning
  const handleReset = () => {
    setCurrentQuestionIndex(0);
    setSelectedAnswers({});
    setShowFeedback(false);
    setQuizCompleted(false);
    setCorrectAnswers(0);
  };

  // Handle answer selection
  const handleAnswerSelect = (optionIndex) => {
    if (showFeedback) return; // Prevent changing answer after submission
    
    setSelectedAnswers({
      ...selectedAnswers,
      [currentQuestionIndex]: optionIndex
    });
  };

  // Check if current answer is correct
  const isCurrentAnswerCorrect = () => {
    if (selectedAnswers[currentQuestionIndex] === undefined || !currentQuestion) return false;
    
    const selectedOptionIndex = selectedAnswers[currentQuestionIndex];
    return currentQuestion.options[selectedOptionIndex]?.is_correct || false;
  };

  // Handle answer submission
  const handleSubmit = () => {
    if (!hasQuestions || showFeedback) return;
    
    setShowFeedback(true);
    
    // Update correct answer count if the current answer is correct
    if (isCurrentAnswerCorrect()) {
      setCorrectAnswers(prev => prev + 1);
    }
  };

  // Handle next question navigation
  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      setShowFeedback(false);
    } else if (showFeedback) {
      // If we're on the last question and feedback is shown, mark quiz as completed
      setQuizCompleted(true);
    }
  };

  // Handle previous question navigation
  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
      setShowFeedback(!!selectedAnswers[currentQuestionIndex - 1]);
    }
  };

  // Animation variants for smooth transitions
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { duration: 0.5 }
    },
    exit: { 
      opacity: 0,
      transition: { duration: 0.3 }
    }
  };

  // If there are no questions, show a message
  if (!hasQuestions) {
    return (
      <Alert severity="info" sx={{ mt: 2, borderRadius: 2 }}>
        No quiz questions available for this submodule.
      </Alert>
    );
  }

  // Render quiz summary if completed
  if (quizCompleted) {
    return (
      <QuizSummary
        correctAnswers={correctAnswers}
        totalQuestions={questions.length}
        onReset={handleReset}
      />
    );
  }

  // Render main quiz interface
  return (
    <Paper 
      elevation={0}
      sx={{ 
        p: 3, 
        borderRadius: 2,
        border: '1px solid',
        borderColor: 'divider' 
      }}
    >
      <AnimatePresence mode="wait">
        <motion.div
          key={currentQuestionIndex}
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
        >
          {/* Quiz header with question counter and reset button */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography 
              variant="h6" 
              component="h3"
              sx={{ fontWeight: 600 }}
            >
              Question {currentQuestionIndex + 1} of {questions.length}
            </Typography>
            
            <Button
              variant="outlined"
              color="secondary"
              size="small"
              startIcon={<RestartAltIcon />}
              onClick={handleReset}
              sx={{ ml: 2 }}
            >
              Restart
            </Button>
          </Box>
          
          {/* Progress bar */}
          <QuizProgress 
            current={currentQuestionIndex + 1} 
            total={questions.length}
            correct={correctAnswers}
          />
          
          {/* Current question */}
          <QuizQuestion
            question={currentQuestion}
            selectedOption={selectedAnswers[currentQuestionIndex]}
            onSelectOption={handleAnswerSelect}
            showFeedback={showFeedback}
          />
          
          {/* Feedback section visible after submission */}
          {showFeedback && (
            <QuizFeedback
              isCorrect={isCurrentAnswerCorrect()}
              explanation={currentQuestion.explanation}
            />
          )}
          
          {/* Navigation buttons */}
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            mt: 3,
            gap: 2
          }}>
            <Button
              variant="outlined"
              color="primary"
              disabled={currentQuestionIndex === 0}
              onClick={handlePrevious}
            >
              Previous
            </Button>
            
            {!showFeedback ? (
              <Button
                variant="contained"
                color="primary"
                disabled={selectedAnswers[currentQuestionIndex] === undefined}
                onClick={handleSubmit}
              >
                Check Answer
              </Button>
            ) : (
              <Button
                variant="contained"
                color="primary"
                onClick={handleNext}
              >
                {currentQuestionIndex < questions.length - 1 ? 'Next Question' : 'View Results'}
              </Button>
            )}
          </Box>
        </motion.div>
      </AnimatePresence>
    </Paper>
  );
};

export default QuizContainer; 