/**
 * Chat API functions
 */
import api from './client';

export const chatApi = {
    // Conversations
    listConversations: async (page = 1, perPage = 20, includeArchived = false) => {
        const response = await api.get('/chat/conversations', {
            params: { page, per_page: perPage, include_archived: includeArchived },
        });
        return response.data;
    },

    createConversation: async (title = null) => {
        const response = await api.post('/chat/conversations', { title });
        return response.data;
    },

    getConversation: async (conversationId) => {
        const response = await api.get(`/chat/conversations/${conversationId}`);
        return response.data;
    },

    deleteConversation: async (conversationId) => {
        const response = await api.delete(`/chat/conversations/${conversationId}`);
        return response.data;
    },

    archiveConversation: async (conversationId) => {
        const response = await api.post(`/chat/conversations/${conversationId}/archive`);
        return response.data;
    },

    // Messages
    sendMessage: async (message, conversationId = null) => {
        const response = await api.post('/chat/send', {
            message,
            conversation_id: conversationId,
        });
        return response.data;
    },

    // Tools
    getEnabledTools: async () => {
        const response = await api.get('/chat/enabled-tools');
        return response.data;
    },
};

export default chatApi;
