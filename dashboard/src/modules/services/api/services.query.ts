import { fetch } from "@wildosvpn/common/utils";
import { ServiceType } from "../types";
import {
    EntityQueryKeyType,
    SelectableEntityQueryKeyType,
    FetchEntityReturn,
    UseEntityQueryProps,
    buildServicesQueryKey
} from "@wildosvpn/libs/entity-table";
import { useQuery } from "@tanstack/react-query";
import { z } from "zod";

// Zod schemas for API response validation
const ServiceTypeSchema = z.object({
    id: z.number(),
    name: z.string(),
    user_ids: z.array(z.number()),
    inbound_ids: z.array(z.number()),
});

const ServicesListResponseSchema = z.object({
    items: z.array(ServiceTypeSchema).default([]),
    pages: z.number().int().nonnegative().default(0),
});

export async function fetchServices({ queryKey }: EntityQueryKeyType): FetchEntityReturn<ServiceType> {
    try {
        // Safe array access with bounds checking to prevent crashes
        const pagination = queryKey.length > 1 && queryKey[1] ? queryKey[1] : { page: 1, size: 10 };
        const primaryFilter = queryKey.length > 2 ? queryKey[2] : "";
        const sortInfo = queryKey.length > 3 && queryKey[3] ? queryKey[3] : { desc: false, sortBy: "created_at" };
        const filtersInfo = queryKey.length > 4 && queryKey[4] ? queryKey[4] : { filters: {} };
        const filters = filtersInfo.filters || {};
        
        const result = await fetch(`services`, {
            query: {
                ...pagination,
                ...filters,
                name: primaryFilter,
                descending: sortInfo.desc,
                order_by: sortInfo.sortBy,
            }
        });
        
        // Validate and parse the API response
        const parsed = ServicesListResponseSchema.parse(result);
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

export async function fetchUserServices({ queryKey }: SelectableEntityQueryKeyType): FetchEntityReturn<ServiceType> {
    try {
        // Safe array access with bounds checking to prevent crashes
        const pagination = queryKey.length > 3 && queryKey[3] ? queryKey[3] : { page: 1, size: 10 };
        const primaryFilter = queryKey.length > 4 ? queryKey[4] : "";
        const sortInfo = queryKey.length > 5 && queryKey[5] ? queryKey[5] : { desc: false, sortBy: "created_at" };
        const filtersInfo = queryKey.length > 6 && queryKey[6] ? queryKey[6] : { filters: {} };
        const filters = filtersInfo.filters || {};
        
        const result = await fetch(`services`, {
            query: {
                ...pagination,
                ...filters,
                name: primaryFilter,
                descending: sortInfo.desc,
                order_by: sortInfo.sortBy,
            }
        });
        
        // Validate and parse the API response
        const parsed = ServicesListResponseSchema.parse(result);
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


export const ServicesQueryFetchKey = "services";

export const useServicesQuery = ({
    page, size, sortBy = "created_at", desc = false, filters = {}
}: UseEntityQueryProps) => {
    return useQuery({
        queryKey: buildServicesQueryKey({ page, size }, filters, { sortBy, desc }),
        queryFn: fetchServices,
        placeholderData: { entities: [] as ServiceType[], pageCount: 0 }
    })
}
