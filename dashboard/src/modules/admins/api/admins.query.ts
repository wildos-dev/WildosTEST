import { useQuery } from "@tanstack/react-query";
import { fetch } from "@wildosvpn/common/utils";
import { AdminType } from "@wildosvpn/modules/admins";
import {
    FetchEntityReturn,
    UseEntityQueryProps,
    EntityQueryKeyType
} from "@wildosvpn/libs/entity-table";
import { buildAdminsQueryKey } from "@wildosvpn/libs/entity-table";
import { z } from "zod";

// Zod schema for AdminType based on the interface definition
const AdminTypeSchema = z.object({
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

const AdminsListResponseSchema = z.object({
    items: z.array(AdminTypeSchema).default([]),
    pages: z.number().int().nonnegative().default(0),
});

export async function fetchAdmins({ queryKey }: EntityQueryKeyType): FetchEntityReturn<AdminType> {
    try {
        // Safe array access with bounds checking to prevent crashes
        const pagination = queryKey.length > 1 && queryKey[1] ? queryKey[1] : { page: 1, size: 10 };
        const primaryFilter = queryKey.length > 2 ? queryKey[2] : "";
        const sortInfo = queryKey.length > 3 && queryKey[3] ? queryKey[3] : { desc: false, sortBy: "created_at" };
        const filtersInfo = queryKey.length > 4 && queryKey[4] ? queryKey[4] : { filters: {} };
        const filters = filtersInfo.filters || {};
        
        const result = await fetch(`admins`, {
            query: {
                ...pagination,
                ...filters,
                username: primaryFilter,
                descending: sortInfo.desc,
                order_by: sortInfo.sortBy,
            }
        });
        
        // Validate and parse the API response
        const parsed = AdminsListResponseSchema.parse(result);
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

export const AdminsQueryFetchKey = "admins";

export const useAdminsQuery = ({
    page, size, sortBy = "created_at", desc = false, filters = {}
}: UseEntityQueryProps) => {
    return useQuery({
        queryKey: buildAdminsQueryKey({ page, size }, filters, { sortBy, desc }),
        queryFn: fetchAdmins,
        placeholderData: { entities: [] as AdminType[], pageCount: 0 }
    })
}
