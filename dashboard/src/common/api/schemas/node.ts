import { z } from 'zod';
import { StatusSchema, OptionalDateTimeSchema, createPaginatedSchema, BaseQueryParamsSchema } from './common';

/**
 * Node-related schemas matching FastAPI backend models
 */

// Node connection backend enum
export const NodeConnectionBackendSchema = z.enum(['grpclib']);

// Node backend schema
export const NodeBackendSchema = z.object({
  name: z.string(),
  backend_type: z.string(),
  version: z.string(),
  running: z.boolean(),
});

// Core node schema
export const NodeSchema = z.object({
  id: z.number(),
  name: z.string(),
  address: z.string(),
  port: z.number(),
  status: StatusSchema,
  usage_coefficient: z.number().default(1.0),
  connection_backend: NodeConnectionBackendSchema.default('grpclib'),
  backends: z.array(NodeBackendSchema).default([]),
  xray_version: z.string().optional(),
  last_status_change: z.string().optional(),
  message: z.string().optional(),
  created_at: z.string().optional(),
  uplink: z.number().optional(),
  downlink: z.number().optional(),
  certificate: z.string().nullable().optional(),
  private_key: z.string().nullable().optional(),
  cert_created_at: z.string().nullable().optional(),
  cert_expires_at: z.string().nullable().optional(),
});

// Node creation schema
export const NodeCreateSchema = z.object({
  name: z.string(),
  address: z.string(),
  port: z.number(),
  usage_coefficient: z.number().default(1.0),
  connection_backend: NodeConnectionBackendSchema.default('grpclib'),
});

// Node modification schema
export const NodeModifySchema = NodeCreateSchema.partial();

// Node query parameters
export const NodeQueryParamsSchema = BaseQueryParamsSchema.extend({
  status: z.array(StatusSchema).optional(),
  name: z.string().optional(),
  include_disabled: z.boolean().optional(),
});

// Node settings schema
export const NodeSettingsSchema = z.object({
  min_node_version: z.string(),
  certificate_file: z.string(),
});

// Backend stats schema
export const BackendStatsSchema = z.object({
  name: z.string(),
  backend_type: z.string(),
  version: z.string(),
  running: z.boolean(),
  uptime: z.number().optional(),
  memory_usage: z.number().optional(),
  cpu_usage: z.number().optional(),
});

// All backends stats response schema (mapping)
export const AllBackendsStatsResponseSchema = z.record(BackendStatsSchema);

// Node usage schema
export const NodeUsageSchema = z.object({
  node_id: z.number(),
  node_name: z.string(),
  uplink: z.number(),
  downlink: z.number(),
  uplink_speed: z.number().optional(),
  downlink_speed: z.number().optional(),
});

// Host system metrics schema
export const HostSystemMetricsSchema = z.object({
  cpu_percent: z.number(),
  cpu_count: z.number(),
  memory_total: z.number(),
  memory_used: z.number(),
  memory_free: z.number(),
  disk_total: z.number(),
  disk_used: z.number(),
  disk_free: z.number(),
  uptime: z.number(),
  loads: z.array(z.number()),
});

// Node stats schema
export const NodeStatsSchema = z.object({
  total: z.number(),
  healthy: z.number(),
  unhealthy: z.number(),
});

// Peak events schema
export const PeakEventSchema = z.object({
  id: z.number(),
  node_id: z.number(),
  node_name: z.string(),
  event_type: z.string(),
  severity: z.string(),
  message: z.string(),
  timestamp: OptionalDateTimeSchema,
  resolved: z.boolean().default(false),
});

// Paginated responses
export const NodesResponseSchema = createPaginatedSchema(NodeSchema);
export const NodeUsageResponseSchema = z.array(NodeUsageSchema);
export const PeakEventsResponseSchema = createPaginatedSchema(PeakEventSchema);

// Types
export type Node = z.infer<typeof NodeSchema>;
export type NodeCreate = z.infer<typeof NodeCreateSchema>;
export type NodeModify = z.infer<typeof NodeModifySchema>;
export type NodeQueryParams = z.infer<typeof NodeQueryParamsSchema>;
export type NodeConnectionBackend = z.infer<typeof NodeConnectionBackendSchema>;
export type NodeBackend = z.infer<typeof NodeBackendSchema>;
export type NodeSettings = z.infer<typeof NodeSettingsSchema>;
export type BackendStats = z.infer<typeof BackendStatsSchema>;
export type AllBackendsStatsResponse = z.infer<typeof AllBackendsStatsResponseSchema>;
export type NodeUsage = z.infer<typeof NodeUsageSchema>;
export type HostSystemMetrics = z.infer<typeof HostSystemMetricsSchema>;
export type NodeStats = z.infer<typeof NodeStatsSchema>;
export type PeakEvent = z.infer<typeof PeakEventSchema>;
export type NodesResponse = z.infer<typeof NodesResponseSchema>;
export type NodeUsageResponse = z.infer<typeof NodeUsageResponseSchema>;
export type PeakEventsResponse = z.infer<typeof PeakEventsResponseSchema>;