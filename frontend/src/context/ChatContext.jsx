/**
 * Chat Context for managing conversations
 */
import React, { createContext, useContext, useState, useCallback } from 'react';
import { chatApi } from '../api/chat';
import { maskPIIInText } from '../utils/piiDetector';

const ChatContext = createContext(null);

export const useChat = () => {
    const context = useContext(ChatContext);
    if (!context) {
        throw new Error('useChat must be used within ChatProvider');
    }
    return context;
};

export const ChatProvider = ({ children }) => {
    const [conversations, setConversations] = useState([]);
    const [currentConversation, setCurrentConversation] = useState(null);
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [sending, setSending] = useState(false);
    const [piiWarning, setPiiWarning] = useState(null);

    const loadConversations = useCallback(async () => {
        try {
            setLoading(true);
            const response = await chatApi.listConversations();
            setConversations(response.conversations);
        } catch (err) {
            console.error('Failed to load conversations:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    const loadConversation = useCallback(async (conversationId) => {
        try {
            setLoading(true);
            const response = await chatApi.getConversation(conversationId);
            setCurrentConversation(response);
            setMessages(response.messages || []);
        } catch (err) {
            console.error('Failed to load conversation:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    const createConversation = useCallback(async (title = null) => {
        try {
            const response = await chatApi.createConversation(title);
            setConversations((prev) => [response, ...prev]);
            setCurrentConversation(response);
            setMessages([]);
            return response;
        } catch (err) {
            console.error('Failed to create conversation:', err);
            throw err;
        }
    }, []);

    const sendMessage = useCallback(async (content, skipPiiCheck = false) => {
        // Check for PII before sending
        if (!skipPiiCheck) {
            const piiResult = maskPIIInText(content);
            if (piiResult.hasWarning) {
                setPiiWarning({
                    original: content,
                    masked: piiResult.maskedText,
                    detected: piiResult.detectedPII,
                });
                return { requiresConfirmation: true, piiWarning: piiResult };
            }
        }

        setPiiWarning(null);

        try {
            setSending(true);

            // Optimistically add user message
            const tempUserMessage = {
                id: 'temp-' + Date.now(),
                role: 'user',
                content,
                created_at: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, tempUserMessage]);

            // Send to API
            const response = await chatApi.sendMessage(
                content,
                currentConversation?.id
            );

            // Update with actual response
            setMessages((prev) => {
                const filtered = prev.filter((m) => m.id !== tempUserMessage.id);
                return [
                    ...filtered,
                    { ...tempUserMessage, id: response.message.id.replace(/-.*/, '') + '-user' },
                    response.message,
                ];
            });

            // Update current conversation
            if (!currentConversation) {
                setCurrentConversation({ id: response.conversation_id });
                loadConversations();
            }

            return { success: true, response };
        } catch (err) {
            // Remove optimistic message on error
            setMessages((prev) => prev.filter((m) => !m.id.startsWith('temp-')));
            throw err;
        } finally {
            setSending(false);
        }
    }, [currentConversation, loadConversations]);

    const confirmSendWithPII = useCallback(async () => {
        if (!piiWarning) return;

        // User confirmed to send original message with PII
        const content = piiWarning.original;
        setPiiWarning(null);
        return sendMessage(content, true);
    }, [piiWarning, sendMessage]);

    const sendMaskedMessage = useCallback(async () => {
        if (!piiWarning) return;

        // Send masked version
        const content = piiWarning.masked;
        setPiiWarning(null);
        return sendMessage(content, true);
    }, [piiWarning, sendMessage]);

    const cancelPiiWarning = useCallback(() => {
        setPiiWarning(null);
    }, []);

    const deleteConversation = useCallback(async (conversationId) => {
        try {
            await chatApi.deleteConversation(conversationId);
            setConversations((prev) => prev.filter((c) => c.id !== conversationId));
            if (currentConversation?.id === conversationId) {
                setCurrentConversation(null);
                setMessages([]);
            }
        } catch (err) {
            console.error('Failed to delete conversation:', err);
            throw err;
        }
    }, [currentConversation]);

    const newChat = useCallback(() => {
        setCurrentConversation(null);
        setMessages([]);
        setPiiWarning(null);
    }, []);

    const value = {
        conversations,
        currentConversation,
        messages,
        loading,
        sending,
        piiWarning,
        loadConversations,
        loadConversation,
        createConversation,
        sendMessage,
        confirmSendWithPII,
        sendMaskedMessage,
        cancelPiiWarning,
        deleteConversation,
        newChat,
    };

    return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};

export default ChatContext;
