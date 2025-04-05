import React from 'react';
import PropTypes from 'prop-types';
import { 
  Box, 
  Typography, 
  Paper, 
  Button,
  useTheme,
  alpha
} from '@mui/material';
import UpdateIcon from '@mui/icons-material/Update';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import CollectionsBookmarkIcon from '@mui/icons-material/CollectionsBookmark';
import BookmarkIcon from '@mui/icons-material/Bookmark';
import { motion } from 'framer-motion';

/**
 * Reusable placeholder component for future content types
 * 
 * @param {Object} props Component props
 * @param {string} props.title Title of the placeholder
 * @param {string} props.description Description of the future content
 * @param {string} props.type Type of content ('exercises', 'resources', 'references')
 * @param {node} props.icon Custom icon to display
 * @param {boolean} props.compact Whether to display in compact mode
 * @returns {JSX.Element} PlaceholderContent component
 */
const PlaceholderContent = ({ 
  title = 'Coming Soon', 
  description = 'This content will be available in a future update.', 
  type = 'generic',
  icon: CustomIcon,
  compact = false
}) => {
  const theme = useTheme();
  
  // Set colors and icons based on content type
  const getTypeConfig = () => {
    switch (type) {
      case 'exercises':
        return {
          color: theme.palette.success.main,
          backgroundColor: alpha(theme.palette.success.main, 0.08),
          borderColor: alpha(theme.palette.success.main, 0.25),
          icon: <FitnessCenterIcon sx={{ fontSize: compact ? 24 : 40 }} />,
          label: 'Interactive exercises'
        };
      case 'resources':
        return {
          color: theme.palette.info.main,
          backgroundColor: alpha(theme.palette.info.main, 0.08),
          borderColor: alpha(theme.palette.info.main, 0.25),
          icon: <CollectionsBookmarkIcon sx={{ fontSize: compact ? 24 : 40 }} />,
          label: 'Additional resources'
        };
      case 'references':
        return {
          color: theme.palette.warning.main,
          backgroundColor: alpha(theme.palette.warning.main, 0.08),
          borderColor: alpha(theme.palette.warning.main, 0.25),
          icon: <BookmarkIcon sx={{ fontSize: compact ? 24 : 40 }} />,
          label: 'Reference materials'
        };
      default:
        return {
          color: theme.palette.primary.main,
          backgroundColor: alpha(theme.palette.primary.main, 0.08),
          borderColor: alpha(theme.palette.primary.main, 0.25),
          icon: <UpdateIcon sx={{ fontSize: compact ? 24 : 40 }} />,
          label: 'Additional content'
        };
    }
  };
  
  const typeConfig = getTypeConfig();
  const displayIcon = CustomIcon || typeConfig.icon;

  // Animation variants
  const containerVariants = {
    initial: { opacity: 0, y: 10 },
    animate: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: 0.5,
        ease: 'easeOut'
      }
    }
  };

  return (
    <motion.div
      initial="initial"
      animate="animate"
      variants={containerVariants}
    >
      <Paper
        elevation={0}
        sx={{
          p: compact ? 2 : 3,
          borderRadius: 2,
          border: '1px dashed',
          borderColor: typeConfig.borderColor,
          backgroundColor: typeConfig.backgroundColor,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          minHeight: compact ? 'auto' : 200
        }}
      >
        <Box 
          sx={{ 
            color: typeConfig.color,
            mb: compact ? 1 : 2 
          }}
        >
          {displayIcon}
        </Box>
        
        <Typography 
          variant={compact ? "subtitle1" : "h6"} 
          component="h3" 
          color="textPrimary"
          sx={{ 
            mb: compact ? 0.5 : 1,
            fontWeight: 600
          }}
        >
          {title}
        </Typography>
        
        <Typography 
          variant="body2" 
          color="textSecondary"
          sx={{ 
            mb: compact ? 1.5 : 2.5,
            maxWidth: compact ? '100%' : '80%',
            mx: 'auto'
          }}
        >
          {description}
        </Typography>
        
        {!compact && (
          <Button 
            variant="outlined"
            size="small"
            color="inherit"
            disabled
            startIcon={<UpdateIcon fontSize="small" />}
            sx={{ 
              opacity: 0.7,
              borderColor: typeConfig.color,
              color: typeConfig.color,
              '&.Mui-disabled': {
                borderColor: alpha(typeConfig.color, 0.5),
                color: alpha(typeConfig.color, 0.7),
              }
            }}
          >
            Coming soon
          </Button>
        )}
      </Paper>
    </motion.div>
  );
};

PlaceholderContent.propTypes = {
  title: PropTypes.string,
  description: PropTypes.string,
  type: PropTypes.oneOf(['exercises', 'resources', 'references', 'generic']),
  icon: PropTypes.node,
  compact: PropTypes.bool
};

export default PlaceholderContent; 