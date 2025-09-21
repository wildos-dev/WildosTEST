import { z } from 'zod';
import { DateTimeSchema, OptionalDateTimeSchema, createPaginatedSchema, BaseQueryParamsSchema } from './common';

/**
 * User-related schemas matching FastAPI backend models
 */

// User expire strategy enum
export const UserExpireStrategySchema = z.enum(['never', 'fixed_date', 'start_on_first_use']);

// Data limit reset strategy enum
export const DataLimitResetStrategySchema = z.enum(['no_reset', 'day', 'week', 'month', 'year']);

// User sorting options
export const UserSortingOptionsSchema = z.enum([
  'username',
  'used_traffic',
  'data_limit',
  'expire_date',
  'created_at'
]);

// Core user schema
export const UserSchema = z.object({
  username: z.string(),
  expire_strategy: UserExpireStrategySchema,
  usage_duration: z.number().nullable().optional(),
  activation_deadline: OptionalDateTimeSchema,
  expire_date: OptionalDateTimeSchema,
  data_limit: z.number().optional(),
  data_limit_reset_strategy: DataLimitResetStrategySchema,
  lifetime_used_traffic: z.number(),
  used_traffic: z.number(),
  sub_updated_at: OptionalDateTimeSchema,
  traffic_reset_at: OptionalDateTimeSchema,
  sub_last_user_agent: z.string().optional(),
  enabled: z.boolean(),
  activated: z.boolean(),
  is_active: z.boolean(),
  expired: z.boolean(),
  data_limit_reached: z.boolean(),
  created_at: DateTimeSchema,
  links: z.array(z.string()),
  subscription_url: z.string(),
  service_ids: z.array(z.number()),
  note: z.string(),
  online_at: z.string().optional(),
});

// User creation schema
export const UserCreateSchema = UserSchema.omit({
  lifetime_used_traffic: true,
  used_traffic: true,
  sub_updated_at: true,
  traffic_reset_at: true,
  sub_last_user_agent: true,
  activated: true,
  is_active: true,
  expired: true,
  data_limit_reached: true,
  created_at: true,
  links: true,
  subscription_url: true,
  online_at: true,
}).extend({
  service_ids: z.array(z.number()), // Service IDs for creation
});

// User modification schema
export const UserModifySchema = UserCreateSchema.partial();

// User query parameters
export const UserQueryParamsSchema = BaseQueryParamsSchema.extend({
  username: z.array(z.string()).optional(),
  order_by: UserSortingOptionsSchema.optional(),
  is_active: z.boolean().optional(),
  activated: z.boolean().optional(),
  expired: z.boolean().optional(),
  data_limit_reached: z.boolean().optional(),
  enabled: z.boolean().optional(),
  owner_username: z.string().optional(),
});

// User usage series schema with strict typing for time-series data
export const UserUsageSeriesSchema = z.object({
  username: z.string(),
  node_id: z.number().optional(),
  node_name: z.string().optional(),
  used_traffic: z.array(z.tuple([z.string(), z.number()])), // [ISO DateTime, traffic bytes]
});

// User stats schema
export const UserStatsSchema = z.object({
  total: z.number(),
  active: z.number(),
  on_hold: z.number(),
  expired: z.number(),
  limited: z.number(),
  online: z.number(),
});

// Paginated responses
export const UsersResponseSchema = createPaginatedSchema(UserSchema);
export const UserUsageResponseSchema = UserUsageSeriesSchema;

// Types
export type User = z.infer<typeof UserSchema>;
export type UserCreate = z.infer<typeof UserCreateSchema>;
export type UserModify = z.infer<typeof UserModifySchema>;
export type UserQueryParams = z.infer<typeof UserQueryParamsSchema>;
export type UserExpireStrategy = z.infer<typeof UserExpireStrategySchema>;
export type DataLimitResetStrategy = z.infer<typeof DataLimitResetStrategySchema>;
export type UserSortingOptions = z.infer<typeof UserSortingOptionsSchema>;
export type UserUsageSeries = z.infer<typeof UserUsageSeriesSchema>;
export type UserStats = z.infer<typeof UserStatsSchema>;
export type UsersResponse = z.infer<typeof UsersResponseSchema>;