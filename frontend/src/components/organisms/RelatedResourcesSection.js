import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Divider,
  IconButton,
  useTheme,
  Grid,
  Card,
  CardContent,
  CardMedia
} from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import LinkIcon from '@mui/icons-material/Link';
import { motion } from 'framer-motion';

// This component serves as a placeholder for future resource types
// such as videos, books, external resources, etc.
const RelatedResourcesSection = ({ enabled = false }) => {
  const theme = useTheme();
  
  if (!enabled) return null;
  
  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: 0.5,
        staggerChildren: 0.1,
        delayChildren: 0.2 
      }
    }
  };
  
  const itemVariants = {
    hidden: { opacity: 0, x: -10 },
    visible: { 
      opacity: 1, 
      x: 0,
      transition: { duration: 0.3 }
    }
  };

  // Placeholder content for the future
  const placeholderResources = [
    {
      id: 1,
      type: 'video',
      title: 'Introduction to the Topic',
      description: 'A comprehensive video tutorial covering fundamental concepts',
      icon: <PlayArrowIcon />
    },
    {
      id: 2,
      type: 'book',
      title: 'Recommended Reading',
      description: 'Essential literature that expands on module content',
      icon: <MenuBookIcon />
    },
    {
      id: 3,
      type: 'link',
      title: 'External Resources',
      description: 'Curated websites, documentation and articles',
      icon: <LinkIcon />
    }
  ];

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      <Paper 
        elevation={2} 
        sx={{ 
          p: { xs: 2, sm: 3 }, 
          borderRadius: 2,
          mb: 4,
          background: `linear-gradient(145deg, ${theme.palette.secondary.light}10, ${theme.palette.background.paper})`,
          border: `1px dashed ${theme.palette.secondary.light}`
        }}
      >
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          mb: 2
        }}>
          <Typography 
            variant="h5" 
            component="h2" 
            color="secondary.dark"
            sx={{ 
              fontWeight: 600,
              fontSize: { xs: '1.2rem', sm: '1.4rem' }
            }}
          >
            Related Resources
          </Typography>
          
          <IconButton 
            size="small" 
            color="secondary"
            aria-label="resource information"
            sx={{ border: `1px solid ${theme.palette.secondary.main}` }}
          >
            <InfoIcon fontSize="small" />
          </IconButton>
        </Box>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          This section will contain additional resources like videos, books, 
          and external links related to your learning path.
        </Typography>
        
        <Divider sx={{ mb: 3 }} />
        
        <Grid container spacing={2}>
          {placeholderResources.map((resource) => (
            <Grid item xs={12} sm={6} md={4} key={resource.id}>
              <motion.div variants={itemVariants}>
                <Card 
                  variant="outlined" 
                  sx={{ 
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    borderRadius: 2,
                    transition: 'all 0.3s ease',
                    borderColor: 'grey.300',
                    '&:hover': {
                      borderColor: theme.palette.secondary.main,
                      transform: 'translateY(-4px)',
                      boxShadow: '0 4px 10px rgba(0,0,0,0.08)'
                    }
                  }}
                >
                  <Box 
                    sx={{ 
                      bgcolor: 'secondary.light', 
                      color: 'secondary.contrastText',
                      p: 1.5,
                      display: 'flex',
                      alignItems: 'center'
                    }}
                  >
                    {resource.icon}
                    <Typography 
                      variant="subtitle2" 
                      sx={{ ml: 1, fontWeight: 600 }}
                    >
                      {resource.type.toUpperCase()}
                    </Typography>
                  </Box>
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Typography 
                      variant="h6" 
                      gutterBottom
                      sx={{ 
                        fontSize: { xs: '1rem', sm: '1.1rem' },
                        fontWeight: 500
                      }}
                    >
                      {resource.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {resource.description}
                    </Typography>
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>
          ))}
        </Grid>
      </Paper>
    </motion.div>
  );
};

export default RelatedResourcesSection; 