import React from 'react';
import {
  Typography,
  Box,
  Grid,
  Alert,
  Slider,
  FormControlLabel,
  Checkbox,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

function AdvancedSettings({
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
  isGenerating
}) {
  return (
    <Accordion
      expanded={advancedSettingsOpen}
      onChange={() => setAdvancedSettingsOpen(!advancedSettingsOpen)}
      sx={{ mb: 3 }}
    >
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="subtitle1" sx={{ fontWeight: 'medium' }}>
          Advanced Settings
        </Typography>
      </AccordionSummary>
      <AccordionDetails>
        <Grid container spacing={4}>
          <Grid item xs={12}>
            <Typography gutterBottom>
              Parallel Module Processing: {parallelCount}
            </Typography>
            <Slider
              value={parallelCount}
              min={1}
              max={4}
              step={1}
              marks
              onChange={(_, value) => setParallelCount(value)}
              valueLabelDisplay="auto"
              disabled={isGenerating}
            />
            <Typography variant="body2" color="text.secondary">
              Higher values may generate learning paths faster but could use more resources.
            </Typography>
          </Grid>
          
          <Grid item xs={12}>
            <Typography gutterBottom>
              Search Parallel Count: {searchParallelCount}
            </Typography>
            <Slider
              value={searchParallelCount}
              min={1}
              max={5}
              step={1}
              marks
              onChange={(_, value) => setSearchParallelCount(value)}
              valueLabelDisplay="auto"
              disabled={isGenerating}
            />
            <Typography variant="body2" color="text.secondary">
              Controls how many searches run in parallel during research phase.
            </Typography>
          </Grid>
          
          <Grid item xs={12}>
            <Typography gutterBottom>
              Submodule Parallel Count: {submoduleParallelCount}
            </Typography>
            <Slider
              value={submoduleParallelCount}
              min={1}
              max={4}
              step={1}
              marks
              onChange={(_, value) => setSubmoduleParallelCount(value)}
              valueLabelDisplay="auto"
              disabled={isGenerating}
            />
            <Typography variant="body2" color="text.secondary">
              Controls how many submodules are processed in parallel.
            </Typography>
          </Grid>
          
          <Grid item xs={12}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" sx={{ fontWeight: 'medium', mb: 2 }}>
              Content Structure Settings
            </Typography>
            <Alert severity="info" sx={{ mb: 3 }}>
              Control exactly how many modules and submodules your learning path should have. 
              By default, the AI will determine the optimal number based on the topic.
              Disable "Automatic" mode to specify exact counts.
            </Alert>
          </Grid>
          
          <Grid item xs={12}>
            <Box sx={{ mb: 2 }}>
              <FormControlLabel
                control={
                  <Checkbox 
                    checked={autoModuleCount} 
                    onChange={(e) => setAutoModuleCount(e.target.checked)}
                    disabled={isGenerating}
                  />
                }
                label="Automatic module count (let AI decide)"
              />
            </Box>
            
            <Typography gutterBottom>
              Desired Number of Modules: {desiredModuleCount}
            </Typography>
            <Slider
              value={desiredModuleCount}
              min={1}
              max={10}
              step={1}
              marks
              onChange={(_, value) => setDesiredModuleCount(value)}
              valueLabelDisplay="auto"
              disabled={isGenerating || autoModuleCount}
              sx={{
                opacity: autoModuleCount ? 0.5 : 1,
                '& .MuiSlider-markLabel': {
                  fontSize: '0.75rem'
                }
              }}
            />
            <Typography variant="body2" color="text.secondary" sx={{ opacity: autoModuleCount ? 0.5 : 1 }}>
              Specify exactly how many modules should be in your learning path.
            </Typography>
          </Grid>
          
          <Grid item xs={12}>
            <Box sx={{ mt: 3, mb: 2 }}>
              <FormControlLabel
                control={
                  <Checkbox 
                    checked={autoSubmoduleCount} 
                    onChange={(e) => setAutoSubmoduleCount(e.target.checked)}
                    disabled={isGenerating}
                  />
                }
                label="Automatic submodule count (let AI decide)"
              />
            </Box>
            
            <Typography gutterBottom>
              Desired Number of Submodules per Module: {desiredSubmoduleCount}
            </Typography>
            <Slider
              value={desiredSubmoduleCount}
              min={1}
              max={5}
              step={1}
              marks
              onChange={(_, value) => setDesiredSubmoduleCount(value)}
              valueLabelDisplay="auto"
              disabled={isGenerating || autoSubmoduleCount}
              sx={{
                opacity: autoSubmoduleCount ? 0.5 : 1,
                '& .MuiSlider-markLabel': {
                  fontSize: '0.75rem'
                }
              }}
            />
            <Typography variant="body2" color="text.secondary" sx={{ opacity: autoSubmoduleCount ? 0.5 : 1 }}>
              Specify exactly how many submodules each module should have.
            </Typography>
          </Grid>
        </Grid>
      </AccordionDetails>
    </Accordion>
  );
}

export default AdvancedSettings; 