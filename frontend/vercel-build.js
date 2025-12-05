#!/usr/bin/env node
/**
 * Vercel build script to inject API base URL into frontend
 * This script replaces the API_BASE_URL placeholder in index.html
 */

const fs = require('fs');
const path = require('path');

// Get API base URL from environment variable
const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:5001/api/v1';

// Read index.html
const indexPath = path.join(__dirname, 'index.html');
let html = fs.readFileSync(indexPath, 'utf8');

// Replace API_BASE_URL placeholder
html = html.replace(
    /window\.__API_BASE_URL__ = window\.__API_BASE_URL__ \|\|[\s\S]*?'http:\/\/localhost:5001\/api\/v1';/,
    `window.__API_BASE_URL__ = '${API_BASE_URL}';`
);

// Write back
fs.writeFileSync(indexPath, html, 'utf8');

console.log(`✅ Injected API_BASE_URL: ${API_BASE_URL}`);

