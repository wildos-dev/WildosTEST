import { useQuery, UseQueryOptions, onlineManager } from '@tanstack/react-query';
import * as React from 'react';
import { useApiErrorHandler } from './use-api-error-handler';

export interface OptimizedQueryConfig {
  enabledWhenOnline?: boolean;
  adaptivePolling?: boolean;
  baseRefetchInterval?: number;
  maxRefetchInterval?: number;
  errorRetryCount?: number;
  staleTime?: number;
  cacheTime?: number;
}

export const useOptimizedQuery = <TData = unknown, TError = unknown>(
  queryKey: any[],
  queryFn: () => Promise<TData>,
  options: Partial<UseQueryOptions<TData, TError>> & OptimizedQueryConfig = {}
) => {
  const { handleError } = useApiErrorHandler({ showToast: false });

  const {
    enabledWhenOnline = true,
    adaptivePolling = true,
    baseRefetchInterval = 30000, // 30 seconds default
    maxRefetchInterval = 300000, // 5 minutes max
    errorRetryCount = 2,
    staleTime = 30000, // 30 seconds
    gcTime = 300000, // 5 minutes (renamed from cacheTime)
    ...queryOptions
  } = options;

  // Adaptive polling with proper reactivity
  const [currentInterval, setCurrentInterval] = React.useState<number | false>(baseRefetchInterval);
  
  React.useEffect(() => {
    if (!adaptivePolling) {
      // Handle different types of refetchInterval
      const interval = queryOptions.refetchInterval;
      if (typeof interval === 'number') {
        setCurrentInterval(interval);
      } else if (interval === false) {
        setCurrentInterval(false);
      } else {
        // If it's a function or undefined, fall back to baseRefetchInterval
        setCurrentInterval(baseRefetchInterval);
      }
      return;
    }

    const updateInterval = () => {
      // Guard against SSR and ensure browser environment
      if (typeof window === 'undefined' || typeof document === 'undefined') {
        setCurrentInterval(baseRefetchInterval);
        return;
      }
      
      if (!document.hasFocus()) {
        setCurrentInterval(Math.min(baseRefetchInterval * 2, maxRefetchInterval));
      } else if (!onlineManager.isOnline()) {
        setCurrentInterval(false as false);
      } else {
        setCurrentInterval(baseRefetchInterval);
      }
    };

    updateInterval();
    
    const handleFocus = () => updateInterval();
    const handleBlur = () => updateInterval();
    
    // Guard against SSR - only add listeners in browser environment
    if (typeof window !== 'undefined') {
      window.addEventListener('focus', handleFocus);
      window.addEventListener('blur', handleBlur);
    }
    
    const unsubscribe = onlineManager.subscribe(() => updateInterval());
    
    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener('focus', handleFocus);
        window.removeEventListener('blur', handleBlur);
      }
      unsubscribe();
    };
  }, [adaptivePolling, baseRefetchInterval, maxRefetchInterval, queryOptions.refetchInterval]);

  // Enhanced error handling
  const enhancedQueryFn = React.useCallback(async () => {
    try {
      return await queryFn();
    } catch (error: any) {
      // Log error context but don't show toast (will be handled by component)
      const context = `Query [${queryKey.join(', ')}]`;
      handleError(error, context);
      throw error;
    }
  }, [queryFn, queryKey, handleError]);

  return useQuery({
    queryKey,
    queryFn: enhancedQueryFn,
    enabled: enabledWhenOnline ? onlineManager.isOnline() : queryOptions.enabled,
    refetchInterval: currentInterval,
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
    retry: errorRetryCount,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    staleTime,
    gcTime,
    ...queryOptions,
  });
};

// Hook for widget-specific queries with built-in error handling
export const useWidgetQuery = <TData = unknown>(
  queryKey: any[],
  queryFn: () => Promise<TData>,
  options: OptimizedQueryConfig & {
    widgetName?: string;
    showErrorToast?: boolean;
  } = {}
) => {
  const { 
    widgetName = 'Widget',
    showErrorToast = false,
    ...queryConfig 
  } = options;

  const { handleError } = useApiErrorHandler({ 
    showToast: showErrorToast,
    defaultErrorMessage: `Failed to load ${widgetName} data`
  });

  const result = useOptimizedQuery(queryKey, queryFn, queryConfig);
  const lastErrorRef = React.useRef<any>(null);

  // Handle query errors specifically for widgets (prevent spam)
  React.useEffect(() => {
    if (result.error && showErrorToast && result.error !== lastErrorRef.current) {
      lastErrorRef.current = result.error;
      handleError(result.error, `${widgetName} data fetch`);
    } else if (!result.error) {
      lastErrorRef.current = null;
    }
  }, [result.error, showErrorToast, handleError, widgetName]);

  return {
    ...result,
    // Add widget-specific helpers
    isReady: !result.isLoading && !result.error,
    hasData: !result.isLoading && !result.error && result.data !== undefined,
    isEmpty: !result.isLoading && !result.error && (
      result.data === undefined || 
      result.data === null || 
      (Array.isArray(result.data) && result.data.length === 0)
    )
  };
};

// Optimized intervals for different types of data
export const QUERY_INTERVALS = {
  REAL_TIME: 5000,    // 5 seconds - for logs, live metrics
  FREQUENT: 15000,    // 15 seconds - for status updates
  NORMAL: 30000,      // 30 seconds - for general data
  SLOW: 60000,        // 1 minute - for less critical data
  VERY_SLOW: 300000,  // 5 minutes - for configuration data
} as const;

// Helper to determine appropriate interval based on data type
export const getOptimalInterval = (dataType: 'logs' | 'metrics' | 'status' | 'general' | 'config'): number => {
  switch (dataType) {
    case 'logs':
      return QUERY_INTERVALS.REAL_TIME;
    case 'metrics':
      return QUERY_INTERVALS.FREQUENT;
    case 'status':
      return QUERY_INTERVALS.FREQUENT;
    case 'general':
      return QUERY_INTERVALS.NORMAL;
    case 'config':
      return QUERY_INTERVALS.VERY_SLOW;
    default:
      return QUERY_INTERVALS.NORMAL;
  }
};