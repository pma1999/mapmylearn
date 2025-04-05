import React from 'react';
import PropTypes from 'prop-types';
import { 
  Box, 
  Typography, 
  Stack,
  useTheme
} from '@mui/material';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';

// Import the placeholder component 
import PlaceholderContent from './PlaceholderContent';

/**
 * Component for displaying exercises (currently placeholder)
 * This will be expanded in the future to show actual interactive exercises
 * 
 * @param {Object} props Component props
 * @param {Array} props.exercises Array of exercise objects (currently not used)
 * @param {string} props.title Optional section title
 * @returns {JSX.Element} ExerciseList component
 */
const ExerciseList = ({ 
  exercises = [], 
  title = 'Practice Exercises'
}) => {
  const theme = useTheme();
  
  return (
    <Box sx={{ mt: 2 }}>
      {title && (
        <Typography 
          variant="h6" 
          component="h3" 
          color="textPrimary"
          sx={{ mb: 2, fontWeight: 600 }}
        >
          {title}
        </Typography>
      )}
      
      <Stack spacing={3}>
        <PlaceholderContent 
          title="Interactive Exercises Coming Soon"
          description="This section will contain practice exercises to help you test your understanding and apply what you've learned."
          type="exercises"
          icon={<FitnessCenterIcon sx={{ fontSize: 40 }} />}
        />
        
        <Box sx={{ px: 2 }}>
          <Typography 
            variant="body2" 
            color="textSecondary" 
            sx={{ 
              fontStyle: 'italic',
              textAlign: 'center'
            }}
          >
            Future exercises will include multiple choice quizzes, code challenges, 
            and interactive problems to reinforce your learning.
          </Typography>
        </Box>
      </Stack>
    </Box>
  );
};

ExerciseList.propTypes = {
  exercises: PropTypes.array,
  title: PropTypes.string
};

export default ExerciseList; 