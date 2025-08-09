import React, { useState, useEffect } from 'react';
import { Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, useMediaQuery, useTheme } from '@mui/material';
import ErrorBoundary from './components/ErrorBoundary';

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
import PwaIntroModal from './components/shared/PwaIntroModal';
import PwaIntroContext from './contexts/PwaIntroContext';

// Import PWA detection utilities
import { detectPWACapabilities, createTutorialTracker } from './utils/pwaDetection';

// Import the theme
import theme from './theme/theme';

// --- Import new GeneratingPage ---
import GeneratingPage from './pages/GeneratingPage'; 
// --- End import ---

// Lazy-load analytics in production only (placed after all imports to satisfy ESLint import/first)
let Analytics = () => null;
let SpeedInsights = () => null;
if (process.env.NODE_ENV === 'production') {
  // Dynamic import without awaiting; components will render when ready
  import('@vercel/analytics/react').then(mod => { Analytics = mod.Analytics; }).catch(() => {});
  import('@vercel/speed-insights/react').then(mod => { SpeedInsights = mod.SpeedInsights; }).catch(() => {});
}

// Enhanced PWA tutorial version management
const TUTORIAL_VERSION = 'v2.0';
const LEGACY_PWA_FLAG_KEY = 'mapmylearn_pwa_intro_shown'; // Old key for cleanup

// New component to render routes and modal
const AppContent = () => {
  const { showWelcomeModal, markWelcomeModalShown } = useAuth();
  const theme = useTheme();
  const isSmallScreen = useMediaQuery(theme.breakpoints.down('sm'));
  const [showPwaIntro, setShowPwaIntro] = useState(false);
  const [pwaCapabilities, setPwaCapabilities] = useState(null);
  const [tutorialTracker] = useState(() => createTutorialTracker(TUTORIAL_VERSION));

  // Detect PWA capabilities universally (regardless of tutorial state)
  useEffect(() => {
    const capabilities = detectPWACapabilities();
    setPwaCapabilities(capabilities);
  }, []);

  // Enhanced PWA tutorial trigger logic
  useEffect(() => {
    const shouldShowTutorial = () => {
      // Only show on mobile/tablet devices
      if (!isSmallScreen) return false;
      
      // Don't show if user has completed the current tutorial version
      if (tutorialTracker.hasCompleted()) return false;
      
      // Clean up legacy flag to force re-display for existing users
      if (localStorage.getItem(LEGACY_PWA_FLAG_KEY)) {
        localStorage.removeItem(LEGACY_PWA_FLAG_KEY);
      }
      
      // Show tutorial for new or returning users with enhanced version
      return true;
    };

    if (shouldShowTutorial()) {
      // Small delay to ensure smooth app initialization
      const timer = setTimeout(() => {
        setShowPwaIntro(true);
      }, 1000);
      
      return () => clearTimeout(timer);
    }
  }, [isSmallScreen, tutorialTracker]);

  const handleClosePwaIntro = () => {
    tutorialTracker.markCompleted();
    setShowPwaIntro(false);
  };

  const openPwaIntro = () => {
    setShowPwaIntro(true);
  };

  // Debug function for development (can be removed in production)
  const resetPwaTutorial = () => {
    tutorialTracker.reset();
    localStorage.removeItem(LEGACY_PWA_FLAG_KEY);
    console.log('PWA tutorial reset - will show on next mobile visit');
  };

  // Expose reset function globally for development/testing
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      window.resetPwaTutorial = resetPwaTutorial;
      console.log('Development mode: Use window.resetPwaTutorial() to reset PWA tutorial');
    }
  }, []);

  return (
    <PwaIntroContext.Provider value={{ 
      openPwaIntro, 
      pwaCapabilities,
      tutorialTracker
    }}>
      <Box sx={{ flexGrow: 1 }}>
        <ErrorBoundary fallback={<Box sx={{ p: 3 }}>Something went wrong. Please reload.</Box>}>
          <Suspense fallback={<Box sx={{ p: 3 }} />}> 
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
          </Suspense>
        </ErrorBoundary>
      </Box>
      <WelcomeModal open={showWelcomeModal} onClose={markWelcomeModalShown} />
      <PwaIntroModal open={showPwaIntro} onClose={handleClosePwaIntro} />
    </PwaIntroContext.Provider>
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
      <SpeedInsights />
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