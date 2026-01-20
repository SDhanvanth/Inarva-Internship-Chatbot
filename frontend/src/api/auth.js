/**
 * Authentication API functions
 */
import api from './client';

export const authApi = {
    signup: async (email, password, fullName = null) => {
        const response = await api.post('/auth/signup', {
            email,
            password,
            full_name: fullName,
        });
        return response.data;
    },

    login: async (email, password) => {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await api.post('/auth/login', formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });
        return response.data;
    },

    logout: async (refreshToken) => {
        const response = await api.post('/auth/logout', {
            refresh_token: refreshToken,
        });
        return response.data;
    },

    refresh: async (refreshToken) => {
        const response = await api.post('/auth/refresh', {
            refresh_token: refreshToken,
        });
        return response.data;
    },

    getCurrentUser: async () => {
        const response = await api.get('/auth/me');
        return response.data;
    },

    changePassword: async (currentPassword, newPassword) => {
        const response = await api.post('/auth/change-password', {
            current_password: currentPassword,
            new_password: newPassword,
        });
        return response.data;
    },
};

export default authApi;
