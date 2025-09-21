/**
 * Standardized inbound API hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { api, buildUrl, buildQueryParams } from '../client';
import { 
  InboundsResponseSchema,
  InboundSchema,
  InboundHostsResponseSchema,
  InboundHostSchema,
  SuccessResponseSchema,
  InboundHostCreate,
  InboundHostModify,
  PaginationParams,
  SortingParams,
  InboundQueryParams,
} from '../schemas';
import { queryKeys, getRelatedQueryKeys } from '../query-keys';

// Inbounds list query
export const useInboundsQuery = (params: {
  pagination?: Partial<PaginationParams>;
  sorting?: Partial<SortingParams>;
  filters?: Partial<Omit<InboundQueryParams, 'page' | 'size'>>;
} = {}) => {
  const queryParams = buildQueryParams(params.pagination, params.sorting, params.filters);
  
  return useQuery({
    queryKey: queryKeys.inboundsList(params),
    queryFn: () => api.get(buildUrl('inbounds', queryParams), InboundsResponseSchema),
    placeholderData: { items: [], pages: 0, page: 1, size: 10, total: 0 },
  });
};

// Single inbound query
export const useInboundQuery = (inboundId: number, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.inboundsInbound(inboundId),
    queryFn: () => api.get(`inbounds/${inboundId}`, InboundSchema),
    enabled: enabled && !!inboundId,
  });
};

// Inbound hosts query
export const useInboundHostsQuery = (inboundId: number, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.inboundsInboundHosts(inboundId),
    queryFn: () => api.get(`inbounds/${inboundId}/hosts`, InboundHostsResponseSchema),
    enabled: enabled && !!inboundId,
    placeholderData: { items: [], pages: 0, page: 1, size: 10, total: 0 },
  });
};

// All hosts query
export const useHostsQuery = (params: {
  pagination?: Partial<PaginationParams>;
  sorting?: Partial<SortingParams>;
  filters?: Record<string, any>;
} = {}) => {
  const queryParams = buildQueryParams(params.pagination, params.sorting, params.filters);
  
  return useQuery({
    queryKey: queryKeys.inboundsHosts(params),
    queryFn: () => api.get(buildUrl('inbounds/hosts', queryParams), InboundHostsResponseSchema),
    placeholderData: { items: [], pages: 0, page: 1, size: 10, total: 0 },
  });
};

// Single host query
export const useHostQuery = (hostId: number, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.inboundsHost(hostId),
    queryFn: () => api.get(`inbounds/hosts/${hostId}`, InboundHostSchema),
    enabled: enabled && !!hostId,
  });
};

// Create unbound host mutation (host without inbound)
export const useCreateUnboundHostMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (host: InboundHostCreate) => 
      api.post('inbounds/hosts', InboundHostSchema, host),
    onSuccess: (newHost) => {
      // Invalidate hosts list
      queryClient.invalidateQueries({ queryKey: queryKeys.inboundsHosts() });
      
      // Add host to cache
      queryClient.setQueryData(queryKeys.inboundsHost(newHost.id), newHost);
      
      toast.success(`Host "${newHost.remark}" created successfully`);
    },
    onError: (error) => {
      toast.error(`Failed to create host: ${error.message}`);
    },
  });
};

// Create host for inbound mutation
export const useCreateHostMutation = (inboundId: number) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (host: InboundHostCreate) => 
      api.post(`inbounds/${inboundId}/hosts`, InboundHostSchema, host),
    onSuccess: (newHost) => {
      // Invalidate inbound hosts and all hosts
      queryClient.invalidateQueries({ queryKey: queryKeys.inboundsInboundHosts(inboundId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.inboundsHosts() });
      
      // Add host to cache
      queryClient.setQueryData(queryKeys.inboundsHost(newHost.id), newHost);
      
      toast.success(`Host "${newHost.remark}" created successfully`);
    },
    onError: (error) => {
      toast.error(`Failed to create host: ${error.message}`);
    },
  });
};

// Update host mutation
export const useUpdateHostMutation = (hostId: number) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (modifications: InboundHostModify) => 
      api.put(`inbounds/hosts/${hostId}`, InboundHostSchema, modifications),
    onSuccess: (updatedHost) => {
      // Update all related query data
      getRelatedQueryKeys.host(hostId).forEach(queryKey => {
        queryClient.invalidateQueries({ queryKey });
      });
      
      // Update host in cache
      queryClient.setQueryData(queryKeys.inboundsHost(hostId), updatedHost);
      
      // Also invalidate inbound hosts if this host belongs to an inbound
      if (updatedHost.inbound_id) {
        queryClient.invalidateQueries({ 
          queryKey: queryKeys.inboundsInboundHosts(updatedHost.inbound_id) 
        });
      }
      
      toast.success(`Host "${updatedHost.remark}" updated successfully`);
    },
    onError: (error) => {
      toast.error(`Failed to update host: ${error.message}`);
    },
  });
};

// Delete host mutation
export const useDeleteHostMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (hostId: number) => api.delete(`inbounds/hosts/${hostId}`, SuccessResponseSchema),
    onSuccess: (_, hostId) => {
      // Remove all related query data
      getRelatedQueryKeys.host(hostId).forEach(queryKey => {
        queryClient.removeQueries({ queryKey });
      });
      
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: queryKeys.inboundsHosts() });
      // Also invalidate any inbound hosts lists that might contain this host
      queryClient.invalidateQueries({ 
        queryKey: [...queryKeys.inbounds, 'detail'],
        type: 'active',
        predicate: (query) => {
          return query.queryKey.some(key => 
            typeof key === 'string' && key.includes('hosts')
          );
        }
      });
      
      toast.success(`Host deleted successfully`);
    },
    onError: (error) => {
      toast.error(`Failed to delete host: ${error.message}`);
    },
  });
};