import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Typography,
  Button,
  Box,
  Container,
  Paper,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Stack
} from '@mui/material';
import AutoStoriesIcon from '@mui/icons-material/AutoStories';
import VerifiedIcon from '@mui/icons-material/Verified';
import DevicesIcon from '@mui/icons-material/Devices';

function HomePage() {
  return (
    <Box>
      {/* Hero Section */}
      <Paper
        elevation={0}
        sx={{
          position: 'relative',
          backgroundColor: 'primary.main',
          color: '#fff',
          mb: 6,
          borderRadius: 4,
          overflow: 'hidden',
          boxShadow: 3
        }}
      >
        <Container maxWidth="lg" sx={{ py: 8 }}>
          <Grid container spacing={4} alignItems="center">
            <Grid item xs={12} md={6}>
              <Typography
                component="h1"
                variant="h2"
                color="inherit"
                gutterBottom
                sx={{ fontWeight: 700 }}
              >
                Personalized Learning Paths
              </Typography>
              <Typography variant="h5" color="inherit" paragraph sx={{ mb: 4, opacity: 0.9 }}>
                Generate custom learning paths for any topic using AI.
                Learn efficiently with personalized, structured content.
              </Typography>
              <Button
                variant="contained"
                color="secondary"
                size="large"
                component={RouterLink}
                to="/generator"
                sx={{ px: 4, py: 1.5, fontSize: '1.1rem', fontWeight: 'bold' }}
              >
                Create Your Path
              </Button>
            </Grid>
            <Grid item xs={12} md={6} sx={{ display: { xs: 'none', md: 'block' } }}>
              <Box
                component="img"
                src="https://source.unsplash.com/random?book,education"
                alt="Learning"
                sx={{
                  width: '100%',
                  height: 'auto',
                  borderRadius: 2,
                  boxShadow: 4
                }}
              />
            </Grid>
          </Grid>
        </Container>
      </Paper>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ mb: 8 }}>
        <Typography
          component="h2"
          variant="h3"
          align="center"
          color="text.primary"
          gutterBottom
          sx={{ mb: 6 }}
        >
          Key Features
        </Typography>
        <Grid container spacing={4}>
          <Grid item xs={12} md={4}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', boxShadow: 2 }}>
              <CardMedia
                component="div"
                sx={{
                  pt: '56.25%',
                  bgcolor: 'primary.light',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <AutoStoriesIcon
                  sx={{
                    fontSize: 80,
                    color: 'white',
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)'
                  }}
                />
              </CardMedia>
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography gutterBottom variant="h5" component="h3">
                  Personalized Content
                </Typography>
                <Typography>
                  Our AI analyzes your chosen topic and creates a custom learning path tailored to your interests.
                  Every path is unique and designed for optimal knowledge progression.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', boxShadow: 2 }}>
              <CardMedia
                component="div"
                sx={{
                  pt: '56.25%',
                  bgcolor: 'secondary.light',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <VerifiedIcon
                  sx={{
                    fontSize: 80,
                    color: 'white',
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)'
                  }}
                />
              </CardMedia>
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography gutterBottom variant="h5" component="h3">
                  Research-Backed
                </Typography>
                <Typography>
                  Each learning path is created using real-time research from the web, ensuring up-to-date and
                  accurate information on your topic of interest.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', boxShadow: 2 }}>
              <CardMedia
                component="div"
                sx={{
                  pt: '56.25%',
                  bgcolor: 'primary.dark',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <DevicesIcon
                  sx={{
                    fontSize: 80,
                    color: 'white',
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)'
                  }}
                />
              </CardMedia>
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography gutterBottom variant="h5" component="h3">
                  Accessible Learning
                </Typography>
                <Typography>
                  Access your learning paths anytime, from any device. Save your paths for future reference
                  and continue your learning journey at your own pace.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>

      {/* Call to Action */}
      <Container maxWidth="md" sx={{ mb: 8 }}>
        <Paper
          sx={{
            p: 4,
            borderRadius: 4,
            backgroundColor: 'primary.light',
            color: 'white',
            textAlign: 'center',
            boxShadow: 3
          }}
        >
          <Stack spacing={3} alignItems="center">
            <Typography variant="h4" component="h3" sx={{ fontWeight: 'bold' }}>
              Start Your Learning Journey Today
            </Typography>
            <Typography variant="body1" sx={{ maxWidth: '80%', mx: 'auto' }}>
              Generate a customized learning path on any topic in just a few clicks.
              Enhance your knowledge and skills with our AI-powered platform.
            </Typography>
            <Button
              variant="contained"
              color="secondary"
              size="large"
              component={RouterLink}
              to="/generator"
              sx={{ px: 4, py: 1.5 }}
            >
              Create Learning Path
            </Button>
          </Stack>
        </Paper>
      </Container>
    </Box>
  );
}

export default HomePage; 