
import { useQuery } from "@tanstack/react-query";
import { fetch } from "@wildosvpn/common/utils";
import {
    FetchEntityReturn,
    UseEntityQueryProps,
    EntityQueryKeyType
} from "@wildosvpn/libs/entity-table";
import { InboundType } from "../types";
import { z } from "zod";

// Import existing schemas from service-inbounds.query.ts
const ProtocolSchema = z.enum([
    "wireguard",
    "vless", 
    "vmess",
    "trojan",
    "shadowtls",
    "shadowsocks",
    "shadowsocks2022",
    "hysteria2",
    "tuic"
]);

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

const InboundSchema = z.object({
    id: z.number(),
    tag: z.string(),
    protocol: ProtocolSchema,
    network: z.string(),
    node: NodeTypeSchema,
    tls: z.string(),
    port: z.number().optional(),
});

const InboundsListResponseSchema = z.object({
    items: z.array(InboundSchema).default([]),
    pages: z.number().int().nonnegative().default(0),
});

export async function fetchInbounds({ queryKey }: EntityQueryKeyType): FetchEntityReturn<InboundType> {
    try {
        // Safe array access with bounds checking to prevent crashes
        const pagination = queryKey.length > 1 && queryKey[1] ? queryKey[1] : { page: 1, size: 10 };
        const primaryFilter = queryKey.length > 2 ? queryKey[2] : "";
        const sortInfo = queryKey.length > 3 && queryKey[3] ? queryKey[3] : { desc: false, sortBy: "created_at" };
        const filtersInfo = queryKey.length > 4 && queryKey[4] ? queryKey[4] : { filters: {} };
        const filters = filtersInfo.filters || {};
        
        const result = await fetch(`inbounds`, {
            query: {
                ...pagination,
                ...filters,
                tag: primaryFilter,
                descending: sortInfo.desc,
                order_by: sortInfo.sortBy,
            }
        });
        
        // Validate and parse the API response
        const parsed = InboundsListResponseSchema.parse(result);
        return {
            entities: parsed.items,
            pageCount: parsed.pages
        };
    } catch (error) {
        // If validation fails, throw a descriptive error
        if (error instanceof z.ZodError) {
            throw new Error(`Invalid API response structure: ${error.message}`);
        }
        throw error;
    }
}

export const InboundsQueryFetchKey = "inbounds";

export const useInboundsQuery = ({
    page, size, sortBy = "created_at", desc = false, filters = {}
}: UseEntityQueryProps) => {
    return useQuery({
        queryKey: [InboundsQueryFetchKey, { page, size }, filters?.tag ?? "", { sortBy, desc }, { filters }],
        queryFn: fetchInbounds,
        placeholderData: { entities: [] as InboundType[], pageCount: 0 }
    })
}
