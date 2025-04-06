import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { 
  Box, 
  Typography, 
  Button, 
  Collapse,
  Paper,
  Divider,
  alpha,
  useTheme,
  CircularProgress,
  Skeleton
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import CollectionsBookmarkIcon from '@mui/icons-material/CollectionsBookmark';
import ArticleIcon from '@mui/icons-material/Article';
import VideoLibraryIcon from '@mui/icons-material/VideoLibrary';
import BookIcon from '@mui/icons-material/Book';
import { motion } from 'framer-motion';

// Import the ResourceList component
import ResourceList from './ResourceList';
import PlaceholderContent from './PlaceholderContent';

/**
 * A reusable component for displaying resources at different levels (topic, module, submodule)
 * 
 * @param {Object} props Component props
 * @param {Array} props.resources Array of resource objects
 * @param {string} props.title Title of the resources section
 * @param {string} props.type Type of resources (topic, module, submodule)
 * @param {boolean} props.isLoading Whether resources are loading
 * @param {boolean} props.collapsible Whether the section is collapsible
 * @param {boolean} props.expanded Initial expanded state (if collapsible)
 * @param {boolean} props.compact Whether to use compact layout
 * @param {string} props.emptyTitle Title to show when no resources
 * @param {string} props.emptyDescription Description to show when no resources
 * @returns {JSX.Element} ResourcesSection component
 */
const ResourcesSection = ({ 
  resources, 
  title = 'Additional Resources',
  type = 'topic',
  isLoading = false,
  collapsible = false,
  expanded = true, 
  compact = false,
  emptyTitle,
  emptyDescription 
}) => {
  const theme = useTheme();
  const [isExpanded, setIsExpanded] = useState(expanded);
  
  // Set appropriate default empty state messages based on type
  const defaultEmptyTitle = type === 'topic' 
    ? 'Learning Path Resources Coming Soon'
    : type === 'module'
      ? 'Module Resources Coming Soon'
      : 'Additional Resources Coming Soon';
      
  const defaultEmptyDescription = type === 'topic'
    ? 'This section will contain curated resources for the entire learning path, including reading lists, video lectures, practice problems, and tools related to this topic.'
    : type === 'module'
      ? 'This section will contain resources specific to this module, including recommended readings, videos, and reference materials.'
      : 'This section will contain supplementary materials specifically relevant to this subtopic.';
  
  // Use provided empty messages or defaults
  const finalEmptyTitle = emptyTitle || defaultEmptyTitle;
  const finalEmptyDescription = emptyDescription || defaultEmptyDescription;
  
  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: 0.5,
        ease: 'easeOut'
      }
    }
  };
  
  // Handle toggle expand/collapse
  const handleToggle = () => {
    setIsExpanded(!isExpanded);
  };
  
  // Get appropriate icon based on resource type
  const getSectionIcon = () => {
    switch (type) {
      case 'topic':
        return <CollectionsBookmarkIcon fontSize={compact ? "medium" : "large"} />;
      case 'module':
        return <BookIcon fontSize={compact ? "medium" : "large"} />;
      case 'submodule':
        return <ArticleIcon fontSize={compact ? "medium" : "large"} />;
      default:
        return <CollectionsBookmarkIcon fontSize={compact ? "medium" : "large"} />;
    }
  };
  
  // Generate loading skeleton
  const renderLoadingSkeleton = () => (
    <Box sx={{ mt: 2 }}>
      <Skeleton variant="rectangular" width="100%" height={60} sx={{ borderRadius: 1, mb: 2 }} />
      <Skeleton variant="rectangular" width="100%" height={60} sx={{ borderRadius: 1, mb: 2 }} />
      <Skeleton variant="rectangular" width="100%" height={60} sx={{ borderRadius: 1 }} />
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
        <CircularProgress size={24} />
      </Box>
    </Box>
  );
  
  // Determine if we should show content (either loading or content area)
  const showContent = isLoading || isExpanded || !collapsible;
  
  // Determine outer container styling based on type and compact mode
  const getContainerSx = () => {
    // Base styles common to all types
    const baseStyles = { 
      borderRadius: 2,
      overflow: 'hidden'
    };
    
    // Type-specific styles
    switch (type) {
      case 'topic':
        return { 
          ...baseStyles,
          p: compact ? 2 : 3,
          border: '1px solid',
          borderColor: 'divider',
          bgcolor: 'background.paper',
          boxShadow: compact ? 0 : 1
        };
      case 'module':
        return {
          ...baseStyles,
          p: compact ? 1.5 : 2,
          mt: 3,
          border: '1px solid',
          borderColor: theme.palette.divider,
          bgcolor: alpha(theme.palette.background.paper, 0.6)
        };
      case 'submodule':
        return {
          ...baseStyles,
          p: compact ? 1 : 2,
          mt: 2,
          bgcolor: alpha(theme.palette.background.paper, 0.4)
        };
      default:
        return baseStyles;
    }
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      <Paper 
        elevation={0} 
        sx={getContainerSx()}
      >
        <Box 
          sx={{ 
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: showContent ? 2 : 0
          }}
        >
          <Typography 
            variant={compact ? "subtitle1" : "h6"} 
            component="h3" 
            sx={{ 
              fontWeight: 600,
              color: type === 'topic' ? 'primary.main' : 'text.primary',
              display: 'flex',
              alignItems: 'center',
              gap: 1
            }}
          >
            {getSectionIcon()}
            {title}
          </Typography>
          
          {collapsible && (
            <Button
              size="small"
              variant={compact ? "text" : "outlined"}
              color="primary"
              startIcon={isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              onClick={handleToggle}
            >
              {isExpanded ? 'Hide' : 'Show'}
            </Button>
          )}
        </Box>
        
        {(type === 'topic' && showContent) && (
          <Divider sx={{ mb: 2 }} />
        )}
        
        <Collapse in={showContent} timeout="auto" unmountOnExit>
          <Box>
            {isLoading ? (
              renderLoadingSkeleton()
            ) : (
              resources && resources.length > 0 ? (
                <ResourceList 
                  resources={resources} 
                  dividers={!compact}
                />
              ) : (
                <PlaceholderContent 
                  title={finalEmptyTitle}
                  description={finalEmptyDescription}
                  type="resources"
                  compact={compact}
                />
              )
            )}
          </Box>
        </Collapse>
      </Paper>
    </motion.div>
  );
};

ResourcesSection.propTypes = {
  resources: PropTypes.arrayOf(
    PropTypes.shape({
      title: PropTypes.string.isRequired,
      description: PropTypes.string,
      url: PropTypes.string,
      type: PropTypes.string
    })
  ),
  title: PropTypes.string,
  type: PropTypes.oneOf(['topic', 'module', 'submodule']),
  isLoading: PropTypes.bool,
  collapsible: PropTypes.bool,
  expanded: PropTypes.bool,
  compact: PropTypes.bool,
  emptyTitle: PropTypes.string,
  emptyDescription: PropTypes.string
};

export default ResourcesSection; 