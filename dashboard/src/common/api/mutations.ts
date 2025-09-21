/**
 * Standardized mutation helpers and types
 */

import { UseMutationOptions, useMutation } from '@tanstack/react-query';
import { z } from 'zod';
import { api, ApiError } from './client';
import { SuccessResponseSchema } from './schemas';

// Standard mutation options with error handling
export interface StandardMutationOptions<TData, TVariables, TError = ApiError> 
  extends Omit<UseMutationOptions<TData, TError, TVariables>, 'mutationFn'> {}

// Helper for creating typed mutations with standard error handling
export const createMutation = <TData extends z.ZodTypeAny, TVariables>(
  mutationFn: (variables: TVariables) => Promise<z.infer<TData>>,
  options?: StandardMutationOptions<z.infer<TData>, TVariables>
) => {
  return useMutation({
    mutationFn,
    ...options,
  });
};

// Standard delete mutation
export const createDeleteMutation = (
  endpoint: string,
  options?: StandardMutationOptions<{ success: boolean }, string | number>
) => {
  return useMutation({
    mutationFn: (id: string | number) => 
      api.delete(`${endpoint}/${id}`, SuccessResponseSchema),
    ...options,
  });
};

// Standard update mutation
export const createUpdateMutation = <TData extends z.ZodTypeAny, TVariables>(
  endpoint: string,
  schema: TData,
  options?: StandardMutationOptions<z.infer<TData>, { id: string | number; data: TVariables }>
) => {
  return useMutation({
    mutationFn: ({ id, data }: { id: string | number; data: TVariables }) => 
      api.put(`${endpoint}/${id}`, schema, data),
    ...options,
  });
};

// Standard create mutation
export const createCreateMutation = <TData extends z.ZodTypeAny, TVariables>(
  endpoint: string,
  schema: TData,
  options?: StandardMutationOptions<z.infer<TData>, TVariables>
) => {
  return useMutation({
    mutationFn: (data: TVariables) => 
      api.post(endpoint, schema, data),
    ...options,
  });
};

// Utility types for common mutation patterns
export type MutationStatus = 'idle' | 'pending' | 'error' | 'success';

export interface MutationState<TData, TError = ApiError> {
  data: TData | undefined;
  error: TError | null;
  isError: boolean;
  isIdle: boolean;
  isPending: boolean;
  isSuccess: boolean;
  status: MutationStatus;
}

// Common error messages for mutations
export const MUTATION_ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  UNAUTHORIZED: 'You are not authorized to perform this action.',
  FORBIDDEN: 'Access denied. You don\'t have permission for this action.',
  NOT_FOUND: 'The requested resource was not found.',
  CONFLICT: 'This action conflicts with existing data.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  SERVER_ERROR: 'Server error. Please try again later.',
  UNKNOWN_ERROR: 'An unexpected error occurred.',
} as const;

// Helper to get user-friendly error message
export const getErrorMessage = (error: ApiError | Error): string => {
  if (ApiError.isApiError(error)) {
    switch (error.status) {
      case 401:
        return MUTATION_ERROR_MESSAGES.UNAUTHORIZED;
      case 403:
        return MUTATION_ERROR_MESSAGES.FORBIDDEN;
      case 404:
        return MUTATION_ERROR_MESSAGES.NOT_FOUND;
      case 409:
        return MUTATION_ERROR_MESSAGES.CONFLICT;
      case 422:
        return MUTATION_ERROR_MESSAGES.VALIDATION_ERROR;
      case 500:
      case 502:
      case 503:
      case 504:
        return MUTATION_ERROR_MESSAGES.SERVER_ERROR;
      default:
        return error.message || MUTATION_ERROR_MESSAGES.UNKNOWN_ERROR;
    }
  }
  
  if (error.name === 'NetworkError' || error.message.includes('fetch')) {
    return MUTATION_ERROR_MESSAGES.NETWORK_ERROR;
  }
  
  return error.message || MUTATION_ERROR_MESSAGES.UNKNOWN_ERROR;
};