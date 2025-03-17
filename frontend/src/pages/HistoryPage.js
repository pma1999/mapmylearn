import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Typography,
  Box,
  Container,
  Paper,
  Button,
  Card,
  CardContent,
  Grid,
  Divider,
  Alert
} from '@mui/material';
import HistoryIcon from '@mui/icons-material/History';
import AddIcon from '@mui/icons-material/Add';

function HistoryPage() {
  return (
    <Container maxWidth="lg">
      <Paper elevation={3} sx={{ p: 4, borderRadius: 2, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <HistoryIcon sx={{ mr: 1, fontSize: 32, color: 'primary.main' }} />
            <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold' }}>
              Learning Path History
            </Typography>
          </Box>
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            component={RouterLink}
            to="/generator"
          >
            Create New Path
          </Button>
        </Box>
        
        <Divider sx={{ mb: 4 }} />
        
        <Box sx={{ mb: 4 }}>
          <Alert severity="info" sx={{ mb: 3 }}>
            This is a placeholder for the history feature. In a full implementation, previously
            generated learning paths would be saved and displayed here for future reference.
          </Alert>
          
          <Typography variant="body1" paragraph>
            The history page would allow you to:
          </Typography>
          
          <ul>
            <li>
              <Typography variant="body1" sx={{ mb: 1 }}>
                View all your previously generated learning paths
              </Typography>
            </li>
            <li>
              <Typography variant="body1" sx={{ mb: 1 }}>
                Search and filter by topic, date created, or favorites
              </Typography>
            </li>
            <li>
              <Typography variant="body1" sx={{ mb: 1 }}>
                Export learning paths in various formats
              </Typography>
            </li>
            <li>
              <Typography variant="body1" sx={{ mb: 1 }}>
                Organize learning paths into collections
              </Typography>
            </li>
          </ul>
        </Box>
        
        <Typography variant="h5" sx={{ mb: 3 }}>
          Sample Learning Paths
        </Typography>
        
        <Grid container spacing={3}>
          {['Machine Learning Fundamentals', 'Spanish for Beginners', 'Introduction to Digital Marketing'].map((topic, index) => (
            <Grid item xs={12} md={4} key={index}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    {topic}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    Created: {new Date(Date.now() - Math.random() * 10000000000).toLocaleDateString()}
                  </Typography>
                  <Typography variant="body2">
                    {Math.floor(Math.random() * 5) + 3} modules, {Math.floor(Math.random() * 15) + 5} submodules
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Button
                      variant="text"
                      size="small"
                      component={RouterLink}
                      to="/generator"
                    >
                      View Details
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>
    </Container>
  );
}

export default HistoryPage; 