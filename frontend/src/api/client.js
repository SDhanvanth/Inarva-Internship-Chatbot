/**
 * API Client with authentication handling
 */
import axios from 'axios';
import { getToken, setToken, clearTokens, getRefreshToken } from '../utils/storage';

const API_BASE_URL = '/api/v1';

// Create axios instance
const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor - add auth token
api.interceptors.request.use(
    (config) => {
        const token = getToken();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor - handle token refresh
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // If 401 and not already retrying, try to refresh token
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const refreshToken = getRefreshToken();
                if (refreshToken) {
                    const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                        refresh_token: refreshToken,
                    });

                    const { access_token, refresh_token } = response.data;
                    setToken(access_token, refresh_token);

                    originalRequest.headers.Authorization = `Bearer ${access_token}`;
                    return api(originalRequest);
                }
            } catch (refreshError) {
                clearTokens();
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }

        // Handle rate limiting
        if (error.response?.status === 429) {
            const retryAfter = error.response.headers['retry-after'];
            error.retryAfter = parseInt(retryAfter) || 60;
        }

        return Promise.reject(error);
    }
);

export default api;

// Helper function for handling API errors
export const handleApiError = (error) => {
    if (error.response) {
        const { data, status } = error.response;
        return {
            message: data.message || data.error || 'An error occurred',
            status,
            details: data.details,
            retryAfter: error.retryAfter,
        };
    }
    if (error.request) {
        return {
            message: 'Network error. Please check your connection.',
            status: 0,
        };
    }
    return {
        message: error.message || 'An unexpected error occurred',
        status: -1,
    };
};
