/**
 * Standardized node API hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { z } from 'zod';
import { api, buildUrl, buildQueryParams } from '../client';
import { 
  NodesResponseSchema,
  NodeSchema,
  NodeStatsSchema,
  NodeSettingsSchema,
  NodeUsageResponseSchema,
  AllBackendsStatsResponseSchema,
  HostSystemMetricsSchema,
  PeakEventSchema,
  NodeCreate,
  NodeModify,
  NodeSettings,
  PaginationParams,
  SortingParams,
  NodeQueryParams,
} from '../schemas';
import { queryKeys, getRelatedQueryKeys } from '../query-keys';

// Nodes list query
export const useNodesQuery = (params: {
  pagination?: Partial<PaginationParams>;
  sorting?: Partial<SortingParams>;
  filters?: Partial<Omit<NodeQueryParams, 'page' | 'size'>>;
} = {}) => {
  const queryParams = buildQueryParams(params.pagination, params.sorting, params.filters);
  
  return useQuery({
    queryKey: queryKeys.nodesList(params),
    queryFn: () => api.get(buildUrl('nodes', queryParams), NodesResponseSchema),
    placeholderData: { items: [], pages: 0, page: 1, size: 10, total: 0 },
  });
};

// Single node query
export const useNodeQuery = (nodeId: number, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.nodesNode(nodeId),
    queryFn: () => api.get(`nodes/${nodeId}`, NodeSchema),
    enabled: enabled && !!nodeId,
  });
};

// Global node settings query
export const useNodeSettingsQuery = (enabled = true) => {
  return useQuery({
    queryKey: ['nodes', 'settings'],
    queryFn: () => api.get('nodes/settings', NodeSettingsSchema),
    enabled,
  });
};

// Node usage query
export const useNodeUsageQuery = (
  nodeId: number,
  params: { start_date?: string; end_date?: string } = {},
  enabled = true
) => {
  return useQuery({
    queryKey: queryKeys.nodesNodeUsage(nodeId, params),
    queryFn: () => api.get(buildUrl(`nodes/${nodeId}/usage`, params), NodeUsageResponseSchema),
    enabled: enabled && !!nodeId,
  });
};

// All nodes usage query
export const useNodesUsageQuery = (
  params: { start_date?: string; end_date?: string } = {}
) => {
  return useQuery({
    queryKey: queryKeys.nodesUsage(params),
    queryFn: () => api.get(buildUrl('nodes/usage', params), NodeUsageResponseSchema),
  });
};

// Node stats query
export const useNodeStatsQuery = () => {
  return useQuery({
    queryKey: queryKeys.nodesStats(),
    queryFn: () => api.get('system/stats/nodes', NodeStatsSchema),
  });
};

// Backend stats query
export const useBackendStatsQuery = (nodeId: number, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.nodesBackendStats(nodeId),
    queryFn: () => api.get(`nodes/${nodeId}/backends/stats`, AllBackendsStatsResponseSchema),
    enabled: enabled && !!nodeId,
    refetchInterval: 30000, // Refresh every 30 seconds
  });
};

// All backends stats query
export const useAllBackendsStatsQuery = () => {
  return useQuery({
    queryKey: queryKeys.nodesAllBackendStats(),
    queryFn: () => api.get('nodes/aggregate-metrics', NodeUsageResponseSchema),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
};

// Host system metrics query
export const useHostSystemMetricsQuery = (nodeId: number, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.nodesHostSystem(nodeId),
    queryFn: () => api.get(`nodes/${nodeId}/host/metrics`, HostSystemMetricsSchema),
    enabled: enabled && !!nodeId,
    refetchInterval: 10000, // Refresh every 10 seconds
  });
};

// Peak events query
export const usePeakEventsQuery = (nodeId: number, enabled = true) => {
  return useQuery({
    queryKey: queryKeys.nodesPeakEvents(nodeId),
    queryFn: () => api.get(`nodes/${nodeId}/peak/events`, z.array(PeakEventSchema)),
    enabled: enabled && !!nodeId,
    placeholderData: [],
  });
};

// Aggregate metrics query
export const useAggregateMetricsQuery = () => {
  return useQuery({
    queryKey: queryKeys.nodesAggregateMetrics(),
    queryFn: () => api.get('nodes/aggregate-metrics', NodeUsageResponseSchema),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
};

// Create node mutation
export const useCreateNodeMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (node: NodeCreate) => api.post('nodes', NodeSchema, node),
    onSuccess: (newNode) => {
      // Invalidate nodes list and stats
      queryClient.invalidateQueries({ queryKey: queryKeys.nodesList() });
      queryClient.invalidateQueries({ queryKey: queryKeys.nodesStats() });
      queryClient.invalidateQueries({ queryKey: queryKeys.nodesAllBackendStats() });
      queryClient.invalidateQueries({ queryKey: queryKeys.nodesAggregateMetrics() });
      
      // Add node to cache
      queryClient.setQueryData(queryKeys.nodesNode(newNode.id), newNode);
      
      toast.success(`Node "${newNode.name}" created successfully`);
    },
    onError: (error) => {
      toast.error(`Failed to create node: ${error.message}`);
    },
  });
};

// Update node mutation
export const useUpdateNodeMutation = (nodeId: number) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (modifications: NodeModify) => 
      api.put(`nodes/${nodeId}`, NodeSchema, modifications),
    onSuccess: (updatedNode) => {
      // Update all related query data
      getRelatedQueryKeys.node(nodeId).forEach(queryKey => {
        queryClient.invalidateQueries({ queryKey });
      });
      
      // Update node in cache
      queryClient.setQueryData(queryKeys.nodesNode(nodeId), updatedNode);
      
      toast.success(`Node "${updatedNode.name}" updated successfully`);
    },
    onError: (error) => {
      toast.error(`Failed to update node: ${error.message}`);
    },
  });
};

// Delete node mutation
export const useDeleteNodeMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (nodeId: number) => api.delete(`nodes/${nodeId}`, z.object({}), { validateResponse: false }),
    onSuccess: (_, nodeId) => {
      // Remove all related query data
      getRelatedQueryKeys.node(nodeId).forEach(queryKey => {
        queryClient.removeQueries({ queryKey });
      });
      
      // Invalidate lists
      queryClient.invalidateQueries({ queryKey: queryKeys.nodesList() });
      queryClient.invalidateQueries({ queryKey: queryKeys.nodesStats() });
      queryClient.invalidateQueries({ queryKey: queryKeys.nodesAllBackendStats() });
      queryClient.invalidateQueries({ queryKey: queryKeys.nodesAggregateMetrics() });
      
      toast.success(`Node deleted successfully`);
    },
    onError: (error) => {
      toast.error(`Failed to delete node: ${error.message}`);
    },
  });
};

// Update global node settings mutation
export const useUpdateNodeSettingsMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (settings: NodeSettings) => 
      api.put('nodes/settings', NodeSettingsSchema, settings),
    onSuccess: (updatedSettings) => {
      // Update global node settings in cache
      queryClient.setQueryData(['nodes', 'settings'], updatedSettings);
      queryClient.invalidateQueries({ queryKey: ['nodes'] });
      
      toast.success('Node settings updated successfully');
    },
    onError: (error) => {
      toast.error(`Failed to update node settings: ${error.message}`);
    },
  });
};

// Restart container mutation
export const useRestartContainerMutation = (nodeId: number) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => 
      api.post(`nodes/${nodeId}/container/restart`, z.object({ success: z.boolean(), message: z.string() })),
    onSuccess: (result) => {
      // Invalidate all node-related data
      queryClient.invalidateQueries({ queryKey: queryKeys.nodesBackendStats(nodeId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.nodesNode(nodeId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.nodesAllBackendStats() });
      queryClient.invalidateQueries({ queryKey: queryKeys.nodesHostSystem(nodeId) });
      
      toast.success(result.message || 'Container restarted successfully');
    },
    onError: (error) => {
      toast.error(`Failed to restart container: ${error.message}`);
    },
  });
};