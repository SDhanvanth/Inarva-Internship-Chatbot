/**
 * Main Application Component
 */
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ChatProvider } from './context/ChatContext';

// Pages
import Login from './pages/Login';
import Signup from './pages/Signup';
import Chat from './pages/Chat';
import Marketplace from './pages/Marketplace';
import EnabledApps from './pages/EnabledApps';
import AppDetails from './pages/AppDetails';
import Usage from './pages/Usage';
import DeveloperPortal from './pages/DeveloperPortal';
import AdminDashboard from './pages/admin/AdminDashboard';

// Layout
import Layout from './components/layout/Layout';

// Protected Route wrapper
const ProtectedRoute = ({ children, requireAdmin = false, requireDeveloper = false }) => {
    const { isAuthenticated, isAdmin, isDeveloper, loading } = useAuth();

    if (loading) {
        return (
            <div className="loading-screen">
                <div className="loader"></div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    if (requireAdmin && !isAdmin) {
        return <Navigate to="/" replace />;
    }

    if (requireDeveloper && !isDeveloper) {
        return <Navigate to="/" replace />;
    }

    return children;
};

// Public Route (redirect if authenticated)
const PublicRoute = ({ children }) => {
    const { isAuthenticated, loading } = useAuth();

    if (loading) {
        return (
            <div className="loading-screen">
                <div className="loader"></div>
            </div>
        );
    }

    if (isAuthenticated) {
        return <Navigate to="/" replace />;
    }

    return children;
};

const AppRoutes = () => {
    return (
        <Routes>
            {/* Public routes */}
            <Route
                path="/login"
                element={
                    <PublicRoute>
                        <Login />
                    </PublicRoute>
                }
            />
            <Route
                path="/signup"
                element={
                    <PublicRoute>
                        <Signup />
                    </PublicRoute>
                }
            />

            {/* Protected routes */}
            <Route
                path="/"
                element={
                    <ProtectedRoute>
                        <Layout>
                            <Chat />
                        </Layout>
                    </ProtectedRoute>
                }
            />
            <Route
                path="/marketplace"
                element={
                    <ProtectedRoute>
                        <Layout>
                            <Marketplace />
                        </Layout>
                    </ProtectedRoute>
                }
            />
            <Route
                path="/marketplace/:appSlug"
                element={
                    <ProtectedRoute>
                        <Layout>
                            <AppDetails />
                        </Layout>
                    </ProtectedRoute>
                }
            />
            <Route
                path="/enabled-apps"
                element={
                    <ProtectedRoute>
                        <Layout>
                            <EnabledApps />
                        </Layout>
                    </ProtectedRoute>
                }
            />
            <Route
                path="/usage"
                element={
                    <ProtectedRoute>
                        <Layout>
                            <Usage />
                        </Layout>
                    </ProtectedRoute>
                }
            />

            {/* Developer routes */}
            <Route
                path="/developer"
                element={
                    <ProtectedRoute requireDeveloper>
                        <Layout>
                            <DeveloperPortal />
                        </Layout>
                    </ProtectedRoute>
                }
            />

            {/* Admin routes */}
            <Route
                path="/admin/*"
                element={
                    <ProtectedRoute requireAdmin>
                        <Layout>
                            <AdminDashboard />
                        </Layout>
                    </ProtectedRoute>
                }
            />

            {/* Catch all */}
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    );
};

const App = () => {
    return (
        <BrowserRouter>
            <AuthProvider>
                <ChatProvider>
                    <AppRoutes />
                </ChatProvider>
            </AuthProvider>
        </BrowserRouter>
    );
};

export default App;
