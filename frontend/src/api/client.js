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

// Use relative path - Vite proxy will forward /api requests to Django
const client = axios.create({
    baseURL: '/api',
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
    const token = localStorage.getItem('lifeos_token');
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

// Handle token expiration
client.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            // Token expired or invalid
            localStorage.removeItem('lifeos_token');
            // Optionally redirect to login
            if (window.location.pathname !== '/login') {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default client;
