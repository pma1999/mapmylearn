import React from 'react';
import PropTypes from 'prop-types';
import { Chip, Tooltip } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import QuizIcon from '@mui/icons-material/Quiz';
import PollIcon from '@mui/icons-material/Poll';
import FlashOnIcon from '@mui/icons-material/FlashOn';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';

const categoryIconMap = {
  knowledge_check: <QuizIcon fontSize="inherit" />,
  opinion_poll: <PollIcon fontSize="inherit" />,
  quick_quiz: <FlashOnIcon fontSize="inherit" />,
  fact_or_fiction: <HelpOutlineIcon fontSize="inherit" />,
};

const normalizeCategory = (cat) => (cat || '').toLowerCase();

const QuestionCategoryChip = ({ category, size = 'small', variant = 'soft' }) => {
  const theme = useTheme();
  const normalized = normalizeCategory(category);
  const icon = categoryIconMap[normalized] || <QuizIcon fontSize="inherit" />;
  const label = (normalized || 'question').replace('_', ' ');

  const catPalette = theme.palette?.questionCategories?.[normalized];
  const bg = catPalette?.bg || theme.palette.action.hover;
  const fg = catPalette?.main || theme.palette.text.primary;

  return (
    <Tooltip title={`Question type: ${label}`}> 
      <Chip
        icon={icon}
        label={label}
        size={size}
        variant={variant}
        sx={{ 
          textTransform: 'capitalize', 
          backgroundColor: bg, 
          color: fg, 
          '& .MuiChip-icon': { color: fg },
          fontWeight: 500
        }}
      />
    </Tooltip>
  );
};

QuestionCategoryChip.propTypes = {
  category: PropTypes.string,
  size: PropTypes.oneOf(['small', 'medium']),
  variant: PropTypes.oneOf(['soft', 'outlined', 'filled']),
};

export default QuestionCategoryChip;
