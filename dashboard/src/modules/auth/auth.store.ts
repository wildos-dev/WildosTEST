import { fetch } from '@wildosvpn/common/utils';
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

// In-memory token storage for better XSS protection
let inMemoryToken: string | null = null;
let inMemoryRefreshToken: string | null = null;

type AdminStateType = {
    isLoggedIn: () => Promise<boolean>,
    getAuthToken: () => string | null;
    getRefreshToken: () => string | null;
    isSudo: () => boolean;
    setAuthToken: (token: string, persistToSession?: boolean) => void;
    setRefreshToken: (refreshToken: string) => void;
    setTokens: (token: string, refreshToken: string) => void;
    removeAuthToken: () => void;
    removeRefreshToken: () => void;
    removeAllTokens: () => void;
    refreshAuthToken: () => Promise<boolean>;
    setSudo: (isSudo: boolean) => void;
    initializeFromSession: () => void;
    persistCurrentSession: () => void;
    clearAllStorage: () => void;
}

export const useAuth = create(
    subscribeWithSelector<AdminStateType>(() => ({
        isLoggedIn: async () => {
            try {
                await fetch('/admins/current');
                return true;
            } catch (error) {
                return false;
            }
        },
        getAuthToken: () => {
            // Primary: in-memory token (most secure)
            if (inMemoryToken) {
                return inMemoryToken;
            }
            // Fallback: sessionStorage (better than localStorage)
            return sessionStorage.getItem('auth_token');
        },
        getRefreshToken: () => {
            // Primary: in-memory token (most secure)  
            if (inMemoryRefreshToken) {
                return inMemoryRefreshToken;
            }
            // Fallback: sessionStorage
            return sessionStorage.getItem('refresh_token');
        },
        isSudo: () => {
            // Allow dev sudo only with explicit flag and localhost/127.0.0.1 hostname
            if (import.meta.env.VITE_ENABLE_DEV_SUDO === 'true' && 
                (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
                return true;
            }
            
            // Check sessionStorage first (new secure location)
            const sessionSudo = sessionStorage.getItem('is-sudo');
            if (sessionSudo !== null) {
                return sessionSudo === "true";
            }
            
            // Fallback to localStorage for migration
            const legacySudo = localStorage.getItem('is-sudo');
            if (legacySudo !== null) {
                // Migrate to sessionStorage and clean up
                sessionStorage.setItem('is-sudo', legacySudo);
                localStorage.removeItem('is-sudo');
                return legacySudo === "true";
            }
            
            return false;
        },
        setSudo: (isSudo) => {
            if (isSudo) {
                // Keep sudo flag in sessionStorage (less sensitive than tokens)
                sessionStorage.setItem('is-sudo', 'true');
            } else {
                // Clear sudo flag from both storages when setting to false
                sessionStorage.removeItem('is-sudo');
            }
            
            // Clean up old localStorage
            localStorage.removeItem('is-sudo');
        },
        setAuthToken: (token: string, persistToSession = false) => {
            // Store in memory (most secure)
            inMemoryToken = token;
            
            // Optionally persist to sessionStorage for page refresh recovery
            if (persistToSession) {
                sessionStorage.setItem('auth_token', token);
            }
            
            // Remove any old localStorage token for migration
            localStorage.removeItem('token');
        },
        setRefreshToken: (refreshToken: string) => {
            // Note: Backend doesn't support refresh tokens, but keeping for future
            inMemoryRefreshToken = refreshToken;
            sessionStorage.setItem('refresh_token', refreshToken);
            
            // Remove old localStorage token
            localStorage.removeItem('refresh_token');
        },
        setTokens: (token: string, refreshToken: string) => {
            inMemoryToken = token;
            inMemoryRefreshToken = refreshToken;
            
            // Persist to session for recovery
            sessionStorage.setItem('auth_token', token);
            sessionStorage.setItem('refresh_token', refreshToken);
            
            // Clean up old localStorage
            localStorage.removeItem('token');
            localStorage.removeItem('refresh_token');
        },
        removeAuthToken: () => {
            // Clear from memory
            inMemoryToken = null;
            
            // Clear from sessionStorage
            sessionStorage.removeItem('auth_token');
            
            // Clean up legacy localStorage
            localStorage.removeItem('token');
        },
        removeRefreshToken: () => {
            // Clear from memory
            inMemoryRefreshToken = null;
            
            // Clear from sessionStorage
            sessionStorage.removeItem('refresh_token');
            
            // Clean up legacy localStorage  
            localStorage.removeItem('refresh_token');
        },
        removeAllTokens: () => {
            // Clear from memory
            inMemoryToken = null;
            inMemoryRefreshToken = null;
            
            // Clear from sessionStorage
            sessionStorage.removeItem('auth_token');
            sessionStorage.removeItem('refresh_token');
            
            // Clean up legacy localStorage
            localStorage.removeItem('token');
            localStorage.removeItem('refresh_token');
        },
        refreshAuthToken: async () => {
            // Backend doesn't support refresh tokens - tokens last 24 hours
            // This method is kept for future backend updates
            console.warn('Refresh tokens not supported by backend - tokens expire after 24 hours');
            return false;
        },
        
        initializeFromSession: () => {
            // Initialize in-memory tokens from sessionStorage on app start
            const sessionToken = sessionStorage.getItem('auth_token');
            const sessionRefreshToken = sessionStorage.getItem('refresh_token');
            
            if (sessionToken) {
                inMemoryToken = sessionToken;
            }
            if (sessionRefreshToken) {
                inMemoryRefreshToken = sessionRefreshToken;
            }
            
            // Migrate from old localStorage if needed
            const oldToken = localStorage.getItem('token');
            if (oldToken && !sessionToken) {
                inMemoryToken = oldToken;
                sessionStorage.setItem('auth_token', oldToken);
                localStorage.removeItem('token');
            }
        },
        
        persistCurrentSession: () => {
            // Explicitly persist in-memory tokens to sessionStorage
            if (inMemoryToken) {
                sessionStorage.setItem('auth_token', inMemoryToken);
            }
            if (inMemoryRefreshToken) {
                sessionStorage.setItem('refresh_token', inMemoryRefreshToken);
            }
        },
        
        clearAllStorage: () => {
            // Nuclear option - clear everything
            inMemoryToken = null;
            inMemoryRefreshToken = null;
            sessionStorage.clear();
            localStorage.removeItem('token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('is-sudo');
        },
    }))
)
