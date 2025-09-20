import { useQuery } from "@tanstack/react-query";
import { fetch } from "@wildosvpn/common/utils";
import { UserType } from "@wildosvpn/modules/users";
import type {
    DoubleEntityQueryKeyType,
    UseEntityQueryProps,
    FetchEntityReturn
} from "@wildosvpn/libs/entity-table";
import { z } from "zod";

// Reuse UserType schemas from users.query.ts
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

const ServiceUsersListResponseSchema = z.object({
    items: z.array(UserTypeSchema).default([]),
    pages: z.number().int().nonnegative().default(0),
});

interface UseServiceUsersQueryProps extends UseEntityQueryProps {
    serviceId: number;
}

export async function fetchServiceUsers({ queryKey }: DoubleEntityQueryKeyType): FetchEntityReturn<UserType> {
    try {
        // Safe array access with bounds checking to prevent crashes
        const pagination = queryKey.length > 2 && queryKey[2] ? queryKey[2] : { page: 1, size: 10 };
        const primaryFilter = queryKey.length > 3 ? queryKey[3] : "";
        
        const result = await fetch(`services/${queryKey[1]}/users`, {
            query: {
                ...pagination,
                username: primaryFilter,
            }
        });
        
        // Validate and parse the API response
        const parsed = ServiceUsersListResponseSchema.parse(result);
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

const ServicesQueryFetchKey = "services";

export const useUsersServiceQuery = ({
    serviceId, page = 1, size = 50
}: UseServiceUsersQueryProps) => {
    return useQuery({
        queryKey: [ServicesQueryFetchKey, serviceId, { page, size }],
        queryFn: fetchServiceUsers,
        placeholderData: { entities: [] as UserType[], pageCount: 0 },
    })
}
