/**
 * Standardized admin API hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { z } from 'zod';
import { api, buildUrl, buildQueryParams } from '../client';
import { 
  AdminsResponseSchema,
  AdminSchema,
  AdminStatsSchema,
  AdminTokenSchema,
  SuccessResponseSchema,
  AdminCreate,
  AdminModify,
  PaginationParams,
  SortingParams,
  AdminQueryParams,
} from '../schemas';
import { queryKeys, getRelatedQueryKeys } from '../query-keys';

// Admins list query
export const useAdminsQuery = (params: {
  pagination?: Partial<PaginationParams>;
  sorting?: Partial<SortingParams>;
  filters?: Partial<Omit<AdminQueryParams, 'page' | 'size'>>;
} = {}) => {
  const queryParams = buildQueryParams(params.pagination, params.sorting, params.filters);
  
  return useQuery({
    queryKey: queryKeys.adminsList(params),
    queryFn: () => api.get(buildUrl('admins', queryParams), AdminsResponseSchema),
    placeholderData: { items: [], pages: 0, page: 1, size: 10, total: 0 },
  });
};

// Single admin query
export const useAdminQuery = (username: string, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.adminsAdmin(username),
    queryFn: () => api.get(`admins/${username}`, AdminSchema),
    enabled: enabled && !!username,
  });
};

// Current admin token query
export const useCurrentAdminTokenQuery = (enabled = true) => {
  return useQuery({
    queryKey: ['admins', 'current', 'token'],
    queryFn: () => api.get('admins/current/token', z.object({ token: z.string() })),
    enabled,
  });
};

// Admin stats query
export const useAdminStatsQuery = () => {
  return useQuery({
    queryKey: queryKeys.adminsStats(),
    queryFn: () => api.get('system/stats/admins', AdminStatsSchema),
  });
};

// Create admin mutation
export const useCreateAdminMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (admin: AdminCreate) => api.post('admins', AdminSchema, admin),
    onSuccess: (newAdmin) => {
      // Invalidate admins list and stats
      queryClient.invalidateQueries({ queryKey: queryKeys.adminsList() });
      queryClient.invalidateQueries({ queryKey: queryKeys.adminsStats() });
      
      // Add admin to cache
      queryClient.setQueryData(queryKeys.adminsAdmin(newAdmin.username), newAdmin);
      
      toast.success(`Admin "${newAdmin.username}" created successfully`);
    },
    onError: (error) => {
      toast.error(`Failed to create admin: ${error.message}`);
    },
  });
};

// Update admin mutation
export const useUpdateAdminMutation = (username: string) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (modifications: AdminModify) => 
      api.put(`admins/${username}`, AdminSchema, modifications),
    onSuccess: (updatedAdmin) => {
      // Update all related query data
      getRelatedQueryKeys.admin(username).forEach(queryKey => {
        queryClient.invalidateQueries({ queryKey });
      });
      
      // Update admin in cache
      queryClient.setQueryData(queryKeys.adminsAdmin(username), updatedAdmin);
      
      toast.success(`Admin "${username}" updated successfully`);
    },
    onError: (error) => {
      toast.error(`Failed to update admin: ${error.message}`);
    },
  });
};

// Delete admin mutation
export const useDeleteAdminMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (username: string) => api.delete(`admins/${username}`, z.object({}), { validateResponse: false }),
    onSuccess: (_, username) => {
      // Remove all related query data
      getRelatedQueryKeys.admin(username).forEach(queryKey => {
        queryClient.removeQueries({ queryKey });
      });
      
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: queryKeys.adminsList() });
      queryClient.invalidateQueries({ queryKey: queryKeys.adminsStats() });
      
      toast.success(`Admin "${username}" deleted successfully`);
    },
    onError: (error) => {
      toast.error(`Failed to delete admin: ${error.message}`);
    },
  });
};

// Enable admin users mutation
export const useEnableAdminUsersMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (username: string) => api.post(`admins/${username}/enable-users`, SuccessResponseSchema),
    onSuccess: (_, username) => {
      // Invalidate admin and user data
      getRelatedQueryKeys.admin(username).forEach(queryKey => {
        queryClient.invalidateQueries({ queryKey });
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.usersList() });
      
      toast.success(`Users enabled for admin "${username}"`);
    },
    onError: (error) => {
      toast.error(`Failed to enable users: ${error.message}`);
    },
  });
};

// Disable admin users mutation
export const useDisableAdminUsersMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (username: string) => api.post(`admins/${username}/disable-users`, SuccessResponseSchema),
    onSuccess: (_, username) => {
      // Invalidate admin and user data
      getRelatedQueryKeys.admin(username).forEach(queryKey => {
        queryClient.invalidateQueries({ queryKey });
      });
      queryClient.invalidateQueries({ queryKey: queryKeys.usersList() });
      
      toast.success(`Users disabled for admin "${username}"`);
    },
    onError: (error) => {
      toast.error(`Failed to disable users: ${error.message}`);
    },
  });
};

// Admin login mutation
export const useAdminLoginMutation = () => {
  return useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) => {
      // Create FormData for OAuth2PasswordRequestForm
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);
      
      return api.post('admins/token', AdminTokenSchema, formData);
    },
    onSuccess: () => {
      toast.success('Login successful');
    },
    onError: (error) => {
      toast.error(`Login failed: ${error.message}`);
    },
  });
};