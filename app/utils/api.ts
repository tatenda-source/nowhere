import axios from 'axios';
import { getOrCreateIdentity, getAccessToken } from './identity';
import { API_URL } from './config';

export const api = axios.create({
    baseURL: API_URL,
    timeout: 10000,
});

api.interceptors.request.use(async (config) => {
    try {
        const token = await getAccessToken();
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
    } catch {
        // Fallback — request proceeds without auth
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        if (!error.response) {
            error.userMessage = 'Cannot reach server. Check your connection.';
        } else if (error.response.status === 401 && !error.config._retried) {
            // Token expired — clear and retry once with a fresh handshake
            error.config._retried = true;
            try {
                const token = await getAccessToken();
                if (token) {
                    error.config.headers['Authorization'] = `Bearer ${token}`;
                    return api.request(error.config);
                }
            } catch {
                // Fall through to rejection
            }
            error.userMessage = 'Session expired. Please restart the app.';
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
