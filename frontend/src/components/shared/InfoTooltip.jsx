import React from 'react';
import PropTypes from 'prop-types';
import {
  Tooltip,
  IconButton,
  Zoom
} from '@mui/material';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { helpTexts } from '../../constants/helpTexts';

/**
 * Reusable Tooltip component for displaying help text.
 * 
 * @param {Object} props Component props
 * @param {string} props.title The help text to display.
 * @param {string} [props.ariaLabel] Optional ARIA label for the icon button.
 * @param {'small' | 'medium' | 'large'} [props.size='small'] Size of the icon.
 * @param {object} [props.sx] Custom styles for the IconButton.
 * @returns {JSX.Element}
 */
const InfoTooltip = ({ 
  title, 
  ariaLabel = helpTexts.defaultInfoAlt,
  size = 'small', 
  sx = {} 
}) => {
  return (
    <Tooltip 
      title={title} 
      arrow 
      placement="top" 
      TransitionComponent={Zoom}
      enterDelay={300}
    >
      <IconButton 
        size={size}
        aria-label={ariaLabel}
        sx={{ 
          p: 0.5, // Add some padding
          color: 'text.secondary',
          '&:hover': {
            color: 'primary.main'
          },
          ...sx 
        }}
        tabIndex={-1} // Prevent tabbing to the icon itself
      >
        <InfoOutlinedIcon fontSize="inherit" />
      </IconButton>
    </Tooltip>
  );
};

InfoTooltip.propTypes = {
  title: PropTypes.node.isRequired,
  ariaLabel: PropTypes.string,
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  sx: PropTypes.object,
};

export default InfoTooltip; 