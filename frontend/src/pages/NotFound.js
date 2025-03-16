import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import { Link } from 'react-router-dom';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';

const NotFound = () => {
  return (
    <Box className="content-container" sx={{ textAlign: 'center' }}>
      <Paper
        elevation={3}
        sx={{
          p: 5,
          maxWidth: 600,
          mx: 'auto',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          mt: 4
        }}
      >
        <ErrorOutlineIcon sx={{ fontSize: 80, color: 'error.main', mb: 3 }} />
        
        <Typography variant="h4" component="h1" gutterBottom>
          Página no encontrada
        </Typography>
        
        <Typography variant="body1" color="text.secondary" paragraph>
          Lo sentimos, la página que estás buscando no existe o ha sido eliminada.
        </Typography>
        
        <Box sx={{ mt: 3 }}>
          <Button
            component={Link}
            to="/"
            variant="contained"
            color="primary"
            sx={{ mr: 2 }}
          >
            Ir al Generador
          </Button>
          
          <Button
            component={Link}
            to="/history"
            variant="outlined"
          >
            Ver Historial
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default NotFound; 