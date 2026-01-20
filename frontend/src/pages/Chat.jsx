/**
 * Chat Page
 */
import React, { useState, useEffect, useRef } from 'react';
import { useChat } from '../context/ChatContext';
import { formatRelativeTime } from '../utils/validation';
import ReactMarkdown from 'react-markdown';
import './Chat.css';

const Chat = () => {
    const {
        messages,
        loading,
        sending,
        piiWarning,
        sendMessage,
        confirmSendWithPII,
        sendMaskedMessage,
        cancelPiiWarning,
        loadConversations,
    } = useChat();

    const [input, setInput] = useState('');
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    useEffect(() => {
        loadConversations();
    }, [loadConversations]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim() || sending) return;

        const message = input.trim();
        setInput('');

        try {
            await sendMessage(message);
        } catch (err) {
            console.error('Failed to send message:', err);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    return (
        <div className="chat-page">
            <div className="chat-messages">
                {messages.length === 0 && !loading && (
                    <div className="chat-welcome">
                        <div className="welcome-icon">✨</div>
                        <h2>Welcome to AI Platform</h2>
                        <p>Start a conversation or enable apps from the marketplace to extend capabilities.</p>
                        <div className="welcome-suggestions">
                            <button onClick={() => setInput('What can you help me with?')}>
                                What can you help me with?
                            </button>
                            <button onClick={() => setInput('Tell me about the marketplace')}>
                                Tell me about the marketplace
                            </button>
                            <button onClick={() => setInput('How do I enable apps?')}>
                                How do I enable apps?
                            </button>
                        </div>
                    </div>
                )}

                {messages.map((msg) => (
                    <div key={msg.id} className={`message message-${msg.role}`}>
                        <div className="message-avatar">
                            {msg.role === 'user' ? '👤' : '🤖'}
                        </div>
                        <div className="message-content">
                            <div className="message-header">
                                <span className="message-role">
                                    {msg.role === 'user' ? 'You' : 'Assistant'}
                                </span>
                                <span className="message-time">
                                    {formatRelativeTime(msg.created_at)}
                                </span>
                            </div>
                            <div className="message-text">
                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                            </div>
                            {msg.tool_calls && msg.tool_calls.length > 0 && (
                                <div className="message-tools">
                                    {msg.tool_calls.map((tool, idx) => (
                                        <div key={idx} className="tool-call">
                                            <span className="tool-icon">🔧</span>
                                            <span className="tool-name">{tool.name}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {sending && (
                    <div className="message message-assistant">
                        <div className="message-avatar">🤖</div>
                        <div className="message-content">
                            <div className="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* PII Warning Modal */}
            {piiWarning && (
                <div className="pii-warning-overlay">
                    <div className="pii-warning-modal glass">
                        <h3>⚠️ Sensitive Information Detected</h3>
                        <p>Your message contains potentially sensitive information:</p>
                        <div className="pii-detected">
                            {piiWarning.detected.map((pii, idx) => (
                                <span key={idx} className="pii-tag">
                                    {pii.type}: {pii.masked}
                                </span>
                            ))}
                        </div>
                        <div className="pii-actions">
                            <button className="btn-secondary" onClick={cancelPiiWarning}>
                                Cancel
                            </button>
                            <button className="btn-primary" onClick={sendMaskedMessage}>
                                Send Masked
                            </button>
                            <button className="btn-warning" onClick={confirmSendWithPII}>
                                Send Original
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <form onSubmit={handleSubmit} className="chat-input-form">
                <div className="chat-input-container">
                    <textarea
                        ref={inputRef}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type your message..."
                        rows={1}
                        disabled={sending}
                    />
                    <button type="submit" disabled={!input.trim() || sending}>
                        <span>Send</span>
                        <span>→</span>
                    </button>
                </div>
                <p className="chat-disclaimer">
                    AI responses may not always be accurate. Verify important information.
                </p>
            </form>
        </div>
    );
};

export default Chat;
