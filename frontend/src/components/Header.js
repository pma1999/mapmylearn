import React, { useState } from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  useMediaQuery,
  useTheme,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Box,
  Tooltip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Home as HomeIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  School as SchoolIcon,
} from '@mui/icons-material';
import { useSettings } from '../contexts/SettingsContext';

const Header = () => {
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { settings } = useSettings();

  const navItems = [
    { text: 'Generador', path: '/', icon: <HomeIcon /> },
    { text: 'Historial', path: '/history', icon: <HistoryIcon /> },
    { text: 'Configuración', path: '/settings', icon: <SettingsIcon /> },
  ];

  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen);
  };

  const activeRoute = (path) => {
    return location.pathname === path;
  };

  const drawer = (
    <Box onClick={handleDrawerToggle} sx={{ textAlign: 'center' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', p: 2 }}>
        <SchoolIcon sx={{ mr: 1 }} />
        <Typography variant="h6" component="div">
          Generador de Rutas
        </Typography>
      </Box>
      <List>
        {navItems.map((item) => (
          <ListItem
            button
            component={RouterLink}
            to={item.path}
            key={item.text}
            selected={activeRoute(item.path)}
            sx={{
              color: activeRoute(item.path) ? 'primary.main' : 'inherit',
              '&.Mui-selected': {
                backgroundColor: 'rgba(63, 81, 181, 0.08)',
              },
            }}
          >
            <ListItemIcon
              sx={{
                color: activeRoute(item.path) ? 'primary.main' : 'inherit',
                minWidth: '40px',
              }}
            >
              {item.icon}
            </ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    </Box>
  );

  const apiKeyWarning = !settings.openaiApiKeySet || !settings.tavilyApiKeySet;

  return (
    <>
      <AppBar position="fixed">
        <Toolbar>
          {isMobile && (
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <SchoolIcon sx={{ mr: 1 }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Generador de Rutas de Aprendizaje
            </Typography>
          </Box>
          <Box sx={{ flexGrow: 1 }} />
          {apiKeyWarning && (
            <Tooltip title="Faltan claves API. Ir a Configuración">
              <Button
                color="inherit"
                component={RouterLink}
                to="/settings"
                startIcon={<SettingsIcon />}
                sx={{ mr: 2, color: '#ffeb3b' }}
              >
                {isMobile ? null : 'Configurar APIs'}
              </Button>
            </Tooltip>
          )}
          {!isMobile && (
            <Box>
              {navItems.map((item) => (
                <Button
                  key={item.text}
                  color="inherit"
                  component={RouterLink}
                  to={item.path}
                  startIcon={item.icon}
                  sx={{
                    ml: 1,
                    borderBottom: activeRoute(item.path)
                      ? '2px solid white'
                      : '2px solid transparent',
                    borderRadius: 0,
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 0.08)',
                    },
                  }}
                >
                  {item.text}
                </Button>
              ))}
            </Box>
          )}
        </Toolbar>
      </AppBar>
      <Drawer
        variant="temporary"
        open={drawerOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile
        }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 240 },
        }}
      >
        {drawer}
      </Drawer>
    </>
  );
};

export default Header; 