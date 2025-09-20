import { useQuery } from "@tanstack/react-query";
import { fetch } from "@wildosvpn/common/utils";

export interface NodesStatsResponse {
    total: number;
    healthy: number;
    unhealthy: number;
}

export const NodesStatsDefault = {
    total: 0,
    healthy: 0,
    unhealthy: 0,
}

export async function fetchNodesStats(): Promise<NodesStatsResponse> {
    return await fetch(`system/stats/nodes`).then((result) => {
        return result;
    });
}

export const NodesStatsQueryFetchKey = "nodes-stats";

export const useNodesStatsQuery = () => {
    return useQuery({
        queryKey: [NodesStatsQueryFetchKey],
        queryFn: fetchNodesStats,
        initialData: NodesStatsDefault
    })
}