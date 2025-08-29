import React from 'react';
import PropTypes from 'prop-types';
import { 
  Box, 
  Typography, 
  List, 
  ListItem, 
  ListItemButton, 
  ListItemText, 
  Collapse, 
  IconButton, 
  Tooltip, 
  useTheme,
  Divider
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import TocIcon from '@mui/icons-material/Toc';

/**
 * Table of Contents component for submodule content navigation
 * Provides responsive design for both desktop sidebar and mobile drawer layouts
 */
const SubmoduleTableOfContents = ({
  headers,
  activeHeaderId,
  onHeaderClick,
  isMobile = false,
  isCollapsed = false,
  onToggleCollapse,
  title = "Table of Contents",
  maxHeight = '400px'
}) => {
  const theme = useTheme();

  // Animation variants for the TOC container
  const containerVariants = {
    hidden: { opacity: 0, x: isMobile ? 0 : -20 },
    visible: {
      opacity: 1,
      x: 0,
      transition: {
        duration: 0.3,
        staggerChildren: 0.05
      }
    },
    exit: { 
      opacity: 0, 
      x: isMobile ? 0 : -20,
      transition: { duration: 0.2 }
    }
  };

  // Animation variants for individual header items
  const itemVariants = {
    hidden: { opacity: 0, x: -10 },
    visible: { 
      opacity: 1, 
      x: 0,
      transition: { duration: 0.2 }
    }
  };

  // Get indentation level based on header level
  const getIndentLevel = (level) => {
    // h1 = 0, h2 = 1, h3 = 2, etc. (max 3 levels of indentation)
    return Math.min(level - 1, 3);
  };

  // Handle header click with optional mobile drawer close
  const handleHeaderClick = (headerId) => {
    onHeaderClick(headerId);
  };

  // If no headers, don't render anything
  if (!headers || headers.length === 0) {
    return null;
  }

  const tocContent = (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
    >
      <Box
        sx={{
          width: '100%',
          maxHeight: isMobile ? 'none' : maxHeight,
          overflowY: isMobile ? 'visible' : 'auto',
          borderRadius: theme.shape.borderRadius,
          bgcolor: isMobile ? 'transparent' : theme.palette.background.paper,
          border: isMobile ? 'none' : `1px solid ${theme.palette.divider}`,
          ...(isMobile ? {} : {
            '&::-webkit-scrollbar': {
              width: '4px',
            },
            '&::-webkit-scrollbar-track': {
              backgroundColor: 'transparent',
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: theme.palette.divider,
              borderRadius: '2px',
            },
          })
        }}
      >
        {/* Header */}
        <Box
          sx={{
            p: isMobile ? 0 : 2,
            borderBottom: isMobile ? 'none' : `1px solid ${theme.palette.divider}`,
            bgcolor: isMobile ? 'transparent' : theme.palette.background.default,
            display: 'flex',
            alignItems: 'center',
            justifyContent: isCollapsed ? 'center' : 'space-between',
            minHeight: isCollapsed ? '48px' : 'auto'
          }}
        >
          {!isCollapsed && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TocIcon sx={{ color: theme.palette.primary.main, fontSize: '1.2rem' }} />
              <Typography 
                variant={isMobile ? "h6" : "subtitle2"} 
                sx={{ 
                  fontWeight: theme.typography.fontWeightMedium,
                  color: theme.palette.text.primary
                }}
              >
                {title}
              </Typography>
            </Box>
          )}
          
          {!isMobile && onToggleCollapse && (
            <Tooltip title={isCollapsed ? "Expand Table of Contents" : "Collapse Table of Contents"}>
              <IconButton
                size="small"
                onClick={onToggleCollapse}
                sx={{ 
                  p: 0.5,
                  ...(isCollapsed && {
                    position: 'absolute',
                    left: '50%',
                    transform: 'translateX(-50%)'
                  })
                }}
              >
                {isCollapsed ? <ExpandMoreIcon /> : <ExpandLessIcon />}
              </IconButton>
            </Tooltip>
          )}
        </Box>

        {/* TOC List */}
        <Collapse in={!isCollapsed} timeout="auto" unmountOnExit>
          <List
            dense
            sx={{
              p: isMobile ? 1 : 1.5,
              '& .MuiListItem-root': {
                px: 0,
                py: 0.25
              }
            }}
          >
            {headers.map((header, index) => {
              const isActive = header.id === activeHeaderId;
              const indentLevel = getIndentLevel(header.level);

              return (
                <motion.div key={header.id} variants={itemVariants}>
                  <ListItem disablePadding>
                    <ListItemButton
                      selected={isActive}
                      onClick={() => handleHeaderClick(header.id)}
                      sx={{
                        pl: indentLevel * 2 + 1,
                        pr: 1,
                        py: 0.5,
                        borderRadius: theme.shape.borderRadius / 2,
                        minHeight: 'auto',
                        '&.Mui-selected': {
                          backgroundColor: theme.palette.primary.main + '15',
                          borderLeft: `3px solid ${theme.palette.primary.main}`,
                          '&:hover': {
                            backgroundColor: theme.palette.primary.main + '20',
                          }
                        },
                        '&:hover': {
                          backgroundColor: theme.palette.action.hover,
                        },
                        transition: 'all 0.2s ease-in-out'
                      }}
                    >
                      <ListItemText
                        primary={header.title}
                        primaryTypographyProps={{
                          variant: header.level <= 2 ? 'body2' : 'caption',
                          sx: {
                            fontWeight: isActive 
                              ? theme.typography.fontWeightBold 
                              : header.level <= 2 
                                ? theme.typography.fontWeightMedium 
                                : theme.typography.fontWeightRegular,
                            color: isActive 
                              ? theme.palette.primary.main 
                              : header.level <= 2
                                ? theme.palette.text.primary
                                : theme.palette.text.secondary,
                            lineHeight: 1.3,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical'
                          }
                        }}
                      />
                    </ListItemButton>
                  </ListItem>
                  
                  {/* Add divider between major sections (h1, h2) */}
                  {header.level <= 2 && index < headers.length - 1 && headers[index + 1].level <= 2 && (
                    <Divider sx={{ my: 0.5, mx: 1 }} />
                  )}
                </motion.div>
              );
            })}
          </List>
        </Collapse>
      </Box>
    </motion.div>
  );

  return (
    <AnimatePresence mode="wait">
      {tocContent}
    </AnimatePresence>
  );
};

SubmoduleTableOfContents.propTypes = {
  headers: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      level: PropTypes.number.isRequired,
      title: PropTypes.string.isRequired,
      position: PropTypes.number
    })
  ).isRequired,
  activeHeaderId: PropTypes.string,
  onHeaderClick: PropTypes.func.isRequired,
  isMobile: PropTypes.bool,
  isCollapsed: PropTypes.bool,
  onToggleCollapse: PropTypes.func,
  title: PropTypes.string,
  maxHeight: PropTypes.string
};

export default SubmoduleTableOfContents;
