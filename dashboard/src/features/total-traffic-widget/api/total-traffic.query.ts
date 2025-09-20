import { useQuery } from "@tanstack/react-query";
import { fetch } from "@wildosvpn/common/utils";

export type UsageMetric = number[];

export interface TotalTrafficsResponse {
    usages: Array<UsageMetric>;
    total: number;
}

export interface TotalTrafficsQueryOptions {
    start: string;
    end: string
}

export type TotalTrafficsQueryKey = [string, string, string, { start?: string, end?: string }]

export const TotalTrafficsDefault = {
    total: 0,
    usages: []
}

export async function fetchTotalTraffics({ queryKey }: { queryKey: TotalTrafficsQueryKey }): Promise<TotalTrafficsResponse> {
    // Safe array access with bounds checking to prevent crashes
    const options = queryKey.length > 3 && queryKey[3] ? queryKey[3] : {};
    
    return await fetch(`system/stats/traffic`, {
        query: {
            start: options.start,
            end: options.end
        }
    }).then((result) => {
        return result;
    });
}
export const useTotalTrafficQuery = ({ start, end }: TotalTrafficsQueryOptions) => {
    return useQuery({
        queryKey: ["system", "stats", "traffic", { start, end }],
        queryFn: fetchTotalTraffics,
        refetchInterval: 1000 * 60 * 5, // 60min refresh
        initialData: TotalTrafficsDefault
    })
}
