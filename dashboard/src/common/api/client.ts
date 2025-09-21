import { FetchOptions, ofetch } from 'ofetch';
import { z } from 'zod';
import { useAuth } from '@wildosvpn/modules/auth';
import { 
  PaginationParams, 
  SortingParams, 
  ErrorResponseSchema 
} from './schemas';

/**
 * Typed API client with proper error handling and validation
 */

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
  
  // Clear sudo flag using auth store method
  authStore.setSudo(false);
  
  // Prevent redirect loop if already on login page
  if (window.location.hash !== '#/login') {
    window.location.hash = '#/login';
  }
  
  // Show user-friendly error message
  console.warn('Session expired. Please login again.');
  
  // Reset flag after a brief delay
  setTimeout(() => {
    logoutInProgress = false;
  }, 1000);
}

// Custom error class for API errors
export class ApiError extends Error {
  public readonly status: number;
  public readonly response?: Response;
  
  constructor(message: string, status: number, response?: Response) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.response = response;
  }
  
  static isApiError(error: unknown): error is ApiError {
    return error instanceof ApiError;
  }
}

// Typed API client configuration
interface ApiClientConfig extends FetchOptions {
  validateResponse?: boolean;
}

// Create the typed API client
const createTypedApiClient = () => {
  const client = ofetch.create({
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
        throw new ApiError('Authentication required', 401, response);
      }
      
      // Parse error response for better error messages
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        const parsed = ErrorResponseSchema.safeParse(errorData);
        if (parsed.success) {
          errorMessage = parsed.data.detail;
        }
      } catch {
        // Fallback to status text if parsing fails
      }
      
      throw new ApiError(errorMessage, response.status, response);
    }
  });

  return client;
};

export const apiClient = createTypedApiClient();

// Typed API methods with validation
export const api = {
  get: async <T extends z.ZodTypeAny>(
    url: string, 
    schema: T, 
    options?: ApiClientConfig
  ): Promise<z.infer<T>> => {
    const { validateResponse = true, ...fetchOptions } = options || {};
    const response = await apiClient(url, { ...fetchOptions, method: 'GET' });
    
    if (validateResponse) {
      const result = schema.safeParse(response);
      if (!result.success) {
        throw new ApiError(
          `Invalid response format: ${result.error.message}`,
          422
        );
      }
      return result.data;
    }
    
    return response;
  },
  
  post: async <T extends z.ZodTypeAny, B = any>(
    url: string,
    schema: T,
    body?: B,
    options?: ApiClientConfig
  ): Promise<z.infer<T>> => {
    const { validateResponse = true, ...fetchOptions } = options || {};
    const response = await apiClient(url, { 
      ...fetchOptions, 
      method: 'POST', 
      body 
    } as any);
    
    if (validateResponse) {
      const result = schema.safeParse(response);
      if (!result.success) {
        throw new ApiError(
          `Invalid response format: ${result.error.message}`,
          422
        );
      }
      return result.data;
    }
    
    return response;
  },
  
  put: async <T extends z.ZodTypeAny, B = any>(
    url: string,
    schema: T,
    body?: B,
    options?: ApiClientConfig
  ): Promise<z.infer<T>> => {
    const { validateResponse = true, ...fetchOptions } = options || {};
    const response = await apiClient(url, { 
      ...fetchOptions, 
      method: 'PUT', 
      body 
    } as any);
    
    if (validateResponse) {
      const result = schema.safeParse(response);
      if (!result.success) {
        throw new ApiError(
          `Invalid response format: ${result.error.message}`,
          422
        );
      }
      return result.data;
    }
    
    return response;
  },
  
  patch: async <T extends z.ZodTypeAny, B = any>(
    url: string,
    schema: T,
    body?: B,
    options?: ApiClientConfig
  ): Promise<z.infer<T>> => {
    const { validateResponse = true, ...fetchOptions } = options || {};
    const response = await apiClient(url, { 
      ...fetchOptions, 
      method: 'PATCH', 
      body 
    } as any);
    
    if (validateResponse) {
      const result = schema.safeParse(response);
      if (!result.success) {
        throw new ApiError(
          `Invalid response format: ${result.error.message}`,
          422
        );
      }
      return result.data;
    }
    
    return response;
  },
  
  delete: async <T extends z.ZodTypeAny>(
    url: string,
    schema: T,
    options?: ApiClientConfig
  ): Promise<z.infer<T>> => {
    const { validateResponse = true, ...fetchOptions } = options || {};
    const response = await apiClient(url, { ...fetchOptions, method: 'DELETE' });
    
    if (validateResponse) {
      const result = schema.safeParse(response);
      if (!result.success) {
        throw new ApiError(
          `Invalid response format: ${result.error.message}`,
          422
        );
      }
      return result.data;
    }
    
    return response;
  },
};

// Helper functions for building URLs with query parameters
export const buildUrl = (
  path: string, 
  params?: Record<string, any>
): string => {
  if (!params || Object.keys(params).length === 0) {
    return path;
  }
  
  const searchParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      if (Array.isArray(value)) {
        value.forEach(item => searchParams.append(key, String(item)));
      } else {
        searchParams.append(key, String(value));
      }
    }
  });
  
  const queryString = searchParams.toString();
  return queryString ? `${path}?${queryString}` : path;
};

// Helper for standard pagination and sorting parameters
export const buildQueryParams = (
  pagination?: Partial<PaginationParams>,
  sorting?: Partial<SortingParams>,
  filters?: Record<string, any>
): Record<string, any> => {
  return {
    ...pagination,
    ...sorting,
    ...filters,
  };
};

// Legacy compatibility exports
export const apiRequest = apiClient;
export { apiClient as fetch };

// Default export for backward compatibility
export default apiClient;