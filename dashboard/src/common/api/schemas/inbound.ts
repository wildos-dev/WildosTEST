import { z } from 'zod';
import { ProtocolSchema, createPaginatedSchema, BaseQueryParamsSchema } from './common';
import { NodeSchema } from './node';

/**
 * Inbound-related schemas matching FastAPI backend models
 */

// Core inbound schema
export const InboundSchema = z.object({
  id: z.number(),
  tag: z.string(),
  protocol: ProtocolSchema,
  network: z.string(),
  node: NodeSchema,
  tls: z.string(),
  port: z.number().optional(),
});

// Inbound host schema
export const InboundHostSchema = z.object({
  id: z.number(),
  remark: z.string(),
  address: z.string(),
  port: z.number().optional(),
  path: z.string().optional(),
  sni: z.string().optional(),
  host: z.string().optional(),
  security: z.string().optional(),
  alpn: z.string().optional(),
  fingerprint: z.string().optional(),
  allowinsecure: z.boolean().optional(),
  is_disabled: z.boolean().default(false),
  mux_enable: z.boolean().optional(),
  mux_protocol: z.string().optional(),
  mux_max_connections: z.number().optional(),
  mux_min_streams: z.number().optional(),
  mux_max_streams: z.number().optional(),
  fragment_setting: z.string().optional(),
  noise_setting: z.string().optional(),
  random_user_agent: z.boolean().optional(),
  inbound_id: z.number(),
});

// Inbound host creation schema
export const InboundHostCreateSchema = InboundHostSchema.omit({
  id: true,
  inbound_id: true,
});

// Inbound host modification schema
export const InboundHostModifySchema = InboundHostCreateSchema.partial();

// Inbound query parameters
export const InboundQueryParamsSchema = BaseQueryParamsSchema.extend({
  tag: z.string().optional(),
});

// Paginated responses
export const InboundsResponseSchema = createPaginatedSchema(InboundSchema);
export const InboundHostsResponseSchema = createPaginatedSchema(InboundHostSchema);

// Types
export type Inbound = z.infer<typeof InboundSchema>;
export type InboundHost = z.infer<typeof InboundHostSchema>;
export type InboundHostCreate = z.infer<typeof InboundHostCreateSchema>;
export type InboundHostModify = z.infer<typeof InboundHostModifySchema>;
export type InboundQueryParams = z.infer<typeof InboundQueryParamsSchema>;
export type InboundsResponse = z.infer<typeof InboundsResponseSchema>;
export type InboundHostsResponse = z.infer<typeof InboundHostsResponseSchema>;