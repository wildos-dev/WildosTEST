import { FetchOptions, ofetch } from 'ofetch';
import { useAuth } from '@wildosvpn/modules/auth';

// Global flag to prevent multiple simultaneous logout attempts
let logoutInProgress = false;

// Helper function to handle authentication failures (only for 401, NOT 403)
function handleAuthFailure() {
    // Prevent multiple simultaneous logout attempts
    if (logoutInProgress) {
        return;
    }
    logoutInProgress = true;
    
    // Clear authentication state using auth store methods
    const authStore = useAuth.getState();
    authStore.removeAllTokens();
    
    // Clear sudo flag using auth store method (handles sessionStorage + localStorage)
    authStore.setSudo(false);
    
    // Prevent redirect loop if already on login page
    if (window.location.hash !== '#/login') {
        // Redirect to login page using hash routing
        window.location.hash = '#/login';
    }
    
    // Show user-friendly error message
    console.warn('Session expired. Please login again.');
    
    // Reset flag after a brief delay to allow for potential future 401s
    setTimeout(() => {
        logoutInProgress = false;
    }, 1000);
}

// Unified API client with interceptors
export const apiClient = ofetch.create({
    baseURL: '/api/',
    onRequest({ options }) {
        // Inject Authorization header from auth store
        const token = useAuth.getState().getAuthToken();
        if (token) {
            options.headers = {
                ...(options.headers || {}),
                Authorization: `Bearer ${token}`,
            } as any;
        }
        
        // Ensure JSON headers for POST/PUT/PATCH requests (but not for FormData)
        if (options.method && ['POST', 'PUT', 'PATCH'].includes(options.method.toUpperCase())) {
            // Don't set Content-Type for FormData - browser will set it with boundary
            if (!(options.body instanceof FormData)) {
                options.headers = {
                    ...(options.headers || {}),
                    'Content-Type': 'application/json',
                } as any;
            }
        }
    },
    async onResponseError({ response }) {
        // Handle 401 errors by immediately logging out
        if (response.status === 401) {
            handleAuthFailure();
        }
        
        // IMPORTANT: DO NOT logout on 403 - this is an authorization failure, not authentication
        // 403 means the user is authenticated but not authorized for this resource
        // Users should NOT be logged out for authorization failures
        
        // Re-throw the error for other status codes
        // Create an Axios-compatible error structure for consistent handling
        const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
        (error as any).response = response;
        throw error;
    }
});

// Convenient API methods
export const api = {
    get: <T = any>(url: string, options?: FetchOptions<'json'>) => 
        apiClient<T>(url, { ...options, method: 'GET' }),
    
    post: <T = any, B = any>(url: string, body?: B, options?: FetchOptions<'json'>) => 
        apiClient<T>(url, { ...options, method: 'POST', body } as any),
    
    put: <T = any, B = any>(url: string, body?: B, options?: FetchOptions<'json'>) => 
        apiClient<T>(url, { ...options, method: 'PUT', body } as any),
    
    patch: <T = any, B = any>(url: string, body?: B, options?: FetchOptions<'json'>) => 
        apiClient<T>(url, { ...options, method: 'PATCH', body } as any),
    
    delete: <T = any>(url: string, options?: FetchOptions<'json'>) => 
        apiClient<T>(url, { ...options, method: 'DELETE' }),
};

// External API client for third-party services (GitHub, etc.)
// Does not include auth interceptors since external APIs don't need our tokens
export const externalApiClient = ofetch.create({
    // No baseURL - external APIs use full URLs
    // No auth interceptors - external APIs handle their own authentication
});

// External API methods for third-party services  
export const externalApi = {
    get: <T = any>(url: string, options?: FetchOptions<'json'>) => 
        externalApiClient<T>(url, { ...options, method: 'GET' }),
    
    post: <T = any, B = any>(url: string, body?: B, options?: FetchOptions<'json'>) => 
        externalApiClient<T>(url, { ...options, method: 'POST', body } as any),
};

// Legacy compatibility for React Query mutations
export const apiRequest = <T = any>(url: string, options?: FetchOptions<'json'>) => 
    apiClient<T>(url, options);

// Default export for React Query
export default apiClient;