import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  Box,
  TextField,
  Button,
  Paper,
  Container,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Slider,
  Grid,
  Alert,
  CircularProgress,
  Stack
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import BoltIcon from '@mui/icons-material/Bolt';
import AutorenewIcon from '@mui/icons-material/Autorenew';

// Import API service
import { generateLearningPath } from '../services/api';

function GeneratorPage() {
  const navigate = useNavigate();
  const [topic, setTopic] = useState('');
  const [parallelCount, setParallelCount] = useState(2);
  const [searchParallelCount, setSearchParallelCount] = useState(3);
  const [submoduleParallelCount, setSubmoduleParallelCount] = useState(2);
  const [advancedSettingsOpen, setAdvancedSettingsOpen] = useState(false);
  const [error, setError] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!topic.trim()) {
      setError('Please enter a topic');
      return;
    }
    
    setError('');
    setIsGenerating(true);
    
    try {
      const response = await generateLearningPath(topic, {
        parallelCount,
        searchParallelCount,
        submoduleParallelCount
      });
      
      // Navigate to result page
      navigate(`/result/${response.task_id}`);
    } catch (err) {
      console.error('Error generating learning path:', err);
      setError('Failed to generate learning path. Please try again.');
      setIsGenerating(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
          <Typography
            variant="h4"
            component="h1"
            gutterBottom
            sx={{ fontWeight: 'bold', textAlign: 'center', mb: 3 }}
          >
            Generate Learning Path
          </Typography>
          
          <Typography variant="body1" sx={{ mb: 4, textAlign: 'center' }}>
            Enter any topic you want to learn about and we'll create a personalized learning path for you.
          </Typography>
          
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}
          
          <TextField
            label="What do you want to learn about?"
            variant="outlined"
            fullWidth
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Enter a topic (e.g., Machine Learning, Spanish Cooking, Digital Marketing)"
            sx={{ mb: 3 }}
            inputProps={{ maxLength: 100 }}
            required
            disabled={isGenerating}
            autoFocus
          />
          
          <Divider sx={{ my: 3 }} />
          
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
              </Grid>
            </AccordionDetails>
          </Accordion>
          
          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              size="large"
              disabled={isGenerating || !topic.trim()}
              startIcon={isGenerating ? <CircularProgress size={20} color="inherit" /> : <BoltIcon />}
              sx={{ py: 1.5, px: 4, borderRadius: 2, fontWeight: 'bold', fontSize: '1.1rem' }}
            >
              {isGenerating ? 'Generating...' : 'Generate Learning Path'}
            </Button>
          </Box>
          
          {isGenerating && (
            <Box sx={{ mt: 4, textAlign: 'center' }}>
              <Stack direction="row" spacing={2} alignItems="center" justifyContent="center">
                <AutorenewIcon sx={{ animation: 'spin 2s linear infinite' }} />
                <Typography>
                  Researching your topic and creating your personalized learning path...
                </Typography>
              </Stack>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                This may take a few minutes depending on the complexity of the topic.
              </Typography>
            </Box>
          )}
        </Box>
      </Paper>
      
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Our AI will research your topic and create a comprehensive learning path
          with modules and submodules to help you master the subject efficiently.
        </Typography>
      </Box>
    </Container>
  );
}

export default GeneratorPage; 