const Sitemap = require('react-router-sitemap').default;
const path = require('path');
const fs = require('fs');

// Import the central route configuration DATA
// This file only contains serializable data (paths, flags)
let routesData;
try {
  // Require the new routesData file which uses module.exports
  routesData = require('../src/routesData'); 
} catch (error) {
  console.error("Error: Could not load routes configuration from '../src/routesData.js'.", error);
  console.error("Ensure the path is correct relative to where the script is executed.");
  process.exit(1); // Exit if config cannot be loaded
}

// Filter for routes marked as public in the configuration data
const publicPaths = routesData
  .filter(route => route.isPublic)
  .map(route => route.path);

// Format paths for the Sitemap constructor
const sitemapPathsConfig = publicPaths.map(p => ({ path: p }));

// Determine the base URL
// Use PUBLIC_URL standard env variable provided by Create React App during build
const baseUrl = process.env.PUBLIC_URL;
if (!baseUrl) {
  console.warn(
    'Warning: PUBLIC_URL environment variable not set. Falling back to \'https://mapmylearn.com/\'.' + 
    ' Ensure PUBLIC_URL is set in your build environment for correct sitemap URLs.'
  );
}
const domain = baseUrl || 'https://mapmylearn.com/'; // Fallback domain

// We don't have any public dynamic routes requiring paramsConfig
// const paramsConfig = {};

let sitemapInstance;
try {
  // Generate sitemap using the discovered public paths (formatted as objects) and the determined domain
  sitemapInstance = new Sitemap(sitemapPathsConfig).build(domain);
} catch (error) {
  console.error("Error: Failed to build the sitemap.", error);
  process.exit(1);
}

const buildPath = path.resolve(__dirname, '../build');
const sitemapPath = path.join(buildPath, 'sitemap.xml');

try {
  // Ensure build directory exists
  if (!fs.existsSync(buildPath)) {
    fs.mkdirSync(buildPath, { recursive: true });
    console.log(`Created build directory: ${buildPath}`)
  }

  // Save the sitemap
  sitemapInstance.save(sitemapPath);

  console.log(`Sitemap generated successfully for domain ${domain} at: ${sitemapPath}`);
  console.log(`Included public paths: ${publicPaths.join(', ')}`);

} catch (error) {
  console.error(`Error: Could not save sitemap to ${sitemapPath}.`, error);
  process.exit(1);
} 