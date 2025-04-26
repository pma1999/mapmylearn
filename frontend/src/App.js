import React, { useState, useEffect, useMemo } from 'react';
import { Routes, Route, Navigate } from 'react-router';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Container, Box } from '@mui/material';
import { Analytics } from "@vercel/analytics/react";

// Import pages
import HomePage from './pages/HomePage';
import GeneratorPage from './pages/GeneratorPage';
import ResultPage from './pages/ResultPage';
import HistoryPage from './pages/HistoryPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import AdminPage from './pages/AdminPage';
import VerifyEmailPage from './pages/VerifyEmailPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';

// Import components
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import ProtectedRoute from './components/ProtectedRoute';
import LearningPathView from './components/learning-path/view/LearningPathView';

// Import auth provider and hook
import { AuthProvider, useAuth } from './services/authContext';

// Import new components
import PurchaseSuccessPage from './components/payments/PurchaseSuccessPage';
import PurchaseCancelPage from './components/payments/PurchaseCancelPage';
import WelcomeModal from './components/shared/WelcomeModal';

// Create theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#f50057',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: [
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
});

// New component to render routes and modal
const AppContent = () => {
  const { showWelcomeModal, markWelcomeModalShown } = useAuth();

  return (
    <>
      <Box sx={{ flexGrow: 1 }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route 
            path="/generator" 
            element={
              <ProtectedRoute>
                <GeneratorPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/history" 
            element={
              <ProtectedRoute>
                <HistoryPage />
              </ProtectedRoute>
            } 
          />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/verify-email" element={<VerifyEmailPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
          <Route 
            path="/admin" 
            element={
              <ProtectedRoute adminOnly={true}>
                <AdminPage />
              </ProtectedRoute>
            } 
          />
          <Route path="/result/:taskId" element={
            <ProtectedRoute>
              <ResultPage />
            </ProtectedRoute>
          } />
          <Route path="/history/:entryId" element={
            <ProtectedRoute>
              <LearningPathView source="history" />
            </ProtectedRoute>
          } />
          <Route 
            path="/purchase/success" 
            element={
              <ProtectedRoute>
                <PurchaseSuccessPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/purchase/cancel" 
            element={
              <ProtectedRoute>
                <PurchaseCancelPage />
              </ProtectedRoute>
            } 
          />
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
        <CssBaseline />
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          minHeight: '100vh',
          backgroundColor: 'background.default'
        }}>
          <Navbar />
          <AppContent />
          <Footer />
        </Box>
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App; 