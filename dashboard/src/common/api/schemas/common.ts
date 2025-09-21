import { z } from 'zod';

/**
 * Common schemas used across multiple API endpoints
 */

// Pagination schema matching FastAPI pagination
export const PaginationSchema = z.object({
  items: z.array(z.any()),
  pages: z.number().int().nonnegative(),
  page: z.number().int().positive().optional(),
  size: z.number().int().positive().optional(),
  total: z.number().int().nonnegative().optional(),
});

// Generic paginated response
export function createPaginatedSchema<T extends z.ZodTypeAny>(itemSchema: T) {
  return z.object({
    items: z.array(itemSchema),
    pages: z.number().int().nonnegative(),
    page: z.number().int().positive().optional(),
    size: z.number().int().positive().optional(),
    total: z.number().int().nonnegative().optional(),
  });
}

// Query parameters for pagination
export const PaginationParamsSchema = z.object({
  page: z.number().int().positive().default(1),
  size: z.number().int().positive().default(10),
});

// Sorting parameters
export const SortingParamsSchema = z.object({
  order_by: z.string().optional(),
  descending: z.boolean().default(false),
});

// Base query parameters combining pagination and sorting (used by all modules)
export const BaseQueryParamsSchema = PaginationParamsSchema.merge(SortingParamsSchema);

// Standard error response (expanded to handle different FastAPI error types)
export const ErrorResponseSchema = z.object({
  detail: z.string(),
  status_code: z.number().int().optional(),
  code: z.string().optional(),
  errors: z.array(z.object({
    loc: z.array(z.union([z.string(), z.number()])).optional(),
    msg: z.string(),
    type: z.string(),
  })).optional(),
});

// Standard success response for mutations
export const SuccessResponseSchema = z.object({
  success: z.boolean().default(true),
  message: z.string().optional(),
});

// Date/time schemas
export const DateTimeSchema = z.string().or(z.date()).transform((val) => {
  if (typeof val === 'string') {
    return new Date(val);
  }
  return val;
});

export const OptionalDateTimeSchema = z.string().or(z.date()).nullable().optional().transform((val) => {
  if (val === null || val === undefined) return val;
  if (typeof val === 'string') {
    return new Date(val);
  }
  return val;
});

// Common enums
export const StatusSchema = z.enum(['healthy', 'unhealthy', 'none', 'disabled']);
export const ProtocolSchema = z.enum([
  'wireguard',
  'vless',
  'vmess',
  'trojan',
  'shadowtls',
  'shadowsocks',
  'shadowsocks2022',
  'hysteria2',
  'tuic'
]);

// Types
export type PaginationParams = z.infer<typeof PaginationParamsSchema>;
export type SortingParams = z.infer<typeof SortingParamsSchema>;
export type BaseQueryParams = z.infer<typeof BaseQueryParamsSchema>;
export type ErrorResponse = z.infer<typeof ErrorResponseSchema>;
export type SuccessResponse = z.infer<typeof SuccessResponseSchema>;
export type Status = z.infer<typeof StatusSchema>;
export type Protocol = z.infer<typeof ProtocolSchema>;