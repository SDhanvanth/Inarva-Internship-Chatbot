/**
 * Sidebar Component
 */
import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useChat } from '../../context/ChatContext';
import './Sidebar.css';

const Sidebar = () => {
    const { user, isAdmin, isDeveloper, logout } = useAuth();
    const { conversations, newChat, loadConversation } = useChat();
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    const handleNewChat = () => {
        newChat();
        navigate('/');
    };

    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <div className="sidebar-logo">
                    <span className="logo-icon">✨</span>
                    <span className="logo-text gradient-text">Multi Chat AI</span>
                </div>
                <button className="new-chat-btn" onClick={handleNewChat}>
                    <span>+</span> New Chat
                </button>
            </div>

            <nav className="sidebar-nav">
                <div className="nav-section">
                    <h3 className="nav-section-title">Main</h3>
                    <NavLink to="/" className="nav-link" end>
                        <span className="nav-icon">💬</span>
                        Chat
                    </NavLink>
                    <NavLink to="/marketplace" className="nav-link">
                        <span className="nav-icon">🏪</span>
                        Marketplace
                    </NavLink>
                    <NavLink to="/enabled-apps" className="nav-link">
                        <span className="nav-icon">⚡</span>
                        Enabled Apps
                    </NavLink>
                    <NavLink to="/usage" className="nav-link">
                        <span className="nav-icon">📊</span>
                        Usage & Limits
                    </NavLink>
                </div>

                {isDeveloper && (
                    <div className="nav-section">
                        <h3 className="nav-section-title">Developer</h3>
                        <NavLink to="/developer" className="nav-link">
                            <span className="nav-icon">🛠️</span>
                            My Apps
                        </NavLink>
                    </div>
                )}

                {isAdmin && (
                    <div className="nav-section">
                        <h3 className="nav-section-title">Admin</h3>
                        <NavLink to="/admin" className="nav-link">
                            <span className="nav-icon">⚙️</span>
                            Dashboard
                        </NavLink>
                    </div>
                )}

                {conversations.length > 0 && (
                    <div className="nav-section">
                        <h3 className="nav-section-title">Recent Chats</h3>
                        <div className="conversation-list">
                            {conversations.slice(0, 5).map((conv) => (
                                <button
                                    key={conv.id}
                                    className="conversation-item"
                                    onClick={() => {
                                        loadConversation(conv.id);
                                        navigate('/');
                                    }}
                                >
                                    <span className="conv-icon">💬</span>
                                    <span className="conv-title">{conv.title || 'New conversation'}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                )}
            </nav>

            <div className="sidebar-footer">
                <div className="user-info">
                    <div className="user-avatar">
                        {user?.full_name?.[0] || user?.email?.[0] || 'U'}
                    </div>
                    <div className="user-details">
                        <span className="user-name">{user?.full_name || user?.email}</span>
                        <span className="user-role">{user?.role}</span>
                    </div>
                </div>
                <button className="logout-btn" onClick={handleLogout}>
                    Logout
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
