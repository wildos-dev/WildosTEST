import type { NodeType } from "@wildosvpn/modules/nodes";
import { useQuery } from "@tanstack/react-query";
import { fetch } from "@wildosvpn/common/utils";

type NodeBackendStatsQueryKey = [string, number, string, string];
type NodeAllBackendsStatsQueryKey = [string, number, string];

interface NodeBackendStatsQuery {
    queryKey: NodeBackendStatsQueryKey;
}

interface NodeAllBackendsStatsQuery {
    queryKey: NodeAllBackendsStatsQueryKey;
}

export async function fetchNodeBackendStats({
    queryKey,
}: NodeBackendStatsQuery): Promise<{
    running: boolean;
} | null> {
    return fetch(`nodes/${Number(queryKey[1])}/${queryKey[2]}/stats`)
        .then((stats) => stats)
        .catch(() => null);
}

// Batch API endpoint - fetch all backends stats for a node in one request
export async function fetchNodeAllBackendsStats({
    queryKey,
}: NodeAllBackendsStatsQuery): Promise<Record<string, {
    running: boolean;
}> | null> {
    return fetch(`nodes/${Number(queryKey[1])}/backends/stats`)
        .then((stats) => stats)
        .catch(() => null);
}

export const useBackendStatsQuery = (node: NodeType, backend: string) => {
    const queryKey: NodeBackendStatsQueryKey = [
        "nodes",
        node.id,
        backend,
        "stats",
    ];

    return useQuery({
        queryKey,
        queryFn: fetchNodeBackendStats,
        refetchInterval: 1000 * 5,
        initialData: null,
    });
};

// Hook for batch fetching all backends stats for a node
export const useAllBackendsStatsQuery = (node: NodeType, enabled: boolean = true, jitter: number = 0) => {
    const queryKey: NodeAllBackendsStatsQueryKey = [
        "nodes",
        node.id,
        "all-backends-stats",
    ];

    return useQuery({
        queryKey,
        queryFn: fetchNodeAllBackendsStats,
        refetchInterval: 1000 * (5 + jitter), // Base 5s + jitter for request spreading
        initialData: null,
        enabled,
    });
};
