import React from 'react';
import PropTypes from 'prop-types';
import Typography from '@mui/material/Typography';
import MarkdownRenderer from './MarkdownRenderer';

/**
 * MarkdownInline
 *
 * Small wrapper around MarkdownRenderer that:
 * - Disables generation of TOC header IDs (enableTocIds=false)
 * - Wraps the rendered markdown with MUI Typography so callers can control
 *   typography variants consistently across the app
 *
 * Usage:
 * <MarkdownInline variant="body2">Some *markdown* text</MarkdownInline>
 */
const MarkdownInline = ({ children, variant = 'body1', className = '', sx = {}, ...rest }) => {
  if (children == null || children === '') return null;

  return (
    <Typography variant={variant} component="div" className={className} sx={sx}>
      <MarkdownRenderer enableTocIds={false} {...rest}>
        {children}
      </MarkdownRenderer>
    </Typography>
  );
};

MarkdownInline.propTypes = {
  children: PropTypes.node,
  variant: PropTypes.string,
  className: PropTypes.string,
  sx: PropTypes.object,
};

export default MarkdownInline;
