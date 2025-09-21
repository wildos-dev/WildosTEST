/**
 * Standardized system API hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { api, buildUrl } from '../client';
import { 
  SubscriptionSettingsSchema,
  TelegramSettingsSchema,
  NodeGrpcPortSchema,
  TrafficUsageSeriesSchema,
  SystemHealthSchema,
  DiskInfoSchema,
  DatabaseHealthSchema,
  MonitoringStatusSchema,
  DatabaseCleanupResultsSchema,
  DatabaseOptimizationResultsSchema,
  VersionInfoSchema,
  ReadinessCheckSchema,
  SubscriptionSettings,
  TelegramSettings,
} from '../schemas';
import { queryKeys } from '../query-keys';

// Subscription settings query
export const useSubscriptionSettingsQuery = () => {
  return useQuery({
    queryKey: queryKeys.systemSubscriptionSettings(),
    queryFn: () => api.get('system/settings/subscription', SubscriptionSettingsSchema),
  });
};

// Telegram settings query
export const useTelegramSettingsQuery = () => {
  return useQuery({
    queryKey: queryKeys.systemTelegramSettings(),
    queryFn: () => api.get('system/settings/telegram', TelegramSettingsSchema),
  });
};

// Node GRPC port query
export const useNodeGrpcPortQuery = () => {
  return useQuery({
    queryKey: queryKeys.systemNodeGrpcPort(),
    queryFn: () => api.get('system/config/node-grpc-port', NodeGrpcPortSchema),
  });
};

// Traffic stats query
export const useTrafficStatsQuery = (
  params: { start_date?: string; end_date?: string } = {}
) => {
  return useQuery({
    queryKey: queryKeys.systemTrafficStats(params),
    queryFn: () => api.get(buildUrl('system/stats/traffic', params), TrafficUsageSeriesSchema),
  });
};

// System health queries
export const useSystemHealthQuery = () => {
  return useQuery({
    queryKey: queryKeys.systemHealth(),
    queryFn: () => api.get('api/system/health', SystemHealthSchema),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
};

export const useDiskInfoQuery = () => {
  return useQuery({
    queryKey: queryKeys.systemDiskInfo(),
    queryFn: () => api.get('api/system/disk-info', DiskInfoSchema),
    refetchInterval: 60000, // Refresh every minute
  });
};

export const useDatabaseHealthQuery = () => {
  return useQuery({
    queryKey: queryKeys.systemDatabaseHealth(),
    queryFn: () => api.get('api/system/database-health', DatabaseHealthSchema),
    refetchInterval: 300000, // Refresh every 5 minutes
  });
};

export const useMonitoringStatusQuery = () => {
  return useQuery({
    queryKey: queryKeys.systemMonitoringStatus(),
    queryFn: () => api.get('api/system/monitoring-status', MonitoringStatusSchema),
    refetchInterval: 60000, // Refresh every minute
  });
};

// Version info query
export const useVersionQuery = () => {
  return useQuery({
    queryKey: queryKeys.systemVersion(),
    queryFn: () => api.get('api/system/version', VersionInfoSchema),
    staleTime: 300000, // Version doesn't change often, cache for 5 minutes
  });
};

// Readiness check query with error handling
export const useReadinessQuery = (enabled = true) => {
  return useQuery({
    queryKey: queryKeys.systemReadiness(),
    queryFn: async () => {
      try {
        return await api.get('api/system/ready', ReadinessCheckSchema);
      } catch (error: any) {
        // Handle 503 errors with readiness details
        if (error.status === 503 && error.response?.detail) {
          // Try to parse the error detail as readiness info
          const result = ReadinessCheckSchema.safeParse(error.response.detail);
          if (result.success) {
            return result.data;
          }
        }
        throw error;
      }
    },
    enabled,
    refetchInterval: 30000, // Check readiness every 30 seconds
    retry: false, // Don't retry failed readiness checks
  });
};

// Update subscription settings mutation
export const useUpdateSubscriptionSettingsMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (settings: SubscriptionSettings) => 
      api.put('system/settings/subscription', SubscriptionSettingsSchema, settings),
    onSuccess: (updatedSettings) => {
      // Update settings in cache
      queryClient.setQueryData(queryKeys.systemSubscriptionSettings(), updatedSettings);
      
      toast.success('Subscription settings updated successfully');
    },
    onError: (error) => {
      toast.error(`Failed to update subscription settings: ${error.message}`);
    },
  });
};

// Update telegram settings mutation
export const useUpdateTelegramSettingsMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (settings: TelegramSettings) => 
      api.put('system/settings/telegram', TelegramSettingsSchema, settings),
    onSuccess: (updatedSettings) => {
      // Update settings in cache
      queryClient.setQueryData(queryKeys.systemTelegramSettings(), updatedSettings);
      
      toast.success('Telegram settings updated successfully');
    },
    onError: (error) => {
      toast.error(`Failed to update Telegram settings: ${error.message}`);
    },
  });
};

// Database cleanup mutation
export const useDatabaseCleanupMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ daysToKeep = 30, dryRun = false }: { daysToKeep?: number; dryRun?: boolean }) => 
      api.post('api/system/database-cleanup', DatabaseCleanupResultsSchema, undefined, {
        query: { days_to_keep: daysToKeep, dry_run: dryRun }
      }),
    onSuccess: (results) => {
      // Invalidate health-related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.systemDatabaseHealth() });
      queryClient.invalidateQueries({ queryKey: queryKeys.systemHealth() });
      
      if (results.success) {
        toast.success('Database cleanup completed successfully');
      } else {
        toast.warning('Database cleanup completed with warnings');
      }
    },
    onError: (error) => {
      toast.error(`Database cleanup failed: ${error.message}`);
    },
  });
};

// Database optimization mutation
export const useDatabaseOptimizationMutation = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => api.post('api/system/database-optimize', DatabaseOptimizationResultsSchema),
    onSuccess: (results) => {
      // Invalidate health-related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.systemDatabaseHealth() });
      queryClient.invalidateQueries({ queryKey: queryKeys.systemHealth() });
      
      if (results.success) {
        toast.success('Database optimization completed successfully');
      } else {
        toast.warning('Database optimization completed with warnings');
      }
    },
    onError: (error) => {
      toast.error(`Database optimization failed: ${error.message}`);
    },
  });
};