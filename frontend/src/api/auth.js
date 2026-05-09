import client from './client';

// Secure token storage using httpOnly cookies is recommended for production
// For now, we use localStorage but tokens should be migrated to httpOnly cookies
// See: https://owasp.org/www-community/controls/xss/

export const login = async (email, password) => {
    const response = await client.post('/auth/login/', { email, password });
    if (response.data.token) {
        // Store both access and refresh tokens for token rotation
        localStorage.setItem('lifeos_access_token', response.data.token);
        localStorage.setItem('lifeos_token', response.data.token);
        if (response.data.refresh) {
            localStorage.setItem('lifeos_refresh_token', response.data.refresh);
        }
    }
    if (response.data.access) {
        localStorage.setItem('lifeos_access_token', response.data.access);
        localStorage.setItem('lifeos_token', response.data.access);
    }
    if (response.data.refresh) {
        localStorage.setItem('lifeos_refresh_token', response.data.refresh);
    }
    return response.data;
};

export const register = async (email, password, firstName, lastName) => {
    const response = await client.post('/auth/register/', {
        email,
        password,
        password_confirm: password,
        first_name: firstName,
        last_name: lastName,
    });

    if (response.data.token) {
        localStorage.setItem('lifeos_token', response.data.token);
        localStorage.setItem('lifeos_access_token', response.data.token);
    }

    if (response.data.access) {
        localStorage.setItem('lifeos_access_token', response.data.access);
        localStorage.setItem('lifeos_token', response.data.access);
    }
    if (response.data.refresh) {
        localStorage.setItem('lifeos_refresh_token', response.data.refresh);
    }

    return response.data;
};

export const getProfile = async () => {
    return client.get('/auth/profile/');
};

export const logout = () => {
    localStorage.removeItem('lifeos_access_token');
    localStorage.removeItem('lifeos_refresh_token');
    localStorage.removeItem('lifeos_token');
};

export const requestPasswordReset = async (email) => {
    return client.post('/auth/password-reset/', { email });
};

export const resetPassword = async (uid, token, password) => {
    return client.post('/auth/password-reset-confirm/', { uid, token, password });
};
