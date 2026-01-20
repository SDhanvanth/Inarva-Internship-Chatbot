/**
 * Admin API functions
 */
import api from './client';

export const adminApi = {
    // System
    getSystemHealth: async () => {
        const response = await api.get('/admin/system/health');
        return response.data;
    },

    getServerInfo: async () => {
        const response = await api.get('/admin/system/info');
        return response.data;
    },

    // Logs
    getRequestLogs: async (params = {}) => {
        const response = await api.get('/admin/logs/requests', { params });
        return response.data;
    },

    getAuditLogs: async (params = {}) => {
        const response = await api.get('/admin/audit-logs', { params });
        return response.data;
    },

    // Users
    listUsers: async (page = 1, perPage = 50, filters = {}) => {
        const response = await api.get('/admin/users', {
            params: { page, per_page: perPage, ...filters },
        });
        return response.data;
    },

    getUser: async (userId) => {
        const response = await api.get(`/admin/users/${userId}`);
        return response.data;
    },

    updateUser: async (userId, data) => {
        const response = await api.patch(`/admin/users/${userId}`, data);
        return response.data;
    },

    // App moderation
    getPendingApps: async () => {
        const response = await api.get('/admin/apps/pending');
        return response.data;
    },

    moderateApp: async (appId, status, rejectionReason = null) => {
        const response = await api.post(`/admin/apps/${appId}/moderate`, {
            status,
            rejection_reason: rejectionReason,
        });
        return response.data;
    },
};

export default adminApi;
