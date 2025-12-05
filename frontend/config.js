/**
 * Frontend configuration
 * This file is used to inject environment variables at build time for Vercel
 */

// API base URL - will be replaced during Vercel build
// For local development, this will be localhost
// For production, Vercel will replace this with the environment variable
window.__API_BASE_URL__ = '{{VITE_API_BASE_URL}}' || 'http://localhost:5001/api/v1';

