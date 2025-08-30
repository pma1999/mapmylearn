import React, { useCallback } from 'react';
import PropTypes from 'prop-types';
import {
  Box,
  Typography,
  FormControlLabel,
  Checkbox,
  Collapse,
  IconButton,
  Stack,
  Paper,
  Divider,
  Chip,
  Tooltip
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import FolderIcon from '@mui/icons-material/Folder';
import ArticleIcon from '@mui/icons-material/Article';
import LinkIcon from '@mui/icons-material/Link';
import { useState } from 'react';

/**
 * Hierarchical tree component for selecting modules and submodules
 * Provides an intuitive interface to choose specific content for export
 */
const ModuleSelectionTree = ({
  modules,
  selectedItems,
  onSelectionChange,
  includeResources = true,
  language = 'es'
}) => {
  const [expandedModules, setExpandedModules] = useState(
    // Initially expand all modules
    modules.reduce((acc, _, index) => {
      acc[index] = true;
      return acc;
    }, {})
  );

  const texts = {
    es: {
      module: 'Módulo',
      submodules: 'submódulos',
      resources: 'recursos',
      noSubmodules: 'Sin submódulos',
      noResources: 'Sin recursos adicionales'
    },
    en: {
      module: 'Module',
      submodules: 'submodules',
      resources: 'resources',
      noSubmodules: 'No submodules',
      noResources: 'No additional resources'
    }
  };

  const t = texts[language] || texts.en;

  // Handle module expansion/collapse
  const handleModuleToggle = (moduleIndex) => {
    setExpandedModules(prev => ({
      ...prev,
      [moduleIndex]: !prev[moduleIndex]
    }));
  };

  // Handle selection changes
  const handleSelectionChange = useCallback((itemKey, checked) => {
    const newSelection = { ...selectedItems };

    if (itemKey.startsWith('module_') && !itemKey.includes('sub_') && !itemKey.includes('resources')) {
      // Module selection - also affects submodules and resources
      const moduleIndex = parseInt(itemKey.split('_')[1]);
      newSelection[itemKey] = checked;

      // Update all submodules in this module
      const module = modules[moduleIndex];
      if (module.submodules) {
        module.submodules.forEach((_, subIndex) => {
          const subKey = `module_${moduleIndex}_sub_${subIndex}`;
          newSelection[subKey] = checked;
        });
      }

      // Update module resources
      if (module.resources && module.resources.length > 0) {
        const resourceKey = `module_${moduleIndex}_resources`;
        newSelection[resourceKey] = checked;
      }
    } else if (itemKey.includes('sub_')) {
      // Submodule selection
      newSelection[itemKey] = checked;
      
      // Check if we need to update parent module
      const moduleIndex = parseInt(itemKey.split('_')[1]);
      const module = modules[moduleIndex];
      const moduleKey = `module_${moduleIndex}`;
      
      if (checked) {
        // If any submodule is selected, module should be selected
        newSelection[moduleKey] = true;
      } else {
        // If no submodules are selected, uncheck module
        const hasSelectedSubmodules = module.submodules?.some((_, subIndex) => {
          const subKey = `module_${moduleIndex}_sub_${subIndex}`;
          return subKey === itemKey ? checked : newSelection[subKey];
        });
        
        if (!hasSelectedSubmodules) {
          newSelection[moduleKey] = false;
          // Also uncheck resources if no submodules are selected
          const resourceKey = `module_${moduleIndex}_resources`;
          newSelection[resourceKey] = false;
        }
      }
    } else if (itemKey.includes('resources')) {
      // Resource selection
      newSelection[itemKey] = checked;
      
      if (checked) {
        // If resources are selected, module should be selected
        const moduleIndex = parseInt(itemKey.split('_')[1]);
        const moduleKey = `module_${moduleIndex}`;
        newSelection[moduleKey] = true;
      }
    }

    onSelectionChange(newSelection);
  }, [selectedItems, onSelectionChange, modules]);

  // Get checkbox state (checked/unchecked/indeterminate)
  const getCheckboxState = (moduleIndex) => {
    const moduleKey = `module_${moduleIndex}`;
    const module = modules[moduleIndex];
    const isModuleSelected = selectedItems[moduleKey];

    if (!module.submodules || module.submodules.length === 0) {
      return { checked: isModuleSelected || false, indeterminate: false };
    }

    const selectedSubmodules = module.submodules.filter((_, subIndex) =>
      selectedItems[`module_${moduleIndex}_sub_${subIndex}`]
    ).length;

    const totalSubmodules = module.submodules.length;

    if (selectedSubmodules === 0) {
      return { checked: false, indeterminate: false };
    } else if (selectedSubmodules === totalSubmodules) {
      return { checked: true, indeterminate: false };
    } else {
      return { checked: false, indeterminate: true };
    }
  };

  return (
    <Box>
      {modules.map((module, moduleIndex) => {
        const moduleKey = `module_${moduleIndex}`;
        const isExpanded = expandedModules[moduleIndex];
        const checkboxState = getCheckboxState(moduleIndex);
        const submoduleCount = module.submodules?.length || 0;
        const resourceCount = module.resources?.length || 0;

        return (
          <Paper 
            key={moduleIndex} 
            variant="outlined" 
            sx={{ mb: 2, borderRadius: 2 }}
          >
            {/* Module Header */}
            <Box sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={checkboxState.checked}
                      indeterminate={checkboxState.indeterminate}
                      onChange={(e) => handleSelectionChange(moduleKey, e.target.checked)}
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <FolderIcon color="primary" />
                      <Typography variant="subtitle1" fontWeight="medium">
                        {`${t.module} ${moduleIndex + 1}: ${module.title || 'Untitled'}`}
                      </Typography>
                    </Box>
                  }
                  sx={{ flexGrow: 1, mr: 0 }}
                />
                
                <Stack direction="row" spacing={0.5} alignItems="center">
                  {submoduleCount > 0 && (
                    <Chip 
                      label={`${submoduleCount} ${t.submodules}`}
                      size="small"
                      variant="outlined"
                    />
                  )}
                  {resourceCount > 0 && includeResources && (
                    <Chip 
                      label={`${resourceCount} ${t.resources}`}
                      size="small"
                      variant="outlined"
                      icon={<LinkIcon />}
                    />
                  )}
                  
                  {submoduleCount > 0 && (
                    <IconButton
                      size="small"
                      onClick={() => handleModuleToggle(moduleIndex)}
                    >
                      {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    </IconButton>
                  )}
                </Stack>
              </Box>

              {/* Module Description */}
              {module.description && (
                <Typography 
                  variant="body2" 
                  color="text.secondary" 
                  sx={{ mt: 1, ml: 5 }}
                >
                  {module.description.length > 150 
                    ? `${module.description.substring(0, 150)}...` 
                    : module.description
                  }
                </Typography>
              )}
            </Box>

            {/* Module Resources */}
            {includeResources && resourceCount > 0 && (
              <>
                <Divider />
                <Box sx={{ px: 2, py: 1.5 }}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={selectedItems[`${moduleKey}_resources`] || false}
                        onChange={(e) => handleSelectionChange(`${moduleKey}_resources`, e.target.checked)}
                        size="small"
                      />
                    }
                    label={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <LinkIcon fontSize="small" color="action" />
                        <Typography variant="body2" color="text.secondary">
                          {`${t.resources} (${resourceCount})`}
                        </Typography>
                      </Box>
                    }
                  />
                </Box>
              </>
            )}

            {/* Submodules */}
            {submoduleCount > 0 && (
              <Collapse in={isExpanded}>
                <Divider />
                <Box sx={{ bgcolor: 'action.hover' }}>
                  {module.submodules.map((submodule, submoduleIndex) => {
                    const submoduleKey = `${moduleKey}_sub_${submoduleIndex}`;
                    
                    return (
                      <Box 
                        key={submoduleIndex}
                        sx={{ 
                          px: 2, 
                          py: 1.5,
                          borderBottom: submoduleIndex < submoduleCount - 1 ? `1px solid ${theme => theme.palette.divider}` : 'none'
                        }}
                      >
                        <FormControlLabel
                          control={
                            <Checkbox
                              checked={selectedItems[submoduleKey] || false}
                              onChange={(e) => handleSelectionChange(submoduleKey, e.target.checked)}
                              size="small"
                            />
                          }
                          label={
                            <Box>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <ArticleIcon fontSize="small" color="action" />
                                <Typography variant="body2" fontWeight="medium">
                                  {`${moduleIndex + 1}.${submoduleIndex + 1} ${submodule.title || 'Untitled Submodule'}`}
                                </Typography>
                              </Box>
                              {submodule.description && (
                                <Typography 
                                  variant="caption" 
                                  color="text.secondary" 
                                  sx={{ display: 'block', mt: 0.5, ml: 3 }}
                                >
                                  {submodule.description.length > 100 
                                    ? `${submodule.description.substring(0, 100)}...` 
                                    : submodule.description
                                  }
                                </Typography>
                              )}
                            </Box>
                          }
                          sx={{ alignItems: 'flex-start' }}
                        />
                      </Box>
                    );
                  })}
                </Box>
              </Collapse>
            )}

            {/* No Content Message */}
            {submoduleCount === 0 && resourceCount === 0 && (
              <>
                <Divider />
                <Box sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    {t.noSubmodules}
                    {!includeResources ? '' : ` • ${t.noResources}`}
                  </Typography>
                </Box>
              </>
            )}
          </Paper>
        );
      })}

      {modules.length === 0 && (
        <Paper variant="outlined" sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            No hay módulos disponibles para exportar
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

ModuleSelectionTree.propTypes = {
  modules: PropTypes.array.isRequired,
  selectedItems: PropTypes.object.isRequired,
  onSelectionChange: PropTypes.func.isRequired,
  includeResources: PropTypes.bool,
  language: PropTypes.string
};

export default ModuleSelectionTree;