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
import PurchaseSuccessPage from './components/payments/PurchaseSuccessPage';
import PurchaseCancelPage from './components/payments/PurchaseCancelPage';

/**
 * Centralized route configuration for the application.
 *
 * Properties:
 * - path: The URL path for the route.
 * - component: The React component to render for the route.
 * - requiresAuth: Boolean, true if the route requires authentication.
 * - adminOnly: Boolean, true if the route requires admin privileges (implies requiresAuth).
 * - isPublic: Boolean, true if the route should be included in the sitemap.xml.
 *             Generally, only static, publicly accessible pages should be true.
 * - source (for LearningPathView): Specifies context for the component.
 */
const routesConfig = [
  {
    path: '/',
    component: HomePage,
    requiresAuth: false,
    isPublic: true,
  },
  {
    path: '/generator',
    component: GeneratorPage,
    requiresAuth: true,
    isPublic: false,
  },
  {
    path: '/history',
    component: HistoryPage,
    requiresAuth: true,
    isPublic: false,
  },
  {
    path: '/login',
    component: LoginPage,
    requiresAuth: false,
    isPublic: true,
  },
  {
    path: '/register',
    component: RegisterPage,
    requiresAuth: false,
    isPublic: true,
  },
  {
    path: '/verify-email',
    component: VerifyEmailPage,
    requiresAuth: false,
    isPublic: true, // This page is accessible without login
  },
  {
    path: '/forgot-password',
    component: ForgotPasswordPage,
    requiresAuth: false,
    isPublic: true, // This page is accessible without login
  },
  {
    path: '/reset-password/:token',
    component: ResetPasswordPage,
    requiresAuth: false, // Page itself doesn't require login, token validation handles access
    isPublic: false, // Transient, user-specific, should not be in sitemap
  },
  {
    path: '/admin',
    component: AdminPage,
    requiresAuth: true,
    adminOnly: true,
    isPublic: false,
  },
  {
    path: '/result/:taskId',
    component: ResultPage,
    requiresAuth: true,
    isPublic: false,
  },
  {
    path: '/history/:entryId',
    // Note: We pass the component directly here, App.js will handle props if needed
    component: LearningPathView,
    requiresAuth: true,
    isPublic: false,
    // source: 'history' // Prop passed in App.js based on route match
  },
  {
    path: '/purchase/success',
    component: PurchaseSuccessPage,
    requiresAuth: true,
    isPublic: false,
  },
  {
    path: '/purchase/cancel',
    component: PurchaseCancelPage,
    requiresAuth: true,
    isPublic: false,
  },
  // Add new routes here
];

// It's often useful to export a lookup object for programmatic access if needed elsewhere
export const routeMap = routesConfig.reduce((acc, route) => {
  acc[route.path] = route;
  return acc;
}, {});

export default routesConfig; 