import React, { useState, useEffect, useMemo } from 'react';
import PropTypes from 'prop-types';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Chip,
  LinearProgress,
  FormControlLabel,
  Switch,
  Divider,
  Paper,
  Stack,
  Alert,
  IconButton,
  Tooltip
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import ArticleIcon from '@mui/icons-material/Article';
import SelectAllIcon from '@mui/icons-material/SelectAll';
import DeselectIcon from '@mui/icons-material/Deselect';
import FileDownloadIcon from '@mui/icons-material/FileDownload';

// Import the hierarchical tree selection component
import ModuleSelectionTree from './ModuleSelectionTree';

/**
 * Dialog component for selective Markdown export
 * Allows users to choose which modules, submodules, and resources to export
 */
const SelectiveExportDialog = ({
  open,
  onClose,
  onExport,
  pathData,
  topic,
  language = 'es'
}) => {
  const [selectedItems, setSelectedItems] = useState({});
  const [includeResources, setIncludeResources] = useState(true);
  const [includeTableOfContents, setIncludeTableOfContents] = useState(true);
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);

  // Extract modules from pathData
  const modules = useMemo(() => {
    if (!pathData) return [];
    return pathData.modules || [];
  }, [pathData]);

  // Initialize selection state when dialog opens
  useEffect(() => {
    if (open && modules.length > 0) {
      // Initially select all items
      const initialSelection = {};
      modules.forEach((module, moduleIndex) => {
        initialSelection[`module_${moduleIndex}`] = true;
        if (module.submodules) {
          module.submodules.forEach((_, submoduleIndex) => {
            initialSelection[`module_${moduleIndex}_sub_${submoduleIndex}`] = true;
          });
        }
        // Include module resources
        if (module.resources && module.resources.length > 0) {
          initialSelection[`module_${moduleIndex}_resources`] = true;
        }
      });
      setSelectedItems(initialSelection);
    }
  }, [open, modules]);

  // Calculate selection statistics
  const selectionStats = useMemo(() => {
    let selectedModules = 0;
    let selectedSubmodules = 0;
    let selectedResources = 0;
    let totalModules = modules.length;
    let totalSubmodules = 0;
    let totalResources = 0;

    modules.forEach((module, moduleIndex) => {
      if (selectedItems[`module_${moduleIndex}`]) {
        selectedModules++;
      }
      
      if (module.submodules) {
        totalSubmodules += module.submodules.length;
        module.submodules.forEach((_, submoduleIndex) => {
          if (selectedItems[`module_${moduleIndex}_sub_${submoduleIndex}`]) {
            selectedSubmodules++;
          }
        });
      }

      if (module.resources && module.resources.length > 0) {
        totalResources += module.resources.length;
        if (selectedItems[`module_${moduleIndex}_resources`]) {
          selectedResources += module.resources.length;
        }
      }
    });

    return {
      selectedModules,
      selectedSubmodules,
      selectedResources,
      totalModules,
      totalSubmodules,
      totalResources,
      isEmpty: selectedModules === 0 && selectedSubmodules === 0
    };
  }, [selectedItems, modules]);

  // Handle select all
  const handleSelectAll = () => {
    const allSelected = {};
    modules.forEach((module, moduleIndex) => {
      allSelected[`module_${moduleIndex}`] = true;
      if (module.submodules) {
        module.submodules.forEach((_, submoduleIndex) => {
          allSelected[`module_${moduleIndex}_sub_${submoduleIndex}`] = true;
        });
      }
      if (module.resources && module.resources.length > 0) {
        allSelected[`module_${moduleIndex}_resources`] = true;
      }
    });
    setSelectedItems(allSelected);
  };

  // Handle deselect all
  const handleDeselectAll = () => {
    setSelectedItems({});
  };

  // Handle export
  const handleExport = async () => {
    if (selectionStats.isEmpty) return;

    setIsExporting(true);
    setExportProgress(0);

    try {
      // Create filtered data based on selection
      const filteredData = {
        ...pathData,
        modules: modules.map((module, moduleIndex) => {
          if (!selectedItems[`module_${moduleIndex}`]) {
            return null; // Module not selected
          }

          const filteredModule = { ...module };

          // Filter submodules
          if (module.submodules) {
            filteredModule.submodules = module.submodules.filter((_, submoduleIndex) => 
              selectedItems[`module_${moduleIndex}_sub_${submoduleIndex}`]
            );
          }

          // Filter resources
          if (!includeResources || !selectedItems[`module_${moduleIndex}_resources`]) {
            filteredModule.resources = [];
          }

          return filteredModule;
        }).filter(Boolean) // Remove null modules
      };

      // Simulate progress steps
      const progressSteps = [20, 40, 60, 80, 100];
      for (let i = 0; i < progressSteps.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 200));
        setExportProgress(progressSteps[i]);
      }

      // Call the export function with filtered data and options
      await onExport(filteredData, {
        includeResources,
        includeTableOfContents,
        includeMetadata,
        selectedItems,
        selectionStats
      });

      // Close dialog after successful export
      onClose();
    } catch (error) {
      console.error('Export error:', error);
    } finally {
      setIsExporting(false);
      setExportProgress(0);
    }
  };

  // Handle item selection change
  const handleSelectionChange = (newSelection) => {
    setSelectedItems(newSelection);
  };

  const texts = {
    es: {
      title: 'Exportar Contenido Seleccionado',
      subtitle: 'Elige qué módulos y contenido incluir en tu exportación',
      selectAll: 'Seleccionar Todo',
      deselectAll: 'Deseleccionar Todo',
      includeResources: 'Incluir recursos',
      includeTableOfContents: 'Incluir índice',
      includeMetadata: 'Incluir metadatos',
      selectedCount: 'Seleccionado',
      modules: 'módulos',
      submodules: 'submódulos', 
      resources: 'recursos',
      exportButton: 'Exportar Markdown',
      exporting: 'Exportando...',
      cancel: 'Cancelar',
      noSelection: 'Selecciona al menos un elemento para exportar',
      exportOptions: 'Opciones de Exportación'
    },
    en: {
      title: 'Export Selected Content',
      subtitle: 'Choose which modules and content to include in your export',
      selectAll: 'Select All',
      deselectAll: 'Deselect All',
      includeResources: 'Include resources',
      includeTableOfContents: 'Include table of contents',
      includeMetadata: 'Include metadata',
      selectedCount: 'Selected',
      modules: 'modules',
      submodules: 'submodules',
      resources: 'resources',
      exportButton: 'Export Markdown',
      exporting: 'Exporting...',
      cancel: 'Cancel',
      noSelection: 'Select at least one item to export',
      exportOptions: 'Export Options'
    }
  };

  const t = texts[language] || texts.en;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          maxHeight: '90vh',
          borderRadius: 2
        }
      }}
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ArticleIcon color="primary" />
            <Box>
              <Typography variant="h6" component="div">
                {t.title}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t.subtitle}
              </Typography>
            </Box>
          </Box>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ p: 0 }}>
        {/* Selection Summary */}
        <Box sx={{ px: 3, py: 2, bgcolor: 'background.default' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              {t.selectedCount}:
            </Typography>
            <Stack direction="row" spacing={1}>
              <Tooltip title={t.selectAll}>
                <IconButton size="small" onClick={handleSelectAll}>
                  <SelectAllIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title={t.deselectAll}>
                <IconButton size="small" onClick={handleDeselectAll}>
                  <DeselectIcon />
                </IconButton>
              </Tooltip>
            </Stack>
          </Box>
          
          <Stack direction="row" spacing={1} flexWrap="wrap">
            <Chip 
              label={`${selectionStats.selectedModules}/${selectionStats.totalModules} ${t.modules}`}
              size="small"
              variant={selectionStats.selectedModules > 0 ? "filled" : "outlined"}
              color={selectionStats.selectedModules > 0 ? "primary" : "default"}
            />
            <Chip 
              label={`${selectionStats.selectedSubmodules}/${selectionStats.totalSubmodules} ${t.submodules}`}
              size="small"
              variant={selectionStats.selectedSubmodules > 0 ? "filled" : "outlined"}
              color={selectionStats.selectedSubmodules > 0 ? "primary" : "default"}
            />
            {selectionStats.totalResources > 0 && (
              <Chip 
                label={`${selectionStats.selectedResources}/${selectionStats.totalResources} ${t.resources}`}
                size="small"
                variant={selectionStats.selectedResources > 0 ? "filled" : "outlined"}
                color={selectionStats.selectedResources > 0 ? "primary" : "default"}
              />
            )}
          </Stack>
        </Box>

        <Divider />

        {/* Module Selection Tree */}
        <Box sx={{ px: 3, py: 2, maxHeight: '40vh', overflow: 'auto' }}>
          <ModuleSelectionTree
            modules={modules}
            selectedItems={selectedItems}
            onSelectionChange={handleSelectionChange}
            includeResources={includeResources}
            language={language}
          />
        </Box>

        <Divider />

        {/* Export Options */}
        <Box sx={{ px: 3, py: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 2 }}>
            {t.exportOptions}
          </Typography>
          
          <Stack spacing={1}>
            <FormControlLabel
              control={
                <Switch
                  checked={includeResources}
                  onChange={(e) => setIncludeResources(e.target.checked)}
                  size="small"
                />
              }
              label={t.includeResources}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={includeTableOfContents}
                  onChange={(e) => setIncludeTableOfContents(e.target.checked)}
                  size="small"
                />
              }
              label={t.includeTableOfContents}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={includeMetadata}
                  onChange={(e) => setIncludeMetadata(e.target.checked)}
                  size="small"
                />
              }
              label={t.includeMetadata}
            />
          </Stack>
        </Box>

        {/* Export Progress */}
        {isExporting && (
          <Box sx={{ px: 3, py: 2 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>
              {t.exporting}
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={exportProgress} 
              sx={{ borderRadius: 1 }}
            />
          </Box>
        )}

        {/* No Selection Alert */}
        {selectionStats.isEmpty && (
          <Box sx={{ px: 3, pb: 2 }}>
            <Alert severity="warning" variant="outlined">
              {t.noSelection}
            </Alert>
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose} disabled={isExporting}>
          {t.cancel}
        </Button>
        <Button
          onClick={handleExport}
          variant="contained"
          startIcon={isExporting ? undefined : <FileDownloadIcon />}
          disabled={selectionStats.isEmpty || isExporting}
        >
          {isExporting ? t.exporting : t.exportButton}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

SelectiveExportDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onExport: PropTypes.func.isRequired,
  pathData: PropTypes.object,
  topic: PropTypes.string,
  language: PropTypes.string
};

export default SelectiveExportDialog;