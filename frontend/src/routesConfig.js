import routesData from './routesData'; // Use default import for CJS export
import React, { lazy } from 'react';

// Route components are lazy-loaded to reduce initial bundle size
const HomePage = lazy(() => import('./pages/HomePage'));
const GeneratorPage = lazy(() => import('./pages/GeneratorPage'));
const ResultPage = lazy(() => import('./pages/ResultPage'));
const HistoryPage = lazy(() => import('./pages/HistoryPage'));
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const AdminPage = lazy(() => import('./pages/AdminPage'));
const VerifyEmailPage = lazy(() => import('./pages/VerifyEmailPage'));
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage'));
const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage'));
const LearningPathView = lazy(() => import('./components/learning-path/view/LearningPathView'));
const TermsPage = lazy(() => import('./pages/TermsPage'));
const PrivacyPolicyPage = lazy(() => import('./pages/PrivacyPolicyPage'));
const PurchaseResultPage = lazy(() => import('./pages/PurchaseResultPage'));
const OfflinePage = lazy(() => import('./pages/OfflinePage'));
const OfflinePathPage = lazy(() => import('./pages/OfflinePathPage'));
const GeneratingPage = lazy(() => import('./pages/GeneratingPage'));

/**
 * Centralized route configuration for the application.
 * Imports route data (paths, flags) from routesData.js
 * and maps React components to them.
 * This is used by the main App component.
 */

// Create a mapping from path to component for easy lookup
const componentMap = {
  '/': HomePage,
  '/generator': GeneratorPage,
  '/history': HistoryPage,
  '/login': LoginPage,
  '/register': RegisterPage,
  '/verify-email': VerifyEmailPage,
  '/forgot-password': ForgotPasswordPage,
  '/reset-password/:token': ResetPasswordPage,
  '/admin': AdminPage,
  '/result/:taskId': ResultPage,
  '/generating/:taskId': GeneratingPage,
  '/history/:entryId': LearningPathView,
  '/offline': OfflinePage,
  '/offline/:offlineId': OfflinePathPage,
  '/terms': TermsPage,
  '/privacy': PrivacyPolicyPage,
  '/public/:shareId': LearningPathView,
  '/purchase-result': PurchaseResultPage,
};

const routesConfig = routesData.map(routeData => ({
  ...routeData,
  component: componentMap[routeData.path] || null, // Add the component from the map
}));

// Check for routes defined in data but missing a component mapping
routesConfig.forEach(route => {
  if (!route.component) {
    console.warn(`Warning: No component found in componentMap for path: ${route.path}. Ensure it's added to routesConfig.js.`);
  }
});

// Original code for routeMap export, ensure it works with the new structure
export const routeMap = routesConfig.reduce((acc, route) => {
  acc[route.path] = route;
  return acc;
}, {});


export default routesConfig; 