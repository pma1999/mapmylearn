import React from 'react';
import { Box } from '@mui/material';
import { Link as RouterLink } from 'react-router'; // Import RouterLink
import logoSrc from '../../assets/images/logo.png'; // Ensure logo.png is placed here

/**
 * Renders the application logo.
 * Can be wrapped in a link or used standalone.
 * Allows overriding default dimensions and applying custom styles.
 */
const Logo = ({ width, height = 32, sx, linkTo = null }) => {
  const defaultStyles = {
    height: height,
    width: width || 'auto', // Default to auto width if only height is set
    verticalAlign: 'middle', // Helps with alignment if placed inline
  };

  const img = (
    <Box
      component="img"
      src={logoSrc}
      alt="MapMyLearn Logo"
      sx={{ ...defaultStyles, ...sx }} // Merge default and custom styles
    />
  );

  // If linkTo prop is provided, wrap the image in a RouterLink
  if (linkTo) {
    return (
      <RouterLink to={linkTo} aria-label="MapMyLearn homepage" style={{ textDecoration: 'none', color: 'inherit', display: 'inline-block' }}>
        {img}
      </RouterLink>
    );
  }

  // Otherwise, return the image directly
  return img;
};

export default Logo; 