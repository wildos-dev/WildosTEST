import type { NodeType } from "@wildosvpn/modules/nodes";
import { useQuery } from "@tanstack/react-query";
import { fetch } from "@wildosvpn/common/utils";
import type {
    EntityQueryKeyType,
    UseEntityQueryProps,
    FetchEntityReturn
} from "@wildosvpn/libs/entity-table";
import { buildNodesQueryKey } from "@wildosvpn/libs/entity-table";
import { z } from "zod";

// Zod schemas for API response validation
const NodeBackendSchema = z.object({
    name: z.string(),
    backend_type: z.string(),
    version: z.string(),
    running: z.boolean(),
});

const NodeTypeSchema = z.object({
    id: z.number(),
    name: z.string(),
    address: z.string(),
    port: z.number(),
    status: z.enum(["healthy", "unhealthy", "none", "disabled"]),
    usage_coefficient: z.number().default(1.0),
    connection_backend: z.enum(["grpclib"]).default("grpclib"),
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

const NodesListResponseSchema = z.object({
    items: z.array(NodeTypeSchema).default([]),
    pages: z.number().int().nonnegative().default(0),
});

export async function fetchNodes({
    queryKey,
}: EntityQueryKeyType): FetchEntityReturn<NodeType> {
    try {
        // Safe array access with bounds checking to prevent crashes
        const pagination = queryKey.length > 1 && queryKey[1] ? queryKey[1] : { page: 1, size: 10 };
        const primaryFilter = queryKey.length > 2 ? queryKey[2] : "";
        const sortInfo = queryKey.length > 3 && queryKey[3] ? queryKey[3] : { desc: false, sortBy: "created_at" };
        const filtersInfo = queryKey.length > 4 && queryKey[4] ? queryKey[4] : { filters: {} };
        const filters = filtersInfo.filters || {};
        
        const result = await fetch('nodes', {
            query: {
                ...pagination,
                ...filters,
                ...(primaryFilter && { name: primaryFilter }),
                descending: sortInfo.desc,
                order_by: sortInfo.sortBy,
                ...(filters.showDisabled === 'true' || filters.status === 'disabled') && { include_disabled: true },
            }
        });
        
        // Validate and parse the API response
        const parsed = NodesListResponseSchema.parse(result);
        return {
            entities: parsed.items,
            pageCount: parsed.pages,
        };
    } catch (error) {
        // If validation fails, throw a descriptive error
        if (error instanceof z.ZodError) {
            throw new Error(`Invalid API response structure: ${error.message}`);
        }
        throw error;
    }
}

export const NodesQueryFetchKey = "nodes";

export const useNodesQuery = ({
    page, size, sortBy = "created_at", desc = false, filters = {}
}: UseEntityQueryProps) => {
    return useQuery({
        queryKey: buildNodesQueryKey({ page, size }, filters, { sortBy, desc }),
        queryFn: fetchNodes,
        placeholderData: { entities: [] as NodeType[], pageCount: 0 },
    });
};
