import React from 'react';
import PropTypes from 'prop-types';
import { 
  Box, 
  Typography, 
  List, 
  ListItem, 
  ListItemIcon,
  ListItemText,
  Divider,
  useTheme,
  alpha
} from '@mui/material';
import ArticleIcon from '@mui/icons-material/Article';
import VideoLibraryIcon from '@mui/icons-material/VideoLibrary';
import BookIcon from '@mui/icons-material/Book';
import LinkIcon from '@mui/icons-material/Link';
import CodeIcon from '@mui/icons-material/Code';
import SchoolIcon from '@mui/icons-material/School';
import { motion } from 'framer-motion';

// Import the placeholder component
import PlaceholderContent from './PlaceholderContent';

// Helper function to validate URLs
const isValidHttpUrl = (string) => {
  if (!string) return false; // Handle null or empty strings
  let url;
  try {
    url = new URL(string);
  } catch (_) {
    return false; // Invalid URL format
  }
  // Allow only http and https protocols for external resources
  return url.protocol === "http:" || url.protocol === "https:";
};

/**
 * Reusable component for displaying lists of resources
 * 
 * @param {Object} props Component props
 * @param {Array} props.resources Array of resource objects
 * @param {string} props.title Optional section title
 * @param {boolean} props.dividers Whether to show dividers between items
 * @param {string} props.emptyTitle Title to show when resources are empty
 * @param {string} props.emptyDescription Description to show when resources are empty
 * @returns {JSX.Element} ResourceList component
 */
const ResourceList = ({ 
  resources, 
  title, 
  dividers = true,
  emptyTitle = 'Additional Resources Coming Soon', 
  emptyDescription = 'This section will contain supplementary materials to enhance your learning experience.'
}) => {
  const theme = useTheme();
  
  // Get appropriate icon based on resource type
  const getResourceIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'article':
        return <ArticleIcon color="primary" />;
      case 'video':
        return <VideoLibraryIcon sx={{ color: theme.palette.warning.main }} />;
      case 'book':
        return <BookIcon sx={{ color: theme.palette.success.main }} />;
      case 'code':
        return <CodeIcon sx={{ color: theme.palette.info.main }} />;
      case 'course':
        return <SchoolIcon sx={{ color: theme.palette.secondary.main }} />;
      default:
        return <LinkIcon color="action" />;
    }
  };
  
  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { 
        staggerChildren: 0.1
      }
    }
  };
  
  const itemVariants = {
    hidden: { opacity: 0, x: -5 },
    visible: { 
      opacity: 1, 
      x: 0,
      transition: { duration: 0.3 }
    }
  };
  
  // If no resources provided, show placeholder
  if (!resources || resources.length === 0) {
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
        <PlaceholderContent 
          title={emptyTitle}
          description={emptyDescription}
          type="resources"
        />
      </Box>
    );
  }
  
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
      
      <motion.div
        initial="hidden"
        animate="visible"
        variants={containerVariants}
      >
        <List 
          sx={{ 
            width: '100%',
            bgcolor: 'background.paper',
            borderRadius: 2,
            border: '1px solid',
            borderColor: theme.palette.divider,
            overflow: 'hidden'
          }}
        >
          {resources.map((resource, index) => {
            // Validate URL before using it
            const isUrlValid = isValidHttpUrl(resource.url);
            const safeUrl = isUrlValid ? resource.url : undefined; // Use undefined if invalid
            const componentType = safeUrl ? "a" : "div"; // Render as 'a' only if URL is valid
            
            return (
              <React.Fragment key={index}>
                <motion.div variants={itemVariants}>
                  <ListItem 
                    button 
                    component={componentType}
                    href={safeUrl}
                    target={safeUrl ? "_blank" : undefined}
                    rel={safeUrl ? "noopener noreferrer" : undefined}
                    sx={{ 
                      py: 1.5,
                      px: 2,
                      '&:hover': {
                        bgcolor: alpha(theme.palette.primary.main, 0.05)
                      }
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 40 }}>
                      {getResourceIcon(resource.type)}
                    </ListItemIcon>
                    <ListItemText 
                      primary={
                        <Typography variant="body1" fontWeight={500}>
                          {resource.title}
                        </Typography>
                      }
                      secondary={resource.description}
                      primaryTypographyProps={{ 
                        color: 'textPrimary',
                        variant: 'subtitle2'
                      }}
                      secondaryTypographyProps={{ 
                        color: 'textSecondary',
                        variant: 'body2',
                        sx: { mt: 0.5 }
                      }}
                    />
                  </ListItem>
                </motion.div>
                
                {dividers && index < resources.length - 1 && (
                  <Divider component="li" />
                )}
              </React.Fragment>
            );
          })}
        </List>
      </motion.div>
    </Box>
  );
};

ResourceList.propTypes = {
  resources: PropTypes.arrayOf(
    PropTypes.shape({
      title: PropTypes.string.isRequired,
      description: PropTypes.string,
      type: PropTypes.string,
      url: PropTypes.string
    })
  ),
  title: PropTypes.string,
  dividers: PropTypes.bool,
  emptyTitle: PropTypes.string,
  emptyDescription: PropTypes.string
};

export default ResourceList; 