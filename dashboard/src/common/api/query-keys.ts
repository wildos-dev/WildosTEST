/**
 * Standardized query key patterns for consistent caching
 * Following React Query best practices for hierarchical cache invalidation
 */

import { PaginationParams, SortingParams } from './schemas';

// Base query keys for different entities
export const queryKeys = {
  // Users
  users: ['users'] as const,
  usersList: (params?: {
    pagination?: Partial<PaginationParams>;
    sorting?: Partial<SortingParams>;
    filters?: Record<string, any>;
  }) => [...queryKeys.users, 'list', params] as const,
  usersUser: (username: string) => [...queryKeys.users, 'detail', username] as const,
  usersUserServices: (username: string) => [...queryKeys.users, 'detail', username, 'services'] as const,
  usersUserUsage: (username: string, params?: { start_date?: string; end_date?: string }) => 
    [...queryKeys.users, 'detail', username, 'usage', params] as const,
  usersStats: () => [...queryKeys.users, 'stats'] as const,

  // Admins
  admins: ['admins'] as const,
  adminsList: (params?: {
    pagination?: Partial<PaginationParams>;
    sorting?: Partial<SortingParams>;
    filters?: Record<string, any>;
  }) => [...queryKeys.admins, 'list', params] as const,
  adminsAdmin: (username: string) => [...queryKeys.admins, 'detail', username] as const,
  adminsAdminToken: (username: string) => [...queryKeys.admins, 'detail', username, 'token'] as const,
  adminsStats: () => [...queryKeys.admins, 'stats'] as const,

  // Nodes
  nodes: ['nodes'] as const,
  nodesList: (params?: {
    pagination?: Partial<PaginationParams>;
    sorting?: Partial<SortingParams>;
    filters?: Record<string, any>;
  }) => [...queryKeys.nodes, 'list', params] as const,
  nodesNode: (nodeId: number) => [...queryKeys.nodes, 'detail', nodeId] as const,
  nodesNodeSettings: (nodeId: number) => [...queryKeys.nodes, 'detail', nodeId, 'settings'] as const,
  nodesNodeUsage: (nodeId: number, params?: { start_date?: string; end_date?: string }) => 
    [...queryKeys.nodes, 'detail', nodeId, 'usage', params] as const,
  nodesStats: () => [...queryKeys.nodes, 'stats'] as const,
  nodesUsage: (params?: { start_date?: string; end_date?: string }) => 
    [...queryKeys.nodes, 'usage', params] as const,
  nodesBackendStats: (nodeId: number) => [...queryKeys.nodes, 'detail', nodeId, 'backend-stats'] as const,
  nodesAllBackendStats: () => [...queryKeys.nodes, 'all-backend-stats'] as const,
  nodesHostSystem: (nodeId: number) => [...queryKeys.nodes, 'detail', nodeId, 'host-system'] as const,
  nodesPeakEvents: (nodeId: number) => [...queryKeys.nodes, 'detail', nodeId, 'peak-events'] as const,
  nodesAggregateMetrics: () => [...queryKeys.nodes, 'aggregate-metrics'] as const,

  // Services
  services: ['services'] as const,
  servicesList: (params?: {
    pagination?: Partial<PaginationParams>;
    sorting?: Partial<SortingParams>;
    filters?: Record<string, any>;
  }) => [...queryKeys.services, 'list', params] as const,
  servicesService: (serviceId: number) => [...queryKeys.services, 'detail', serviceId] as const,
  servicesServiceUsers: (serviceId: number) => [...queryKeys.services, 'detail', serviceId, 'users'] as const,
  servicesServiceInbounds: (serviceId: number) => [...queryKeys.services, 'detail', serviceId, 'inbounds'] as const,

  // Inbounds
  inbounds: ['inbounds'] as const,
  inboundsList: (params?: {
    pagination?: Partial<PaginationParams>;
    sorting?: Partial<SortingParams>;
    filters?: Record<string, any>;
  }) => [...queryKeys.inbounds, 'list', params] as const,
  inboundsInbound: (inboundId: number) => [...queryKeys.inbounds, 'detail', inboundId] as const,
  inboundsInboundHosts: (inboundId: number) => [...queryKeys.inbounds, 'detail', inboundId, 'hosts'] as const,
  inboundsHosts: (params?: {
    pagination?: Partial<PaginationParams>;
    sorting?: Partial<SortingParams>;
    filters?: Record<string, any>;
  }) => [...queryKeys.inbounds, 'hosts', params] as const,
  inboundsHost: (hostId: number) => [...queryKeys.inbounds, 'hosts', 'detail', hostId] as const,

  // System
  system: ['system'] as const,
  systemSubscriptionSettings: () => [...queryKeys.system, 'settings', 'subscription'] as const,
  systemTelegramSettings: () => [...queryKeys.system, 'settings', 'telegram'] as const,
  systemNodeGrpcPort: () => [...queryKeys.system, 'config', 'node-grpc-port'] as const,
  systemTrafficStats: (params?: { start_date?: string; end_date?: string }) => 
    [...queryKeys.system, 'stats', 'traffic', params] as const,
  systemHealth: () => [...queryKeys.system, 'health'] as const,
  systemDiskInfo: () => [...queryKeys.system, 'disk-info'] as const,
  systemDatabaseHealth: () => [...queryKeys.system, 'database-health'] as const,
  systemMonitoringStatus: () => [...queryKeys.system, 'monitoring-status'] as const,
  systemVersion: () => [...queryKeys.system, 'version'] as const,
  systemReadiness: () => [...queryKeys.system, 'readiness'] as const,

  // Settings
  settings: ['settings'] as const,
  settingsNodeConfig: () => [...queryKeys.settings, 'node-config'] as const,
} as const;

// Helper function to get all related query keys for cache invalidation
export const getRelatedQueryKeys = {
  user: (username: string) => [
    queryKeys.usersUser(username),
    queryKeys.usersUserServices(username),
    queryKeys.usersUserUsage(username),
    queryKeys.usersList(),
    queryKeys.usersStats(),
  ],
  admin: (username: string) => [
    queryKeys.adminsAdmin(username),
    queryKeys.adminsAdminToken(username),
    queryKeys.adminsList(),
    queryKeys.adminsStats(),
  ],
  node: (nodeId: number) => [
    queryKeys.nodesNode(nodeId),
    queryKeys.nodesNodeSettings(nodeId),
    queryKeys.nodesNodeUsage(nodeId),
    queryKeys.nodesBackendStats(nodeId),
    queryKeys.nodesHostSystem(nodeId),
    queryKeys.nodesPeakEvents(nodeId),
    queryKeys.nodesList(),
    queryKeys.nodesStats(),
    queryKeys.nodesUsage(),
    queryKeys.nodesAllBackendStats(),
    queryKeys.nodesAggregateMetrics(),
  ],
  service: (serviceId: number) => [
    queryKeys.servicesService(serviceId),
    queryKeys.servicesServiceUsers(serviceId),
    queryKeys.servicesServiceInbounds(serviceId),
    queryKeys.servicesList(),
  ],
  inbound: (inboundId: number) => [
    queryKeys.inboundsInbound(inboundId),
    queryKeys.inboundsInboundHosts(inboundId),
    queryKeys.inboundsList(),
  ],
  host: (hostId: number) => [
    queryKeys.inboundsHost(hostId),
    queryKeys.inboundsHosts(),
  ],
};