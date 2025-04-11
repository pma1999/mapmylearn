import React, { useState } from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Box, 
  Chip, 
  Divider,
  IconButton,
  Collapse,
  Stack,
  useTheme,
  useMediaQuery,
  Button
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import CollectionsBookmarkIcon from '@mui/icons-material/CollectionsBookmark';
import { motion } from 'framer-motion';

// Import SubmoduleCard component
import SubmoduleCard from './SubmoduleCard';
// Import ResourcesSection instead of PlaceholderContent
import ResourcesSection from '../shared/ResourcesSection';

const ModuleCard = ({ module, index, pathId }) => {
  const [expanded, setExpanded] = useState(index === 0);
  const [showResources, setShowResources] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const handleExpandClick = () => {
    setExpanded(!expanded);
  };
  
  const handleResourcesToggle = () => {
    setShowResources(!showResources);
  };
  
  // Animation variants
  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: 0.5,
        delay: index * 0.1 
      }
    }
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={cardVariants}
    >
      <Card 
        elevation={3} 
        sx={{ 
          mb: 3,
          borderRadius: 2,
          overflow: 'visible',
          transition: 'all 0.3s ease',
          '&:hover': {
            boxShadow: theme.shadows[6]
          }
        }}
      >
        <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
          <Box 
            sx={{ 
              display: 'flex', 
              justifyContent: 'space-between',
              alignItems: 'center',
              cursor: 'pointer'
            }}
            onClick={handleExpandClick}
          >
            <Typography 
              variant="h5" 
              component="h2" 
              sx={{ 
                fontWeight: 600,
                fontSize: { xs: '1.2rem', sm: '1.4rem', md: '1.5rem' },
                color: theme.palette.primary.main
              }}
            >
              Module {index + 1}: {module.title}
            </Typography>
            <IconButton
              onClick={(e) => {
                e.stopPropagation();
                handleExpandClick();
              }}
              aria-expanded={expanded}
              aria-label="show more"
              sx={{
                transform: expanded ? 'rotate(0deg)' : 'rotate(180deg)',
                transition: 'transform 0.3s',
                ml: 2
              }}
            >
              {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>
          
          <Collapse in={expanded} timeout="auto" unmountOnExit>
            <Box sx={{ mt: 2 }}>
              <Typography 
                variant="body1" 
                color="text.secondary"
                sx={{ 
                  mb: 2,
                  lineHeight: 1.7,
                  fontSize: { xs: '0.9rem', sm: '1rem' }
                }}
              >
                {module.description}
              </Typography>
              
              {module.prerequisites && module.prerequisites.length > 0 && (
                <Box sx={{ mb: 3 }}>
                  <Typography 
                    variant="subtitle1" 
                    sx={{ 
                      fontWeight: 600,
                      mb: 1.5,
                      fontSize: { xs: '0.9rem', sm: '1rem' }
                    }}
                  >
                    Prerequisites:
                  </Typography>
                  <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                    {module.prerequisites.map((prereq, idx) => (
                      <Chip
                        key={idx}
                        label={prereq}
                        size="small"
                        color="secondary"
                        variant="outlined"
                        sx={{ 
                          m: 0.5,
                          borderRadius: '16px'
                        }}
                      />
                    ))}
                  </Stack>
                </Box>
              )}
              
              <Divider sx={{ my: 3 }} />
              
              {module.submodules && module.submodules.length > 0 ? (
                <Box sx={{ mt: 2 }}>
                  <Typography 
                    variant="h6" 
                    sx={{ 
                      mb: 2,
                      fontWeight: 600,
                      fontSize: { xs: '1rem', sm: '1.2rem' }
                    }}
                  >
                    Submodules:
                  </Typography>
                  
                  <Stack spacing={2}>
                    {module.submodules.map((submodule, idx) => (
                      <SubmoduleCard 
                        key={idx} 
                        submodule={submodule} 
                        index={idx} 
                        moduleIndex={index}
                        pathId={pathId}
                      />
                    ))}
                  </Stack>
                </Box>
              ) : (
                module.content && (
                  <Box sx={{ mt: 3 }}>
                    <Typography variant="body1">
                      Content coming soon...
                    </Typography>
                  </Box>
                )
              )}
              
              {/* Module-level Resources Section - Updated to use ResourcesSection */}
              <ResourcesSection 
                resources={module.resources}
                title="Module Resources"
                type="module"
                collapsible={true}
                expanded={showResources}
                compact={isMobile}
              />
            </Box>
          </Collapse>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default ModuleCard; 