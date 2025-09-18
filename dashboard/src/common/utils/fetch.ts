
import apiClient, { api, apiRequest } from './http';

// REMOVED: Raw $fetch that bypassed interceptors - use apiClient instead

// Re-export the new unified API client and methods
export { apiClient as fetch };
export { api, apiRequest };

// Legacy alias for backward compatibility
export const fetcher = apiClient;
