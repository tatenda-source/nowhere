import axios from 'axios';
import { getOrCreateIdentity, getAccessToken } from './identity';
import { API_URL } from './config';

export const api = axios.create({
    baseURL: API_URL,
    withCredentials: true,
    timeout: 10000,
});

api.interceptors.request.use(async (config) => {
    try {
        const token = await getAccessToken();
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
    } catch (e) {
        // Fallback — request proceeds without auth
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (!error.response) {
            // Network error (no response from server)
            error.userMessage = 'Cannot reach server. Check your connection.';
        } else if (error.response.status === 429) {
            const detail = error.response.data?.detail || 'Too many requests';
            error.userMessage = detail;
        } else if (error.response.status >= 500) {
            error.userMessage = 'Something went wrong on our end. Try again.';
        } else {
            error.userMessage = error.response.data?.detail || 'Something went wrong.';
        }
        return Promise.reject(error);
    }
);
