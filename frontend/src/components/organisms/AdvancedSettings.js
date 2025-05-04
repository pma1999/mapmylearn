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
  Tooltip,
  Collapse
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import TuneIcon from '@mui/icons-material/Tune';
import InfoIcon from '@mui/icons-material/Info';
import SettingsEthernetIcon from '@mui/icons-material/SettingsEthernet';
import AccountTreeIcon from '@mui/icons-material/AccountTree';

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
      <AccordionDetails sx={{ pt: 2 }}>
        <Typography variant="body2" color="text.secondary" paragraph sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' }, mb: 3 }}>
          Fine-tune the generation process. Hover over <InfoIcon fontSize="inherit" sx={{ verticalAlign: 'middle' }}/> icons for details.
        </Typography>
        
        <Grid container spacing={isMobile ? 3 : 4}>
          <Grid item xs={12}>
            <Stack spacing={2}>
              <Stack direction="row" spacing={1} alignItems="center">
                <AccountTreeIcon color="action" />
                <Typography variant="subtitle1" sx={{ fontWeight: 'medium' }}>
                  Path Structure
                </Typography>
              </Stack>

              <Box sx={{ pl: 2 }}>
                <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
                  <Typography variant="body1">
                    Module Count
                  </Typography>
                  <Tooltip title="Controls how many main modules your course will have.">
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
                <Collapse in={!autoModuleCount}>
                  <Box sx={{ pl: 4, pr: 1, mt: 1 }}>
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
                        <Typography variant="body2" sx={{ minWidth: '2ch', textAlign: 'right' }}>
                          {desiredModuleCount}
                        </Typography>
                      </Grid>
                    </Grid>
                  </Box>
                </Collapse>
              </Box>

              <Box sx={{ pl: 2 }}>
                <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
                  <Typography variant="body1">
                    Submodule Count
                  </Typography>
                  <Tooltip title="Controls how many submodules each main module will contain on average.">
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
                <Collapse in={!autoSubmoduleCount}>
                  <Box sx={{ pl: 4, pr: 1, mt: 1 }}>
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
                        <Typography variant="body2" sx={{ minWidth: '2ch', textAlign: 'right' }}>
                          {desiredSubmoduleCount}
                        </Typography>
                      </Grid>
                    </Grid>
                  </Box>
                </Collapse>
              </Box>
            </Stack>
          </Grid>
          
          <Grid item xs={12}>
            <Stack spacing={2}>
              <Stack direction="row" spacing={1} alignItems="center">
                <SettingsEthernetIcon color="action" />
                <Typography variant="subtitle1" sx={{ fontWeight: 'medium' }}>
                  Parallel Processing
                </Typography>
                <Tooltip title="Controls how many operations run simultaneously. Higher values may speed up generation but increase resource usage.">
                  <InfoIcon fontSize="small" color="action" />
                </Tooltip>
              </Stack>
              
              <Grid container spacing={isMobile ? 2 : 3} sx={{ pl: 2 }}>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" gutterBottom sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
                    Module Planning
                  </Typography>
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs>
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
                    <Grid item>
                      <Typography variant="body2" sx={{ minWidth: '2ch', textAlign: 'right' }}>
                        {parallelCount}
                      </Typography>
                    </Grid>
                  </Grid>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" gutterBottom sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
                    Web Search
                  </Typography>
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs>
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
                    <Grid item>
                      <Typography variant="body2" sx={{ minWidth: '2ch', textAlign: 'right' }}>
                        {searchParallelCount}
                      </Typography>
                    </Grid>
                  </Grid>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" gutterBottom sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
                    Submodule Generation
                  </Typography>
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs>
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
                    <Grid item>
                      <Typography variant="body2" sx={{ minWidth: '2ch', textAlign: 'right' }}>
                        {submoduleParallelCount}
                      </Typography>
                    </Grid>
                  </Grid>
                </Grid>
              </Grid>
            </Stack>
          </Grid>
        </Grid>
        
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 3 }}>
          Note: Adjusting parallelism affects generation speed and resource consumption.
        </Typography>
      </AccordionDetails>
    </Accordion>
  );
};

export default AdvancedSettings; 