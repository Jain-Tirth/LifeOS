import axios from 'axios';

const API_URL = '/api'; // Using proxy in development

const client = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add interceptor for auth token
client.interceptors.request.use((config) => {
    const token = localStorage.getItem('lifeos_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export default client;
