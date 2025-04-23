const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use((req, res, next) => {
    // Define the Content Security Policy for the development environment
    const csp = [
      "default-src 'self'",
      // Allow Vercel debug script ONLY in development
      "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://va.vercel-scripts.com",
      "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.goin.cloud",
      "img-src 'self' data: https: http:",
      "font-src 'self' https://fonts.gstatic.com https://cdn.goin.cloud",
      // Allow connection to backend API (adjust target below if needed)
      "connect-src 'self' https://web-production-62f88.up.railway.app http://localhost:8000",
      "object-src 'none'",
      // Allow Stripe's iframe
      "frame-src 'self' https://js.stripe.com",
      "base-uri 'self'",
      "form-action 'self'"
    ].join('; ');

    res.setHeader('Content-Security-Policy', csp);
    next();
  });

  // Example: Add other proxy configurations if needed for API requests
  // Make sure the target matches your backend development server address
  // app.use(
  //   '/api',
  //   createProxyMiddleware({
  //     target: 'http://localhost:8000', // Your backend server
  //     changeOrigin: true,
  //   })
  // );
}; 