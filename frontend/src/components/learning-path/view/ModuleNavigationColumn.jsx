import React from 'react';
import PropTypes from 'prop-types';
import { Box, Typography, Paper, List, ListItem, ListItemButton, ListItemText, Collapse, useTheme, Chip, Stack, Checkbox, FormControlLabel, IconButton, Tooltip } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';

const ModuleNavigationColumn = ({ 
  modules, 
  activeModuleIndex, 
  setActiveModuleIndex,
  activeSubmoduleIndex,
  setActiveSubmoduleIndex,
  onSubmoduleSelect,
  progressMap,
  onToggleProgress
}) => {
  const theme = useTheme();

  const handleModuleClick = (index) => {
    setActiveModuleIndex(index === activeModuleIndex ? null : index);
    if (index !== activeModuleIndex) {
      setActiveSubmoduleIndex(0); 
    }
  };

  const handleSubmoduleClick = (modIndex, subIndex) => {
    setActiveModuleIndex(modIndex);
    setActiveSubmoduleIndex(subIndex);
    if (onSubmoduleSelect) {
      onSubmoduleSelect(modIndex, subIndex);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: { opacity: 1, x: 0 }
  };

  return (
    <Box 
      data-tut="module-navigation-column"
      component={motion.div} 
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      sx={{ 
        height: '100%',
        overflowY: 'auto',
        pr: 0.5,
        pb: 2,
        borderRight: { 
          xs: 'none', 
          md: `1px solid ${theme.palette.divider}` 
        },
      }}
    >
      <List component="nav" aria-labelledby="module-navigation-header" sx={{ p: { xs: 1, md: 1.5} }}>
        {modules.map((module, modIndex) => {
          const isActiveModule = modIndex === activeModuleIndex;
          return (
            <motion.div key={modIndex} variants={itemVariants}>
              <Paper 
                data-tut={modIndex === 0 ? "module-item-0" : undefined}
                variant="outlined"
                sx={{ 
                  mb: 1.5,
                  overflow: 'hidden',
                  borderColor: isActiveModule ? theme.palette.primary.main : theme.palette.divider,
                  borderWidth: isActiveModule ? '2px' : '1px',
                  transition: 'all 0.2s ease-in-out',
                  bgcolor: isActiveModule ? theme.palette.action.hover : 'transparent',
                  '&:hover': {
                     borderColor: theme.palette.primary.light,
                  }
                }}
              >
                <ListItemButton 
                  selected={isActiveModule} 
                  onClick={() => handleModuleClick(modIndex)}
                  sx={{ 
                    py: 1.5, 
                    px: 2,
                  }}
                >
                  <ListItemText 
                    primary={`Module ${modIndex + 1}: ${module.title}`}
                    primaryTypographyProps={{ 
                      fontWeight: isActiveModule ? theme.typography.fontWeightBold : theme.typography.fontWeightMedium,
                      variant: 'h6',
                      fontSize: '1.0rem',
                    }} 
                  />
                  {isActiveModule ? <ExpandLess /> : <ExpandMore />}
                </ListItemButton>
                <Collapse in={isActiveModule} timeout="auto" unmountOnExit>
                  <Box sx={{ p: 2, borderTop: `1px solid ${theme.palette.divider}` }}>
                     <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {module.description}
                     </Typography>
                     
                     {module.prerequisites && module.prerequisites.length > 0 && (
                       <Box sx={{ mb: 2 }}>
                         <Typography variant="caption" display="block" sx={{ fontWeight: theme.typography.fontWeightMedium, mb: 0.5 }}>Prerequisites:</Typography>
                         <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                           {module.prerequisites.map((prereq, idx) => (
                             <Chip key={idx} label={prereq} size="small" />
                           ))}
                         </Stack>
                       </Box>
                     )}

                     <Typography variant="subtitle2" sx={{ fontWeight: theme.typography.fontWeightBold, mb: 1 }}>Submodules:</Typography>
                     <List component="div" disablePadding>
                      {(module.submodules || []).map((submodule, subIndex) => {
                         const isActiveSubmodule = isActiveModule && subIndex === activeSubmoduleIndex;
                         const progressKey = `${modIndex}_${subIndex}`;
                         const isCompleted = progressMap[progressKey] || false;

                         const handleCheckboxClick = (event) => {
                            event.stopPropagation();
                            onToggleProgress(modIndex, subIndex);
                         };

                         return (
                           <ListItem 
                              key={subIndex} 
                              disablePadding
                              data-tut={modIndex === 0 && subIndex === 0 ? "submodule-item-0-0" : undefined}
                              secondaryAction={
                                 <Tooltip title={isCompleted ? "Mark as Incomplete" : "Mark as Complete"}>
                                     <Checkbox
                                         data-tut={modIndex === 0 && subIndex === 0 ? "progress-checkbox-0-0" : undefined}
                                         edge="end"
                                         checked={isCompleted}
                                         onChange={handleCheckboxClick}
                                         onClick={handleCheckboxClick}
                                         inputProps={{ 'aria-labelledby': `submodule-label-${modIndex}-${subIndex}` }}
                                         size="small"
                                         sx={{ 
                                             color: isCompleted ? theme.palette.success.main : theme.palette.action.active,
                                             '&.Mui-checked': {
                                                 color: theme.palette.success.main,
                                             },
                                             mr: -1
                                         }}
                                     />
                                 </Tooltip>
                              }
                              sx={{ 
                                 mb: 0.5, 
                                 borderLeft: isActiveSubmodule ? `3px solid ${theme.palette.secondary.main}` : 'none',
                                 backgroundColor: isActiveSubmodule ? theme.palette.action.selected : 'transparent',
                                 '&:hover': {
                                      backgroundColor: isActiveSubmodule ? theme.palette.action.selected : theme.palette.action.hover,
                                 }
                              }}
                           >
                             <ListItemButton 
                                dense 
                                selected={isActiveSubmodule}
                                onClick={() => handleSubmoduleClick(modIndex, subIndex)}
                                sx={{ pl: 2, py: 0.5 }}
                             >
                                 <ListItemText 
                                     id={`submodule-label-${modIndex}-${subIndex}`}
                                     primary={`${modIndex + 1}.${subIndex + 1} ${submodule.title}`} 
                                     primaryTypographyProps={{ 
                                     fontWeight: isActiveSubmodule ? theme.typography.fontWeightBold : theme.typography.fontWeightRegular, 
                                     variant: 'body2',
                                     color: isActiveSubmodule ? theme.palette.secondary.dark : theme.palette.text.primary,
                                     }}
                                     sx={{ 
                                         textDecoration: isCompleted ? 'line-through' : 'none', 
                                         color: isCompleted ? theme.palette.text.disabled : 'inherit' 
                                     }}
                                 />
                             </ListItemButton>
                           </ListItem>
                         );
                      })}
                     </List>
                     
                     {/* Optional: Add Module Resources Toggle/Link Here */}
                     {module.resources && module.resources.length > 0 && (
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                           {module.resources.length} module resource(s) available.
                        </Typography>
                     )}
                  </Box>
                </Collapse>
              </Paper>
            </motion.div>
          );
        })}
      </List>
    </Box>
  );
};

ModuleNavigationColumn.propTypes = {
  modules: PropTypes.array.isRequired,
  activeModuleIndex: PropTypes.number,
  setActiveModuleIndex: PropTypes.func.isRequired,
  activeSubmoduleIndex: PropTypes.number,
  setActiveSubmoduleIndex: PropTypes.func.isRequired,
  onSubmoduleSelect: PropTypes.func,
  progressMap: PropTypes.object.isRequired,
  onToggleProgress: PropTypes.func.isRequired,
};

export default ModuleNavigationColumn; 