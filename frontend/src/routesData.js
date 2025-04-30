/**
 * Centralized route DATA configuration for the application.
 * This file contains only serializable data (paths, flags)
 * and does NOT import React components, making it safe to require
 * directly in Node.js build scripts.
 *
 * Properties:
 * - path: The URL path for the route.
 * - requiresAuth: Boolean, true if the route requires authentication.
 * - adminOnly: Boolean, true if the route requires admin privileges.
 * - isPublic: Boolean, true if the route should be included in the sitemap.xml.
 */
const routesData = [
  {
    path: '/',
    requiresAuth: false,
    isPublic: true,
  },
  {
    path: '/generator',
    requiresAuth: true,
    isPublic: false,
  },
  {
    path: '/history',
    requiresAuth: true,
    isPublic: false,
  },
  {
    path: '/login',
    requiresAuth: false,
    isPublic: true,
  },
  {
    path: '/register',
    requiresAuth: false,
    isPublic: true,
  },
  {
    path: '/verify-email',
    requiresAuth: false,
    isPublic: true,
  },
  {
    path: '/forgot-password',
    requiresAuth: false,
    isPublic: true,
  },
  {
    path: '/reset-password/:token',
    requiresAuth: false,
    isPublic: false,
  },
  {
    path: '/admin',
    requiresAuth: true,
    adminOnly: true,
    isPublic: false,
  },
  {
    path: '/result/:taskId',
    requiresAuth: true,
    isPublic: false,
  },
  {
    path: '/history/:entryId',
    requiresAuth: true,
    isPublic: false,
  },
  {
    path: '/purchase/success',
    requiresAuth: true,
    isPublic: false,
  },
  {
    path: '/purchase/cancel',
    requiresAuth: true,
    isPublic: false,
  },
  // Add new routes data here
  {
    path: '/terms',
    requiresAuth: false,
    isPublic: true,
  },
  {
    path: '/privacy',
    requiresAuth: false,
    isPublic: true,
  },
];

// Export using module.exports for compatibility with require()
module.exports = routesData; 