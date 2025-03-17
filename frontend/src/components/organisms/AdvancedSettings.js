import React from 'react';
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Box,
  Slider,
  Grid,
  FormControlLabel,
  Checkbox,
  Stack,
  Tooltip
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import TuneIcon from '@mui/icons-material/Tune';
import InfoIcon from '@mui/icons-material/Info';

const AdvancedSettings = ({
  advancedSettingsOpen,
  setAdvancedSettingsOpen,
  parallelCount,
  setParallelCount,
  searchParallelCount,
  setSearchParallelCount,
  submoduleParallelCount,
  setSubmoduleParallelCount,
  autoModuleCount,
  setAutoModuleCount,
  desiredModuleCount,
  setDesiredModuleCount,
  autoSubmoduleCount,
  setAutoSubmoduleCount,
  desiredSubmoduleCount,
  setDesiredSubmoduleCount,
  isGenerating,
  isMobile
}) => {
  return (
    <Accordion 
      expanded={advancedSettingsOpen} 
      onChange={() => setAdvancedSettingsOpen(!advancedSettingsOpen)}
      disabled={isGenerating}
      sx={{ mb: 2 }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls="advanced-settings-content"
        id="advanced-settings-header"
      >
        <Stack direction="row" spacing={1} alignItems="center">
          <TuneIcon color="primary" />
          <Typography variant="h6" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}>Advanced Settings</Typography>
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        <Typography variant="body2" color="text.secondary" paragraph sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
          These settings control the behavior of the learning path generator. You can adjust them to customize your learning path.
        </Typography>
        
        <Grid container spacing={isMobile ? 2 : 3} sx={{ mb: 2 }}>
          <Grid item xs={12}>
            <Box sx={{ mb: 3 }}>
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                <Typography variant="subtitle2" sx={{ fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
                  Module Count
                </Typography>
                <Tooltip title="Controls how many main modules your learning path will have">
                  <InfoIcon fontSize="small" color="action" />
                </Tooltip>
              </Stack>
              
              <FormControlLabel
                control={
                  <Checkbox
                    checked={autoModuleCount}
                    onChange={(e) => setAutoModuleCount(e.target.checked)}
                    disabled={isGenerating}
                    size={isMobile ? "small" : "medium"}
                  />
                }
                label={
                  <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                    Auto-determine module count (recommended)
                  </Typography>
                }
              />
              
              {!autoModuleCount && (
                <Box sx={{ pl: 3, pr: 1 }}>
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs>
                      <Slider
                        value={desiredModuleCount}
                        onChange={(e, newValue) => setDesiredModuleCount(newValue)}
                        step={1}
                        marks
                        min={3}
                        max={10}
                        disabled={isGenerating || autoModuleCount}
                        size={isMobile ? "small" : "medium"}
                      />
                    </Grid>
                    <Grid item>
                      <Typography sx={{ fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
                        {desiredModuleCount}
                      </Typography>
                    </Grid>
                  </Grid>
                </Box>
              )}
            </Box>
          </Grid>
          
          <Grid item xs={12}>
            <Box sx={{ mb: 3 }}>
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                <Typography variant="subtitle2" sx={{ fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
                  Submodule Count
                </Typography>
                <Tooltip title="Controls how many submodules each main module will contain on average">
                  <InfoIcon fontSize="small" color="action" />
                </Tooltip>
              </Stack>
              
              <FormControlLabel
                control={
                  <Checkbox
                    checked={autoSubmoduleCount}
                    onChange={(e) => setAutoSubmoduleCount(e.target.checked)}
                    disabled={isGenerating}
                    size={isMobile ? "small" : "medium"}
                  />
                }
                label={
                  <Typography variant="body2" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                    Auto-determine submodule count (recommended)
                  </Typography>
                }
              />
              
              {!autoSubmoduleCount && (
                <Box sx={{ pl: 3, pr: 1 }}>
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs>
                      <Slider
                        value={desiredSubmoduleCount}
                        onChange={(e, newValue) => setDesiredSubmoduleCount(newValue)}
                        step={1}
                        marks
                        min={2}
                        max={8}
                        disabled={isGenerating || autoSubmoduleCount}
                        size={isMobile ? "small" : "medium"}
                      />
                    </Grid>
                    <Grid item>
                      <Typography sx={{ fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
                        {desiredSubmoduleCount}
                      </Typography>
                    </Grid>
                  </Grid>
                </Box>
              )}
            </Box>
          </Grid>
          
          <Grid item xs={12}>
            <Box sx={{ mb: 3 }}>
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                <Typography variant="subtitle2" sx={{ fontSize: { xs: '0.8rem', sm: '0.9rem' } }}>
                  Parallel Processing
                </Typography>
                <Tooltip title="Controls how many operations can run in parallel. Higher values may be faster but may increase costs">
                  <InfoIcon fontSize="small" color="action" />
                </Tooltip>
              </Stack>
              
              <Grid container spacing={isMobile ? 2 : 3}>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" sx={{ mb: 1, fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                    Module Generation: {parallelCount}
                  </Typography>
                  <Slider
                    value={parallelCount}
                    onChange={(e, newValue) => setParallelCount(newValue)}
                    step={1}
                    marks
                    min={1}
                    max={5}
                    disabled={isGenerating}
                    size={isMobile ? "small" : "medium"}
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" sx={{ mb: 1, fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                    Search Parallelism: {searchParallelCount}
                  </Typography>
                  <Slider
                    value={searchParallelCount}
                    onChange={(e, newValue) => setSearchParallelCount(newValue)}
                    step={1}
                    marks
                    min={1}
                    max={5}
                    disabled={isGenerating}
                    size={isMobile ? "small" : "medium"}
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" sx={{ mb: 1, fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                    Submodule Parallelism: {submoduleParallelCount}
                  </Typography>
                  <Slider
                    value={submoduleParallelCount}
                    onChange={(e, newValue) => setSubmoduleParallelCount(newValue)}
                    step={1}
                    marks
                    min={1}
                    max={5}
                    disabled={isGenerating}
                    size={isMobile ? "small" : "medium"}
                  />
                </Grid>
              </Grid>
            </Box>
          </Grid>
        </Grid>
        
        <Typography variant="body2" color="warning.main" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
          Note: Higher parallelism values will make generation faster but may increase API usage costs.
        </Typography>
      </AccordionDetails>
    </Accordion>
  );
};

export default AdvancedSettings; 