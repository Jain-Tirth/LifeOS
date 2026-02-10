import client from './client';

export const login = async (email, password) => {
    const response = await client.post('/auth/login/', { email, password });
    if (response.data.token) {
        localStorage.setItem('lifeos_token', response.data.token);
    }
    return response.data;
};

export const register = async (email, password, firstName, lastName) => {
    return client.post('/auth/register/', {
        email,
        password,
        first_name: firstName,
        last_name: lastName,
    });
};

export const getProfile = async () => {
    return client.get('/auth/profile/');
};

export const logout = () => {
    localStorage.removeItem('lifeos_token');
};
