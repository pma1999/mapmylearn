import React, { useState, useEffect, useMemo } from 'react';
import { Routes, Route, Navigate } from 'react-router';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Container, Box } from '@mui/material';
import { Analytics } from "@vercel/analytics/react";

// Import components
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import ProtectedRoute from './components/ProtectedRoute';

// Import auth provider and hook
import { AuthProvider, useAuth } from './services/authContext';

// Import Notification provider
import { NotificationProvider } from './contexts/NotificationContext';

// Import the centralized route configuration
import routesConfig from './routesConfig';

// Import new components
import WelcomeModal from './components/shared/WelcomeModal';

// Import the theme
import theme from './theme/theme';

// --- Import new GeneratingPage ---
import GeneratingPage from './pages/GeneratingPage'; 
// --- End import ---

// New component to render routes and modal
const AppContent = () => {
  const { showWelcomeModal, markWelcomeModalShown } = useAuth();

  return (
    <>
      <Box sx={{ flexGrow: 1 }}>
        <Routes>
          {routesConfig.map((route, index) => {
            const { path, component: Component, requiresAuth, adminOnly } = route;
            
            // Handle the LearningPathView specific props based on route path
            let elementProps = {};
            if (path === '/history/:entryId') {
              elementProps = { source: 'history' };
            } else if (path === '/public/:shareId') { 
              elementProps = { source: 'public' };
            }
            const element = <Component {...elementProps} />;

            if (requiresAuth) {
              return (
                <Route 
                  key={index} 
                  path={path} 
                  element={
                    <ProtectedRoute adminOnly={!!adminOnly}>
                      {element}
                    </ProtectedRoute>
                  } 
                />
              );
            } else {
              return <Route key={index} path={path} element={element} />;
            }
          })}
          {/* Add Route for GeneratingPage */}
          <Route 
            path="/generating/:taskId" 
            element={
              <ProtectedRoute>
                <GeneratingPage />
              </ProtectedRoute>
            }
          />
          {/* Fallback route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Box>
      <WelcomeModal open={showWelcomeModal} onClose={markWelcomeModalShown} />
    </>
  );
}

function App() {
  /*
   * SEO Improvement Note (Step 4):
   * This application uses Client-Side Rendering (CSR).
   * For optimal SEO, especially for the HomePage, configure pre-rendering (e.g., via Vercel settings)
   * or implement Server-Side Rendering (SSR) / Static Site Generation (SSG) for public-facing routes.
   * This ensures search engine crawlers receive fully rendered HTML content.
   * Dynamic metadata (title, description) is handled by react-helmet-async (Step 1).
   */
  return (
    <AuthProvider>
      <Analytics />
      <ThemeProvider theme={theme}>
        <NotificationProvider>
          <CssBaseline />
          <Box sx={{ 
            display: 'flex', 
            flexDirection: 'column', 
            minHeight: '100vh',
          }}>
            <Navbar />
            <AppContent />
            <Footer />
          </Box>
        </NotificationProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App; 