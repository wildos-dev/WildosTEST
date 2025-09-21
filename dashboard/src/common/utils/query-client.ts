import { QueryClient } from '@tanstack/react-query';
import { apiClient, ApiError } from '../api/client';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Use the standardized API client as default fetcher
      queryFn: ({ queryKey }) => {
        const [url, ...params] = queryKey as [string, ...any[]];
        
        // Handle simple query keys: [url, params]
        if (params.length === 1 && params[0] && typeof params[0] === 'object' && !Array.isArray(params[0])) {
          return apiClient(url, { query: params[0] });
        }
        
        // Handle entity-table query keys: [entityName, pagination, primaryFilter, sortInfo, filtersInfo]
        if (params.length >= 4) {
          const [pagination, primaryFilter, sortInfo, filtersInfo] = params;
          const queryParams = {
            ...(pagination || {}),
            ...(filtersInfo?.filters || {}),
            ...(primaryFilter && { search: primaryFilter }),
            ...(sortInfo?.desc !== undefined && { descending: sortInfo.desc }),
            ...(sortInfo?.sortBy && { order_by: sortInfo.sortBy }),
          };
          return apiClient(url, { query: queryParams });
        }
        
        // Fallback for simple URLs with no params
        return apiClient(url);
      },
      // Retry failed requests up to 3 times with exponential backoff
      retry: (failureCount, error: any) => {
        // Use standardized ApiError if available
        if (ApiError.isApiError(error)) {
          const status = error.status;
          // Don't retry on client errors (4xx) except 408 Request Timeout
          if (status >= 400 && status < 500 && status !== 408) {
            return false;
          }
        }
        
        // Fallback to previous logic for compatibility
        const status = error?.response?.status || error?.status || 0;
        if (status >= 400 && status < 500 && status !== 408) {
          return false;
        }
        
        // Retry up to 3 times for server errors (5xx) and network errors
        return failureCount < 3;
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      // Data is fresh for 5 minutes, then stale but usable
      staleTime: 5 * 60 * 1000, // 5 minutes
      // Keep data in cache for 10 minutes after component unmount
      gcTime: 10 * 60 * 1000, // 10 minutes (was cacheTime in v4)
      // Refetch when window regains focus only if data is stale
      refetchOnWindowFocus: (query) => query.isStale(),
      // Enable background refetch while data is stale
      refetchOnMount: true,
      refetchOnReconnect: true,
    },
    mutations: {
      // Retry mutations once on network errors
      retry: (failureCount, error: any) => {
        // Use standardized ApiError if available
        if (ApiError.isApiError(error)) {
          const status = error.status;
          // Don't retry client errors (4xx)
          if (status >= 400 && status < 500) {
            return false;
          }
        }
        
        // Fallback to previous logic for compatibility
        const status = error?.response?.status || error?.status || 0;
        if (status >= 400 && status < 500) {
          return false;
        }
        
        return failureCount < 1; // Retry once for server/network errors
      },
      retryDelay: 1000,
    },
  },
});
