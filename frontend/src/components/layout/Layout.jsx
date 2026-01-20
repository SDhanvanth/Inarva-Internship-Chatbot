/**
 * Main Layout Component
 */
import React from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import './Layout.css';

const Layout = ({ children }) => {
    return (
        <div className="layout">
            <Sidebar />
            <div className="layout-main">
                <Header />
                <main className="layout-content">
                    {children}
                </main>
            </div>
        </div>
    );
};

export default Layout;
