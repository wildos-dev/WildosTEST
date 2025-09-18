import { HostType } from "@wildosvpn/modules/hosts";
import { useQuery } from "@tanstack/react-query";
import { fetch } from "@wildosvpn/common/utils";
import {
    FetchEntityReturn,
    UseEntityQueryProps,
    EntitySidebarQueryKeyType
} from "@wildosvpn/libs/entity-table";
import { buildHostsSelectableQueryKey } from "@wildosvpn/libs/entity-table";
import { z } from "zod";

// Import protocol types for proper validation
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

// Zod schema based on the actual HostType definition
const HostTypeSchema = z.object({
    id: z.number().optional(),
    remark: z.string(),
    address: z.string(),
    port: z.union([z.number().int().gte(1).lte(65535), z.null()]),
    weight: z.number().int().nullable().optional(),
    is_disabled: z.boolean().default(false),
    inboundId: z.number().optional(),
    protocol: ProtocolSchema,
});

const HostsListResponseSchema = z.object({
    items: z.array(HostTypeSchema).default([]),
    pages: z.number().int().nonnegative().default(0),
});

export async function fetchHosts({ queryKey }: EntitySidebarQueryKeyType): FetchEntityReturn<HostType> {
    try {
        // Safe array access with bounds checking to prevent crashes
        const pagination = queryKey.length > 3 && queryKey[3] ? queryKey[3] : { page: 1, size: 10 };
        const primaryFilter = queryKey.length > 4 ? queryKey[4] : "";
        const sortInfo = queryKey.length > 5 && queryKey[5] ? queryKey[5] : { desc: false, sortBy: "created_at" };
        const filtersInfo = queryKey.length > 6 && queryKey[6] ? queryKey[6] : { filters: {} };
        const filters = filtersInfo.filters || {};
        
        const result = await fetch(queryKey[1] !== undefined ? `inbounds/${queryKey[1]}/hosts` : `inbounds/hosts`, {
            query: {
                ...pagination,
                ...filters,
                remark: primaryFilter,
                descending: sortInfo.desc,
                order_by: sortInfo.sortBy,
            }
        });
        
        // Validate and parse the API response
        const parsed = HostsListResponseSchema.parse(result);
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

export const HostsQueryFetchKey = "hosts";

export const useHostsQuery = ({
    page, size, sortBy = "created_at", desc = false, filters = {}, inboundId
}: UseEntityQueryProps & { inboundId?: number }) => {
    return useQuery({
        queryKey: buildHostsSelectableQueryKey(
            "inbounds",
            inboundId,
            { page, size },
            filters,
            { sortBy, desc }
        ),
        queryFn: fetchHosts,
        placeholderData: { entities: [] as HostType[], pageCount: 0 }
    })
}
