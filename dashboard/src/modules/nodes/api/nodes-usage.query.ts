import { useQuery } from "@tanstack/react-query";
import { fetch } from "@wildosvpn/common/utils";

export type UsageMetric = number[];

export interface NodesUsageResponse {
    usages: Array<UsageMetric>;
    total: number;
}

export interface NodesUsageQueryOptions {
    nodeId: number;
    start: string;
    end: string;
}

export type NodesUsageQueryKey = [string, number, string, { start?: string, end?: string }]

export const NodesUsageDefault = {
    total: 0,
    usages: []
}

export async function fetchNodesUsage({ queryKey }: { queryKey: NodesUsageQueryKey }): Promise<NodesUsageResponse> {
    const [, nodeId,, range] = queryKey;
    const safeId = Number.isFinite(nodeId) ? nodeId : 0;
    return await fetch(`/nodes/${safeId}/usage`, {
        query: {
            start: range?.start ?? "",
            end: range?.end ?? ""
        }
    }).then((result) => {
        return result;
    });
}
export const useNodesUsageQuery = ({ nodeId, start, end }: NodesUsageQueryOptions) => {
    return useQuery({
        queryKey: ["nodes", nodeId, "usage", { start, end }],
        queryFn: fetchNodesUsage,
        refetchInterval: 1000 * 60 * 5, // 60min refresh
        initialData: NodesUsageDefault
    })
}
