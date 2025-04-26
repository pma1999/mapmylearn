const Sitemap = require('react-router-sitemap').default;
const path = require('path');
const fs = require('fs');

// Placeholder: Define your routes. 
// This needs to be adjusted based on how routes are actually defined and exported in your App.js or routing configuration.
// For CRA, explicitly defining public routes might be simpler than importing complex App logic.
const routes = [
    '/',
    '/login',
    '/register',
    '/forgot-password'
    // Add any other *publicly* accessible routes here.
    // Do NOT add routes behind authentication like /generator, /history, /admin, /result/:taskId etc.
];

const paramsConfig = {
    // If you have dynamic public routes like /blog/:slug, configure them here
    // '/blog/:slug': [
    //     { slug: 'article-1' },
    //     { slug: 'article-2' }
    // ]
};

const sitemap = new Sitemap(routes)
    .applyParams(paramsConfig)
    .build('https://mapmylearn.app'); // IMPORTANT: Replace with your actual domain

const buildPath = path.resolve(__dirname, '../build');
const sitemapPath = path.join(buildPath, 'sitemap.xml');

// Ensure build directory exists
if (!fs.existsSync(buildPath)) {
    fs.mkdirSync(buildPath, { recursive: true });
}

sitemap.save(sitemapPath);

console.log(`Sitemap generated at ${sitemapPath}`); 