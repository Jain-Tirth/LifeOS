import axios from 'axios';

// Helper to get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

export const apiBaseUrl = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '');

// Use VITE_API_URL in production and fall back to the local Vite proxy in dev.
const client = axios.create({
    baseURL: apiBaseUrl,
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true, // Important for session auth and CSRF
});

// Initialize CSRF token on app load
export const initCSRF = async () => {
    try {
        await client.get('/auth/csrf/');
    } catch (error) {
        console.error('Failed to initialize CSRF token:', error);
    }
};

// Add interceptor for auth token and CSRF
client.interceptors.request.use((config) => {
    // Add JWT token if available
    // SECURITY NOTE: In production, tokens should be stored in httpOnly cookies
    // and automatically sent with requests via withCredentials
    const token = localStorage.getItem('lifeos_access_token') || localStorage.getItem('lifeos_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add CSRF token for session authentication
    const csrfToken = getCookie('csrftoken');
    if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
    }
    
    return config;
});

// Handle token expiration with proper error handling
client.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // Prevent infinite retry loops
        if (originalRequest._retry) {
            return Promise.reject(error);
        }

        if (error.response && error.response.status === 401 && originalRequest) {
            const refreshToken = localStorage.getItem('lifeos_refresh_token');
            
            // Only attempt refresh if we have a refresh token
            if (refreshToken) {
                originalRequest._retry = true;
                try {
                    const refreshClient = axios.create({
                        baseURL: apiBaseUrl,
                        headers: { 'Content-Type': 'application/json' },
                        withCredentials: true,
                    });

                    const refreshResponse = await refreshClient.post('/auth/refresh/', {
                        refresh: refreshToken,
                    });

                    const newAccessToken = refreshResponse.data.access;
                    const newRefreshToken = refreshResponse.data.refresh || refreshToken;

                    // Update tokens in storage
                    localStorage.setItem('lifeos_access_token', newAccessToken);
                    localStorage.setItem('lifeos_refresh_token', newRefreshToken);
                    localStorage.setItem('lifeos_token', newAccessToken);

                    // Retry original request with new token
                    originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
                    return client(originalRequest);
                } catch (refreshError) {
                    // Refresh failed - clear tokens and redirect to login
                    localStorage.removeItem('lifeos_access_token');
                    localStorage.removeItem('lifeos_refresh_token');
                    localStorage.removeItem('lifeos_token');
                    
                    // Don't redirect if already on login page or if refresh endpoint failed
                    if (window.location.pathname !== '/login' && 
                        !originalRequest.url?.includes('/auth/refresh/')) {
                        window.location.href = '/login';
                    }
                    return Promise.reject(refreshError);
                }
            }

            // No refresh token - redirect to login if not already there
            if (window.location.pathname !== '/login') {
                window.location.href = '/login';
            }
        }

        return Promise.reject(error);
    }
);

export default client;

// SECURITY RECOMMENDATIONS FOR PRODUCTION:
// 1. Migrate token storage from localStorage to httpOnly cookies
// 2. Implement Content Security Policy (CSP) headers
// 3. Add input validation library (e.g., Zod, Yup) for user inputs
// 4. Enable Subresource Integrity (SRI) for all external scripts
