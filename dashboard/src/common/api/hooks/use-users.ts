/**
 * Standardized user API hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { z } from 'zod';
import { api, buildUrl, buildQueryParams } from '../client';
import { 
  UsersResponseSchema,
  UserSchema,
  UserStatsSchema,
  ServicesResponseSchema,
  UserUsageSeriesSchema,
  UserCreate,
  UserModify,
  PaginationParams,
  SortingParams,
  UserQueryParams,
} from '../schemas';
import { queryKeys, getRelatedQueryKeys } from '../query-keys';

// Users list query
export const useUsersQuery = (params: {
  pagination?: Partial<PaginationParams>;
  sorting?: Partial<SortingParams>;
  filters?: Partial<Omit<UserQueryParams, 'page' | 'size' | 'order_by' | 'descending'>>;
} = {}) => {
  const queryParams = buildQueryParams(params.pagination, params.sorting, params.filters);
  
  return useQuery({
    queryKey: queryKeys.usersList(params),
    queryFn: () => api.get(buildUrl('users', queryParams), UsersResponseSchema),
    placeholderData: { items: [], pages: 0, page: 1, size: 10, total: 0 },
  });
};

// Single user query
export const useUserQuery = (username: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.usersUser(username),
    queryFn: () => api.get(`users/${username}`, UserSchema),
    enabled: enabled && !!username,
  });
};

// User services query
export const useUserServicesQuery = (username: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.usersUserServices(username),
    queryFn: () => api.get(`users/${username}/services`, ServicesResponseSchema),
    enabled: enabled && !!username,
    placeholderData: { items: [], pages: 0, page: 1, size: 10, total: 0 },
  });
};

// User usage query
export const useUserUsageQuery = (
  username: string,
  params: { start_date?: string; end_date?: string } = {},
  enabled = true
) => {
  return useQuery({
    queryKey: queryKeys.usersUserUsage(username, params),
    queryFn: () => api.get(buildUrl(`users/${username}/usage`, params), UserUsageSeriesSchema),
    enabled: enabled && !!username,
  });
};

// User stats query
export const useUserStatsQuery = () => {
  return useQuery({
    queryKey: queryKeys.usersStats(),
    queryFn: () => api.get('system/stats/users', UserStatsSchema),
  });
};

// Create user mutation
export const useCreateUserMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (user: UserCreate) => api.post('users', UserSchema, user),
    onSuccess: (newUser) => {
      // Invalidate users list and stats
      queryClient.invalidateQueries({ queryKey: queryKeys.usersList() });
      queryClient.invalidateQueries({ queryKey: queryKeys.usersStats() });
      
      // Add user to cache
      queryClient.setQueryData(queryKeys.usersUser(newUser.username), newUser);
      
      toast.success(`User "${newUser.username}" created successfully`);
    },
    onError: (error) => {
      toast.error(`Failed to create user: ${error.message}`);
    },
  });
};

// Update user mutation
export const useUpdateUserMutation = (username: string) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (modifications: UserModify) => 
      api.put(`users/${username}`, UserSchema, modifications),
    onSuccess: (updatedUser) => {
      // Update all related query data
      getRelatedQueryKeys.user(username).forEach(queryKey => {
        queryClient.invalidateQueries({ queryKey });
      });
      
      // Update user in cache
      queryClient.setQueryData(queryKeys.usersUser(username), updatedUser);
      
      toast.success(`User "${username}" updated successfully`);
    },
    onError: (error) => {
      toast.error(`Failed to update user: ${error.message}`);
    },
  });
};

// Delete user mutation
export const useDeleteUserMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (username: string) => api.delete(`users/${username}`, z.object({}), { validateResponse: false }),
    onSuccess: (_, username) => {
      // Remove all related query data
      getRelatedQueryKeys.user(username).forEach(queryKey => {
        queryClient.removeQueries({ queryKey });
      });
      
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: queryKeys.usersList() });
      queryClient.invalidateQueries({ queryKey: queryKeys.usersStats() });
      
      toast.success(`User "${username}" deleted successfully`);
    },
    onError: (error) => {
      toast.error(`Failed to delete user: ${error.message}`);
    },
  });
};

// User status mutations
export const useEnableUserMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (username: string) => api.post(`users/${username}/enable`, UserSchema),
    onSuccess: (updatedUser, username) => {
      getRelatedQueryKeys.user(username).forEach(queryKey => {
        queryClient.invalidateQueries({ queryKey });
      });
      
      queryClient.setQueryData(queryKeys.usersUser(username), updatedUser);
      toast.success(`User "${username}" enabled successfully`);
    },
    onError: (error) => {
      toast.error(`Failed to enable user: ${error.message}`);
    },
  });
};

export const useDisableUserMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (username: string) => api.post(`users/${username}/disable`, UserSchema),
    onSuccess: (updatedUser, username) => {
      getRelatedQueryKeys.user(username).forEach(queryKey => {
        queryClient.invalidateQueries({ queryKey });
      });
      
      queryClient.setQueryData(queryKeys.usersUser(username), updatedUser);
      toast.success(`User "${username}" disabled successfully`);
    },
    onError: (error) => {
      toast.error(`Failed to disable user: ${error.message}`);
    },
  });
};

// Reset user data usage mutation
export const useResetUserDataUsageMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (username: string) => api.post(`users/${username}/reset`, UserSchema),
    onSuccess: (updatedUser, username) => {
      getRelatedQueryKeys.user(username).forEach(queryKey => {
        queryClient.invalidateQueries({ queryKey });
      });
      
      queryClient.setQueryData(queryKeys.usersUser(username), updatedUser);
      toast.success(`Data usage reset for user "${username}"`);
    },
    onError: (error) => {
      toast.error(`Failed to reset data usage: ${error.message}`);
    },
  });
};

// Revoke user subscription mutation
export const useRevokeUserSubscriptionMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (username: string) => api.post(`users/${username}/revoke_sub`, UserSchema),
    onSuccess: (updatedUser, username) => {
      getRelatedQueryKeys.user(username).forEach(queryKey => {
        queryClient.invalidateQueries({ queryKey });
      });
      
      queryClient.setQueryData(queryKeys.usersUser(username), updatedUser);
      toast.success(`Subscription revoked for user "${username}"`);
    },
    onError: (error) => {
      toast.error(`Failed to revoke subscription: ${error.message}`);
    },
  });
};

// Set user owner mutation
export const useSetUserOwnerMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ username, adminUsername }: { username: string; adminUsername: string }) => 
      api.put(`users/${username}/set-owner`, UserSchema, undefined, {
        query: { admin_username: adminUsername }
      }),
    onSuccess: (updatedUser, { username }) => {
      getRelatedQueryKeys.user(username).forEach(queryKey => {
        queryClient.invalidateQueries({ queryKey });
      });
      
      queryClient.setQueryData(queryKeys.usersUser(username), updatedUser);
      toast.success(`Owner updated for user "${username}"`);
    },
    onError: (error) => {
      toast.error(`Failed to set owner: ${error.message}`);
    },
  });
};