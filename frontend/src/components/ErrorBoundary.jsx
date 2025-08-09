import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    // eslint-disable-next-line no-console
    console.error('ErrorBoundary caught an error:', error, info);
  }

  render() {
    const { hasError } = this.state;
    const { fallback = null, children } = this.props;

    if (hasError) {
      return fallback || null;
    }

    return children;
  }
}

export default ErrorBoundary;
