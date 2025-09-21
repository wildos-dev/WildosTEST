import { z } from 'zod';
import { createPaginatedSchema, BaseQueryParamsSchema } from './common';

/**
 * Service-related schemas matching FastAPI backend models
 */

// Core service schema
export const ServiceSchema = z.object({
  id: z.number(),
  name: z.string(),
  user_ids: z.array(z.number()),
  inbound_ids: z.array(z.number()),
});

// Service creation schema
export const ServiceCreateSchema = z.object({
  name: z.string(),
  inbound_ids: z.array(z.number()),
});

// Service modification schema
export const ServiceModifySchema = ServiceCreateSchema.partial();

// Service query parameters
export const ServiceQueryParamsSchema = BaseQueryParamsSchema.extend({
  name: z.string().optional(),
});

// Paginated responses
export const ServicesResponseSchema = createPaginatedSchema(ServiceSchema);

// Types
export type Service = z.infer<typeof ServiceSchema>;
export type ServiceCreate = z.infer<typeof ServiceCreateSchema>;
export type ServiceModify = z.infer<typeof ServiceModifySchema>;
export type ServiceQueryParams = z.infer<typeof ServiceQueryParamsSchema>;
export type ServicesResponse = z.infer<typeof ServicesResponseSchema>;