/**
 * Standardized service API hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { api, buildUrl, buildQueryParams } from '../client';
import { 
  ServicesResponseSchema,
  ServiceSchema,
  UsersResponseSchema,
  InboundsResponseSchema,
  SuccessResponseSchema,
  ServiceCreate,
  ServiceModify,
  PaginationParams,
  SortingParams,
  ServiceQueryParams,
} from '../schemas';
import { queryKeys, getRelatedQueryKeys } from '../query-keys';

// Services list query
export const useServicesQuery = (params: {
  pagination?: Partial<PaginationParams>;
  sorting?: Partial<SortingParams>;
  filters?: Partial<Omit<ServiceQueryParams, 'page' | 'size'>>;
} = {}) => {
  const queryParams = buildQueryParams(params.pagination, params.sorting, params.filters);
  
  return useQuery({
    queryKey: queryKeys.servicesList(params),
    queryFn: () => api.get(buildUrl('services', queryParams), ServicesResponseSchema),
    placeholderData: { items: [], pages: 0, page: 1, size: 10, total: 0 },
  });
};

// Single service query
export const useServiceQuery = (serviceId: number, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.servicesService(serviceId),
    queryFn: () => api.get(`services/${serviceId}`, ServiceSchema),
    enabled: enabled && !!serviceId,
  });
};

// Service users query
export const useServiceUsersQuery = (serviceId: number, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.servicesServiceUsers(serviceId),
    queryFn: () => api.get(`services/${serviceId}/users`, UsersResponseSchema),
    enabled: enabled && !!serviceId,
    placeholderData: { items: [], pages: 0, page: 1, size: 10, total: 0 },
  });
};

// Service inbounds query
export const useServiceInboundsQuery = (serviceId: number, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.servicesServiceInbounds(serviceId),
    queryFn: () => api.get(`services/${serviceId}/inbounds`, InboundsResponseSchema),
    enabled: enabled && !!serviceId,
    placeholderData: { items: [], pages: 0, page: 1, size: 10, total: 0 },
  });
};

// Create service mutation
export const useCreateServiceMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (service: ServiceCreate) => api.post('services', ServiceSchema, service),
    onSuccess: (newService) => {
      // Invalidate services list
      queryClient.invalidateQueries({ queryKey: queryKeys.servicesList() });
      
      // Add service to cache
      queryClient.setQueryData(queryKeys.servicesService(newService.id), newService);
      
      toast.success(`Service "${newService.name}" created successfully`);
    },
    onError: (error) => {
      toast.error(`Failed to create service: ${error.message}`);
    },
  });
};

// Update service mutation
export const useUpdateServiceMutation = (serviceId: number) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (modifications: ServiceModify) => 
      api.put(`services/${serviceId}`, ServiceSchema, modifications),
    onSuccess: (updatedService) => {
      // Update all related query data
      getRelatedQueryKeys.service(serviceId).forEach(queryKey => {
        queryClient.invalidateQueries({ queryKey });
      });
      
      // Update service in cache
      queryClient.setQueryData(queryKeys.servicesService(serviceId), updatedService);
      
      toast.success(`Service "${updatedService.name}" updated successfully`);
    },
    onError: (error) => {
      toast.error(`Failed to update service: ${error.message}`);
    },
  });
};

// Delete service mutation
export const useDeleteServiceMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (serviceId: number) => api.delete(`services/${serviceId}`, SuccessResponseSchema),
    onSuccess: (_, serviceId) => {
      // Remove all related query data
      getRelatedQueryKeys.service(serviceId).forEach(queryKey => {
        queryClient.removeQueries({ queryKey });
      });
      
      // Invalidate lists and related data
      queryClient.invalidateQueries({ queryKey: queryKeys.servicesList() });
      queryClient.invalidateQueries({ queryKey: queryKeys.usersList() }); // Users might be affected
      
      toast.success(`Service deleted successfully`);
    },
    onError: (error) => {
      toast.error(`Failed to delete service: ${error.message}`);
    },
  });
};