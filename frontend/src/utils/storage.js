/**
 * Secure token storage utilities
 */

const ACCESS_TOKEN_KEY = 'ai_platform_access_token';
const REFRESH_TOKEN_KEY = 'ai_platform_refresh_token';

// Use memory storage for access token (more secure)
let memoryAccessToken = null;

/**
 * Get access token
 */
export const getToken = () => {
    // Try memory first, then sessionStorage
    return memoryAccessToken || sessionStorage.getItem(ACCESS_TOKEN_KEY);
};

/**
 * Get refresh token
 */
export const getRefreshToken = () => {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
};

/**
 * Store tokens
 */
export const setToken = (accessToken, refreshToken = null) => {
    memoryAccessToken = accessToken;
    sessionStorage.setItem(ACCESS_TOKEN_KEY, accessToken);

    if (refreshToken) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    }
};

/**
 * Clear all tokens
 */
export const clearTokens = () => {
    memoryAccessToken = null;
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
};

/**
 * Check if user has valid tokens
 */
export const hasTokens = () => {
    return !!getToken() || !!getRefreshToken();
};

/**
 * Parse JWT token payload (without verification)
 */
export const parseToken = (token) => {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
            atob(base64)
                .split('')
                .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                .join('')
        );
        return JSON.parse(jsonPayload);
    } catch {
        return null;
    }
};

/**
 * Check if token is expired
 */
export const isTokenExpired = (token) => {
    const payload = parseToken(token);
    if (!payload || !payload.exp) return true;

    // Add 10 second buffer
    return Date.now() >= (payload.exp * 1000 - 10000);
};
