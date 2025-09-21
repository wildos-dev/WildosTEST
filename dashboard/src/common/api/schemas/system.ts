import { z } from 'zod';

/**
 * System-related schemas matching FastAPI backend models
 */

// Subscription rule result enum
export const SubscriptionRuleResultSchema = z.enum([
  'links',
  'base64-links',
  'sing-box',
  'xray',
  'clash',
  'clash-meta',
  'template',
  'block'
]);

// Subscription rule schema
export const SubscriptionRuleSchema = z.object({
  pattern: z.string(),
  result: SubscriptionRuleResultSchema,
});

// Subscription settings schema
export const SubscriptionSettingsSchema = z.object({
  template_on_acceptance: z.boolean().default(true),
  profile_title: z.string().default('Support'),
  support_link: z.string().default('t.me/support'),
  update_interval: z.number().default(12),
  shuffle_configs: z.boolean().default(false),
  placeholder_if_disabled: z.boolean().default(true),
  placeholder_remark: z.string().default('disabled'),
  rules: z.array(SubscriptionRuleSchema).default([]),
});

// Telegram settings schema
export const TelegramSettingsSchema = z.object({
  api_token: z.string(),
  admin_chat_ids: z.array(z.string()),
  proxy_url: z.string().optional(),
  proxy_secret: z.string().optional(),
}).nullable();

// System health schemas
export const DiskDetailsSchema = z.object({
  usage_percent: z.number(),
  free_gb: z.number(),
  total_gb: z.number(),
  timestamp: z.string().optional(),
});

export const DiskInfoSchema = z.object({
  safe: z.boolean(),
  details: DiskDetailsSchema,
});

export const DatabaseHealthSchema = z.object({
  healthy: z.boolean(),
  info: z.object({
    size_mb: z.number(),
    last_modified: z.string().optional(),
  }),
  issues: z.array(z.string()).default([]),
});

export const SystemHealthSchema = z.object({
  status: z.enum(['healthy', 'warning', 'critical']),
  disk: DiskInfoSchema,
  database: DatabaseHealthSchema,
  timestamp: z.string().optional(),
});

// Monitoring status schema
export const MonitoringStatusSchema = z.object({
  disk_monitoring: z.object({
    active: z.boolean(),
    last_check: z.string().optional(),
    status: z.enum(['safe', 'warning']),
  }),
  database_monitoring: z.object({
    active: z.boolean(),
    status: z.enum(['healthy', 'issues_detected']),
    last_check: z.string().optional(),
  }),
  system_status: z.object({
    overall: z.enum(['healthy', 'needs_attention']),
  }),
});

// Node GRPC port config schema
export const NodeGrpcPortSchema = z.object({
  port: z.number(),
});

// Traffic usage series schema
export const TrafficUsageSeriesSchema = z.object({
  username: z.string().optional(),
  node_id: z.number().optional(),
  node_name: z.string().optional(),
  used_traffic: z.array(z.array(z.union([z.string(), z.number()]))),
});

// Database cleanup results schema
export const DatabaseCleanupResultsSchema = z.object({
  success: z.boolean(),
  cleanup_results: z.record(z.any()),
});

// Database optimization results schema
export const DatabaseOptimizationResultsSchema = z.object({
  success: z.boolean(),
  optimization_results: z.record(z.any()),
});

// Version info schema
export const VersionInfoSchema = z.object({
  version: z.string(),
  name: z.string(),
  description: z.string(),
});

// Readiness check schema
export const ReadinessCheckSchema = z.object({
  status: z.enum(['ready', 'not_ready']),
  message: z.string(),
  issues: z.object({
    disk_safe: z.boolean(),
    database_healthy: z.boolean(),
  }).optional(),
});

// Types
export type SubscriptionRuleResult = z.infer<typeof SubscriptionRuleResultSchema>;
export type SubscriptionRule = z.infer<typeof SubscriptionRuleSchema>;
export type SubscriptionSettings = z.infer<typeof SubscriptionSettingsSchema>;
export type TelegramSettings = z.infer<typeof TelegramSettingsSchema>;
export type DiskInfo = z.infer<typeof DiskInfoSchema>;
export type DatabaseHealth = z.infer<typeof DatabaseHealthSchema>;
export type SystemHealth = z.infer<typeof SystemHealthSchema>;
export type MonitoringStatus = z.infer<typeof MonitoringStatusSchema>;
export type NodeGrpcPort = z.infer<typeof NodeGrpcPortSchema>;
export type TrafficUsageSeries = z.infer<typeof TrafficUsageSeriesSchema>;
export type DatabaseCleanupResults = z.infer<typeof DatabaseCleanupResultsSchema>;
export type DatabaseOptimizationResults = z.infer<typeof DatabaseOptimizationResultsSchema>;
export type VersionInfo = z.infer<typeof VersionInfoSchema>;
export type ReadinessCheck = z.infer<typeof ReadinessCheckSchema>;
export type DiskDetails = z.infer<typeof DiskDetailsSchema>;