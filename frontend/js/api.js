/**
 * API Client for Warner Sound Tracker Backend
 */

// API base URL - will be set from environment or default to localhost
// For Vercel: The API URL will be injected via window.__API_BASE_URL__
// For local development: defaults to localhost
// Priority: window.__API_BASE_URL__ > environment variable > default
let API_BASE_URL = 'http://localhost:5001/api/v1';

// Check for injected API URL (set in index.html)
if (typeof window !== 'undefined' && window.__API_BASE_URL__) {
    API_BASE_URL = window.__API_BASE_URL__;
}
// Fallback: check for environment variable (for build-time injection)
else if (typeof process !== 'undefined' && process.env && process.env.VITE_API_BASE_URL) {
    API_BASE_URL = process.env.VITE_API_BASE_URL;
}

class ApiClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Health check
    async healthCheck() {
        return this.request('/health');
    }

    // Sessions
    async getSessions(limit = 50) {
        return this.request(`/sessions?limit=${limit}`);
    }

    async getSession(sessionId) {
        return this.request(`/sessions/${sessionId}`);
    }

    // Videos
    async getVideos(filters = {}) {
        const params = new URLSearchParams();
        if (filters.session_id) params.append('session_id', filters.session_id);
        if (filters.start_date) params.append('start_date', filters.start_date);
        if (filters.end_date) params.append('end_date', filters.end_date);
        if (filters.account) params.append('account', filters.account);
        if (filters.sound_key) params.append('sound_key', filters.sound_key);
        
        return this.request(`/videos?${params.toString()}`);
    }

    // Sounds
    async getSounds(sessionId = null) {
        const params = sessionId ? `?session_id=${sessionId}` : '';
        return this.request(`/sounds${params}`);
    }

    // Reports
    async generateReport(sessionId = null, soundKeys = null) {
        const body = {};
        if (sessionId) body.session_id = sessionId;
        if (soundKeys) body.sound_keys = soundKeys;

        return this.request('/reports/generate', {
            method: 'POST',
            body: JSON.stringify(body)
        });
    }
}

// Create global API client instance
const api = new ApiClient(API_BASE_URL);

