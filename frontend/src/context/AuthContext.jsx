/**
 * Authentication Context
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi } from '../api/auth';
import { setToken, clearTokens, getToken, getRefreshToken, parseToken, isTokenExpired } from '../utils/storage';

const AuthContext = createContext(null);

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Check auth status on mount
    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        try {
            const token = getToken();
            const refreshToken = getRefreshToken();

            if (!token && !refreshToken) {
                setLoading(false);
                return;
            }

            // If access token expired but refresh token exists, try refresh
            if ((!token || isTokenExpired(token)) && refreshToken) {
                try {
                    const response = await authApi.refresh(refreshToken);
                    setToken(response.access_token, response.refresh_token);
                } catch {
                    clearTokens();
                    setLoading(false);
                    return;
                }
            }

            // Fetch current user
            const userData = await authApi.getCurrentUser();
            setUser(userData);
        } catch (err) {
            clearTokens();
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const login = useCallback(async (email, password) => {
        try {
            setError(null);
            const response = await authApi.login(email, password);
            setToken(response.access_token, response.refresh_token);

            const userData = await authApi.getCurrentUser();
            setUser(userData);

            return { success: true };
        } catch (err) {
            const message = err.response?.data?.detail || 'Login failed';
            setError(message);
            return { success: false, error: message };
        }
    }, []);

    const signup = useCallback(async (email, password, fullName) => {
        try {
            setError(null);
            await authApi.signup(email, password, fullName);

            // Auto login after signup
            return await login(email, password);
        } catch (err) {
            const message = err.response?.data?.detail || 'Signup failed';
            setError(message);
            return { success: false, error: message };
        }
    }, [login]);

    const logout = useCallback(async () => {
        try {
            const refreshToken = getRefreshToken();
            if (refreshToken) {
                await authApi.logout(refreshToken);
            }
        } catch {
            // Ignore logout errors
        } finally {
            clearTokens();
            setUser(null);
        }
    }, []);

    const isAuthenticated = !!user;
    const isAdmin = user?.role === 'admin';
    const isDeveloper = user?.role === 'developer' || user?.role === 'admin';

    const value = {
        user,
        loading,
        error,
        isAuthenticated,
        isAdmin,
        isDeveloper,
        login,
        signup,
        logout,
        checkAuth,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
