import React from 'react';
import PropTypes from 'prop-types';
import { Chip, Tooltip } from '@mui/material';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import TipsAndUpdatesIcon from '@mui/icons-material/TipsAndUpdates';
import PsychologyIcon from '@mui/icons-material/Psychology';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import HistoryEduIcon from '@mui/icons-material/HistoryEdu';
import ScienceIcon from '@mui/icons-material/Science';

const categoryIconMap = {
  fun_fact: <LightbulbIcon fontSize="inherit" />,
  key_insight: <PsychologyIcon fontSize="inherit" />,
  best_practice: <TipsAndUpdatesIcon fontSize="inherit" />,
  common_pitfall: <ReportProblemIcon fontSize="inherit" />,
  myth_buster: <PsychologyIcon fontSize="inherit" />,
  historical_context: <HistoryEduIcon fontSize="inherit" />,
  practical_tip: <TipsAndUpdatesIcon fontSize="inherit" />,
  advanced_nugget: <ScienceIcon fontSize="inherit" />,
};

const normalizeCategory = (cat) => (cat || '').toLowerCase();

const CuriosityCategoryChip = ({ category, size = 'small', variant = 'soft' }) => {
  const normalized = normalizeCategory(category);
  const icon = categoryIconMap[normalized] || <LightbulbIcon fontSize="inherit" />;
  const label = (normalized || 'insight').replace('_', ' ');

  return (
    <Tooltip title={`Category: ${label}`}> 
      <Chip
        icon={icon}
        label={label}
        size={size}
        variant={variant}
        sx={{ textTransform: 'capitalize' }}
      />
    </Tooltip>
  );
};

CuriosityCategoryChip.propTypes = {
  category: PropTypes.string,
  size: PropTypes.oneOf(['small', 'medium']),
  variant: PropTypes.oneOf(['soft', 'outlined', 'filled']),
};

export default CuriosityCategoryChip;
