import routesData from './routesData'; // Use default import for CJS export

// Import components
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
import LearningPathView from './components/learning-path/view/LearningPathView';
import TermsPage from './pages/TermsPage';
import PrivacyPolicyPage from './pages/PrivacyPolicyPage';
import PurchaseResultPage from './pages/PurchaseResultPage';

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
  '/history/:entryId': LearningPathView,
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