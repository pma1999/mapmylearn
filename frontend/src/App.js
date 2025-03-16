import React, { useState, useMemo } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Context Providers
import { SettingsProvider, useSettings } from './contexts/SettingsContext';

// Components
import Header from './components/Header';
import NotificationBar from './components/NotificationBar';

// Pages
import Generator from './pages/Generator';
import History from './pages/History';
import HistoryDetail from './pages/HistoryDetail';
import Settings from './pages/Settings';
import NotFound from './pages/NotFound';

// Theme
import getTheme from './theme';

// App Component
const AppContent = () => {
  const { settings } = useSettings();
  const [notification, setNotification] = useState({ message: '', severity: 'info' });

  // Create theme based on dark mode setting
  const theme = useMemo(() => createTheme(getTheme(settings.darkMode)), [settings.darkMode]);

  // Function to show notifications
  const showNotification = (message, severity = 'info') => {
    setNotification({ message, severity });
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <div className="app-container">
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Generator showNotification={showNotification} />} />
            <Route path="/history" element={<History showNotification={showNotification} />} />
            <Route path="/history/:id" element={<HistoryDetail showNotification={showNotification} />} />
            <Route path="/settings" element={<Settings showNotification={showNotification} />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
        <NotificationBar message={notification.message} severity={notification.severity} onClose={() => setNotification({ ...notification, message: '' })} />
      </div>
    </ThemeProvider>
  );
};

// Root App component with all providers
const App = () => {
  return (
    <BrowserRouter>
      <SettingsProvider>
        <AppContent />
      </SettingsProvider>
    </BrowserRouter>
  );
};

export default App; 