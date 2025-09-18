import { createFileRoute } from '@tanstack/react-router'
import { z } from 'zod'

export const nodesSearchSchema = z.object({
  q: z.string().optional(),
  status: z.enum(['all','healthy','unhealthy','disabled']).optional().default('all'),
  page: z.coerce.number().int().min(1).optional().default(1),
  showDisabled: z.coerce.boolean().optional().default(false),
})

export const Route = createFileRoute('/_dashboard/nodes')({
  validateSearch: (s) => nodesSearchSchema.parse(s),
})