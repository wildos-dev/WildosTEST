import { z } from 'zod';

/**
 * Subscription-related schemas matching FastAPI backend models
 */

// Subscription user info schema
export const SubscriptionUserInfoSchema = z.object({
  upload: z.number(),
  download: z.number(),
  total: z.number(),
  expire: z.number(),
});

// Client type enum for subscription
export const ClientTypeSchema = z.enum([
  'sing-box',
  'wireguard',
  'clash-meta',
  'clash',
  'xray',
  'v2ray',
  'links'
]);

// Types
export type SubscriptionUserInfo = z.infer<typeof SubscriptionUserInfoSchema>;
export type ClientType = z.infer<typeof ClientTypeSchema>;