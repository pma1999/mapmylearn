import React from 'react';
import PropTypes from 'prop-types';
import { Fab, Tooltip, useTheme, Badge } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import TocIcon from '@mui/icons-material/Toc';
import ListIcon from '@mui/icons-material/List';

/**
 * Floating Action Button for opening Table of Contents on mobile
 * Only appears when content has headers and provides quick access to TOC
 */
const TOCFloatingButton = ({
  onOpen,
  hasHeaders = false,
  headerCount = 0,
  isVisible = true,
  variant = 'primary',
  size = 'medium',
  position = 'bottom-right'
}) => {
  const theme = useTheme();

  // Position variants for the FAB
  const positionStyles = {
    'bottom-right': {
      position: 'fixed',
      bottom: theme.spacing(12), // Above mobile bottom navigation
      right: theme.spacing(2),
      zIndex: theme.zIndex.speedDial
    },
    'bottom-left': {
      position: 'fixed',
      bottom: theme.spacing(12),
      left: theme.spacing(2),
      zIndex: theme.zIndex.speedDial
    },
    'top-right': {
      position: 'fixed',
      top: theme.spacing(10),
      right: theme.spacing(2),
      zIndex: theme.zIndex.speedDial
    }
  };

  // Animation variants for the FAB
  const fabVariants = {
    hidden: {
      scale: 0,
      opacity: 0,
      rotate: -180,
      transition: {
        duration: 0.3,
        ease: "easeInOut"
      }
    },
    visible: {
      scale: 1,
      opacity: 1,
      rotate: 0,
      transition: {
        duration: 0.4,
        ease: "easeOutBack",
        delay: 0.1
      }
    },
    hover: {
      scale: 1.1,
      transition: {
        duration: 0.2,
        ease: "easeInOut"
      }
    },
    tap: {
      scale: 0.95,
      transition: {
        duration: 0.1,
        ease: "easeInOut"
      }
    }
  };

  // Don't render if no headers or not visible
  if (!hasHeaders || !isVisible) {
    return null;
  }

  const buttonContent = (
    <motion.div
      variants={fabVariants}
      initial="hidden"
      animate="visible"
      exit="hidden"
      whileHover="hover"
      whileTap="tap"
      style={positionStyles[position]}
    >
      <Tooltip 
        title={`Table of Contents (${headerCount} section${headerCount !== 1 ? 's' : ''})`}
        arrow
        placement="left"
      >
        <Badge
          badgeContent={headerCount > 9 ? '9+' : headerCount}
          color="secondary"
          invisible={headerCount === 0}
          sx={{
            '& .MuiBadge-badge': {
              fontSize: '0.7rem',
              minWidth: '18px',
              height: '18px',
              borderRadius: '9px'
            }
          }}
        >
          <Fab
            color={variant}
            size={size}
            onClick={onOpen}
            sx={{
              boxShadow: theme.shadows[8],
              '&:hover': {
                boxShadow: theme.shadows[12],
                transform: 'translateY(-2px)'
              },
              '&:active': {
                boxShadow: theme.shadows[4],
                transform: 'translateY(0px)'
              },
              transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
              // Ensure button is accessible and visible
              backdropFilter: 'blur(10px)',
              backgroundColor: variant === 'primary' 
                ? theme.palette.primary.main 
                : theme.palette.secondary.main
            }}
            aria-label={`Open table of contents with ${headerCount} sections`}
          >
            {headerCount <= 3 ? <ListIcon /> : <TocIcon />}
          </Fab>
        </Badge>
      </Tooltip>
    </motion.div>
  );

  return (
    <AnimatePresence mode="wait">
      {buttonContent}
    </AnimatePresence>
  );
};

/**
 * Compact version of the TOC floating button for minimal interference
 */
export const TOCMiniButton = ({
  onOpen,
  hasHeaders = false,
  isVisible = true
}) => {
  const theme = useTheme();

  if (!hasHeaders || !isVisible) {
    return null;
  }

  return (
    <motion.div
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0, opacity: 0 }}
      transition={{ duration: 0.3 }}
      style={{
        position: 'fixed',
        top: theme.spacing(1),
        right: theme.spacing(1),
        zIndex: theme.zIndex.speedDial
      }}
    >
      <Tooltip title="Table of Contents" arrow placement="left">
        <Fab
          size="small"
          color="primary"
          onClick={onOpen}
          sx={{
            minHeight: '40px',
            width: '40px',
            height: '40px',
            boxShadow: theme.shadows[4],
            '&:hover': {
              boxShadow: theme.shadows[8]
            }
          }}
          aria-label="Open table of contents"
        >
          <TocIcon sx={{ fontSize: '1.1rem' }} />
        </Fab>
      </Tooltip>
    </motion.div>
  );
};

TOCFloatingButton.propTypes = {
  onOpen: PropTypes.func.isRequired,
  hasHeaders: PropTypes.bool,
  headerCount: PropTypes.number,
  isVisible: PropTypes.bool,
  variant: PropTypes.oneOf(['primary', 'secondary']),
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  position: PropTypes.oneOf(['bottom-right', 'bottom-left', 'top-right'])
};

TOCMiniButton.propTypes = {
  onOpen: PropTypes.func.isRequired,
  hasHeaders: PropTypes.bool,
  isVisible: PropTypes.bool
};

export default TOCFloatingButton;
