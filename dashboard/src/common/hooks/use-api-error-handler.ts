import * as React from 'react';
import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: any;
}

export interface UseApiErrorHandlerOptions {
  showToast?: boolean;
  defaultErrorMessage?: string;
  onError?: (error: ApiError) => void;
}

export const useApiErrorHandler = (options: UseApiErrorHandlerOptions = {}) => {
  const { t } = useTranslation();
  const {
    showToast = true,
    defaultErrorMessage = 'An unexpected error occurred',
    onError
  } = options;

  const handleError = React.useCallback((error: any, context?: string) => {
    // Parse error object
    const apiError: ApiError = {
      message: error?.message || error?.response?._data?.detail || defaultErrorMessage,
      status: error?.response?.status || error?.status,
      code: error?.code || error?.response?._data?.code,
      details: error?.response?._data || error?.details
    };

    // Add context to error message if provided
    const errorMessage = context 
      ? `${context}: ${apiError.message}`
      : apiError.message;

    // Show toast notification if enabled
    if (showToast) {
      const title = apiError.status 
        ? `${t('Error')} ${apiError.status}`
        : t('Error');
      
      toast.error(title, {
        description: errorMessage,
        duration: 5000,
        action: apiError.code ? {
          label: t('Code'),
          onClick: () => toast.info(`Error Code: ${apiError.code}`)
        } : undefined
      });
    }

    // Call custom error handler if provided
    if (onError) {
      onError(apiError);
    }

    // Log error for debugging
    console.error('API Error:', {
      context,
      error: apiError,
      originalError: error
    });

    return apiError;
  }, [showToast, defaultErrorMessage, onError, t]);

  const handleNetworkError = React.useCallback((_error: any, context?: string) => {
    const networkError = {
      message: t('error.network_connection'),
      status: 0,
      code: 'NETWORK_ERROR'
    };

    return handleError(networkError, context);
  }, [handleError, t]);

  const handleTimeoutError = React.useCallback((_error: any, context?: string) => {
    const timeoutError = {
      message: t('error.request_timeout'),
      status: 408,
      code: 'TIMEOUT_ERROR'
    };

    return handleError(timeoutError, context);
  }, [handleError, t]);

  return {
    handleError,
    handleNetworkError,
    handleTimeoutError
  };
};

// Enhanced fetch wrapper with error handling
export const useEnhancedFetch = () => {
  const { handleError, handleNetworkError, handleTimeoutError } = useApiErrorHandler();

  const enhancedFetch = React.useCallback(async (url: string, options: any = {}, context?: string) => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      return response;
    } catch (error: any) {
      if (error.name === 'AbortError') {
        throw handleTimeoutError(error, context);
      } else if (!navigator.onLine) {
        throw handleNetworkError(error, context);
      } else {
        throw handleError(error, context);
      }
    }
  }, [handleError, handleNetworkError, handleTimeoutError]);

  return { enhancedFetch };
};