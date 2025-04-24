const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Define Content Security Policy
  const csp = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://va.vercel-scripts.com",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.goin.cloud",
    "img-src 'self' data: https: http:",
    "font-src 'self' https://fonts.gstatic.com https://cdn.goin.cloud",
    "connect-src 'self' https://web-production-62f88.up.railway.app http://localhost:8000 https://api.stripe.com",
    "object-src 'none'",
    "frame-src 'self' https://js.stripe.com",
    "base-uri 'self'",
    "form-action 'self'",
    "media-src 'self' http://localhost:8000 https://web-production-62f88.up.railway.app"
  ].join('; ');

  app.use((req, res, next) => {
    // Apply CSP header
    res.setHeader('Content-Security-Policy', csp);
    
    // Other security headers (optional but recommended)
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('X-Frame-Options', 'DENY');
    res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
    res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload');
    
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