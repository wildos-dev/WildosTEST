import { useQuery } from "@tanstack/react-query";
import { fetch } from "@wildosvpn/common/utils";
import { UserType } from "@wildosvpn/modules/users";
import {
    FetchEntityReturn,
    UseEntityQueryProps,
    EntityQueryKeyType,
    buildUsersQueryKey
} from "@wildosvpn/libs/entity-table";
import { z } from "zod";

// Zod schemas for API response validation
const ExpireStrategySchema = z.enum(["never", "fixed_date", "start_on_first_use"]);
const DataLimitResetStrategySchema = z.enum(["no_reset", "day", "week", "month", "year"]);

const UserTypeSchema = z.object({
    expire_strategy: ExpireStrategySchema,
    usage_duration: z.number().nullable().optional(),
    activation_deadline: z.string().or(z.date()).nullable().optional(),
    expire_date: z.string().or(z.date()).nullable().optional(),
    data_limit: z.number().optional(),
    data_limit_reset_strategy: DataLimitResetStrategySchema,
    lifetime_used_traffic: z.number(),
    used_traffic: z.number(),
    sub_updated_at: z.string().or(z.date()).optional(),
    traffic_reset_at: z.string().or(z.date()).optional(),
    sub_last_user_agent: z.string().optional(),
    enabled: z.boolean(),
    activated: z.boolean(),
    is_active: z.boolean(),
    expired: z.boolean(),
    data_limit_reached: z.boolean(),
    username: z.string(),
    created_at: z.string().or(z.date()),
    links: z.array(z.string()),
    subscription_url: z.string(),
    service_ids: z.array(z.number()),
    note: z.string(),
    online_at: z.string(),
});

const UsersListResponseSchema = z.object({
    items: z.array(UserTypeSchema).default([]),
    pages: z.number().int().nonnegative().default(0),
});

export type SortUserBy = "username" | "used_traffic" | "data_limit" | "expire_date" | "created_at"

export async function fetchUsers({ queryKey }: EntityQueryKeyType): FetchEntityReturn<UserType> {
    try {
        // Safe array access with bounds checking to prevent crashes
        const pagination = queryKey.length > 1 && queryKey[1] ? queryKey[1] : { page: 1, size: 10 };
        const primaryFilter = queryKey.length > 2 ? queryKey[2] : "";
        const sortInfo = queryKey.length > 3 && queryKey[3] ? queryKey[3] : { desc: false, sortBy: "created_at" };
        const filtersInfo = queryKey.length > 4 && queryKey[4] ? queryKey[4] : { filters: {} };
        const filters = filtersInfo.filters || {};
        
        const result = await fetch(`users`, {
            query: {
                page: pagination.page === 0 ? 1 : pagination.page,
                size: pagination.size,
                ...filters,
                username: primaryFilter,
                descending: sortInfo.desc,
                order_by: sortInfo.sortBy,
            }
        });
        
        // Validate and parse the API response
        const parsed = UsersListResponseSchema.parse(result);
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

export const UsersQueryFetchKey = "users";

export const useUsersQuery = ({
    page, size, sortBy = "created_at", desc = false, filters = {}
}: UseEntityQueryProps) => {
    return useQuery({
        queryKey: buildUsersQueryKey({ page, size }, filters, { sortBy, desc }),
        queryFn: fetchUsers,
        placeholderData: { entities: [] as UserType[], pageCount: 0 }
    })
}
