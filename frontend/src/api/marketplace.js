/**
 * Marketplace API functions
 */
import api from './client';

export const marketplaceApi = {
    // Browse apps
    listApps: async (page = 1, perPage = 20, category = null, search = null) => {
        const params = { page, per_page: perPage };
        if (category) params.category = category;
        if (search) params.search = search;

        const response = await api.get('/marketplace/apps', { params });
        return response.data;
    },

    getApp: async (appSlug) => {
        const response = await api.get(`/marketplace/apps/${appSlug}`);
        return response.data;
    },

    getCategories: async () => {
        const response = await api.get('/marketplace/categories');
        return response.data;
    },

    // User's enabled apps
    getEnabledApps: async () => {
        const response = await api.get('/marketplace/my-apps');
        return response.data;
    },

    enableApp: async (appId, grantedPermissions = null) => {
        const response = await api.post(`/marketplace/apps/${appId}/enable`, {
            app_id: appId,
            granted_permissions: grantedPermissions,
        });
        return response.data;
    },

    disableApp: async (appId) => {
        const response = await api.delete(`/marketplace/apps/${appId}/disable`);
        return response.data;
    },
};

// Developer portal API
export const developerApi = {
    listMyApps: async (page = 1, perPage = 20, statusFilter = null) => {
        const params = { page, per_page: perPage };
        if (statusFilter) params.status_filter = statusFilter;

        const response = await api.get('/developer/apps', { params });
        return response.data;
    },

    createApp: async (appData) => {
        const response = await api.post('/developer/apps', appData);
        return response.data;
    },

    getMyApp: async (appId) => {
        const response = await api.get(`/developer/apps/${appId}`);
        return response.data;
    },

    updateApp: async (appId, appData) => {
        const response = await api.put(`/developer/apps/${appId}`, appData);
        return response.data;
    },

    deleteApp: async (appId) => {
        const response = await api.delete(`/developer/apps/${appId}`);
        return response.data;
    },

    submitForReview: async (appId) => {
        const response = await api.post(`/developer/apps/${appId}/submit-for-review`);
        return response.data;
    },

    getAppStats: async (appId) => {
        const response = await api.get(`/developer/apps/${appId}/stats`);
        return response.data;
    },
};

export default marketplaceApi;
