/**
 * Header Component
 */
import React from 'react';
import { useLocation } from 'react-router-dom';
import './Header.css';

const pageTitles = {
    '/': 'Chat',
    '/marketplace': 'Marketplace',
    '/enabled-apps': 'Enabled Apps',
    '/usage': 'Usage & Limits',
    '/developer': 'Developer Portal',
    '/admin': 'Admin Dashboard',
};

const Header = () => {
    const location = useLocation();
    const title = pageTitles[location.pathname] || 'Multi Chat AI';

    return (
        <header className="header">
            <h1 className="header-title">{title}</h1>
            <div className="header-actions">
                <div className="search-box">
                    <span className="search-icon">🔍</span>
                    <input type="text" placeholder="Search..." />
                </div>
            </div>
        </header>
    );
};

export default Header;
