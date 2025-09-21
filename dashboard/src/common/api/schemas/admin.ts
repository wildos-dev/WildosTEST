import { z } from 'zod';
import { createPaginatedSchema, BaseQueryParamsSchema } from './common';

/**
 * Admin-related schemas matching FastAPI backend models
 */

// Core admin schema
export const AdminSchema = z.object({
  id: z.number(),
  username: z.string(),
  enabled: z.boolean(),
  is_sudo: z.boolean(),
  all_services_access: z.boolean(),
  modify_users_access: z.boolean(),
  service_ids: z.array(z.number()),
  subscription_url_prefix: z.string(),
  users_data_usage: z.number(),
});

// Admin creation schema
export const AdminCreateSchema = z.object({
  username: z.string(),
  password: z.string(),
  is_sudo: z.boolean().default(false),
  enabled: z.boolean().default(true),
  all_services_access: z.boolean().default(false),
  modify_users_access: z.boolean().default(false),
  service_ids: z.array(z.number()).default([]),
  subscription_url_prefix: z.string().default(''),
});

// Admin modification schema
export const AdminModifySchema = AdminCreateSchema.omit({ 
  username: true, 
  password: true 
}).partial();

// Admin query parameters
export const AdminQueryParamsSchema = BaseQueryParamsSchema.extend({
  username: z.string().optional(),
});

// Admin token schema - matches backend Token model
export const AdminTokenSchema = z.object({
  access_token: z.string(),
  is_sudo: z.boolean(),
  token_type: z.string().default('bearer').optional(),
});

// Admin stats schema
export const AdminStatsSchema = z.object({
  total: z.number(),
});

// Paginated responses
export const AdminsResponseSchema = createPaginatedSchema(AdminSchema);

// Types
export type Admin = z.infer<typeof AdminSchema>;
export type AdminCreate = z.infer<typeof AdminCreateSchema>;
export type AdminModify = z.infer<typeof AdminModifySchema>;
export type AdminQueryParams = z.infer<typeof AdminQueryParamsSchema>;
export type AdminToken = z.infer<typeof AdminTokenSchema>;
export type AdminStats = z.infer<typeof AdminStatsSchema>;
export type AdminsResponse = z.infer<typeof AdminsResponseSchema>;