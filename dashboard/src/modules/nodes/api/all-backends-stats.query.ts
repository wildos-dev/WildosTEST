import { useQuery } from "@tanstack/react-query";
import { fetch } from "@wildosvpn/common/utils";

export interface AllBackendsStatsResponse {
    totalBackends: number;
    runningBackends: number;
    stoppedBackends: number;
    totalNodes: number;
    nodesWithData: number;
}

export const AllBackendsStatsDefault: AllBackendsStatsResponse = {
    totalBackends: 0,
    runningBackends: 0,
    stoppedBackends: 0,
    totalNodes: 0,
    nodesWithData: 0,
}

// First, get list of all nodes
async function fetchAllNodes() {
    return await fetch('nodes', { 
        query: { page: 1, size: 1000 } // Get all nodes
    }).then((result) => {
        return result.items || [];
    });
}

// Then get backend stats for all nodes
export async function fetchAllBackendsStats(): Promise<AllBackendsStatsResponse> {
    try {
        const nodes = await fetchAllNodes();
        
        if (!nodes || nodes.length === 0) {
            return AllBackendsStatsDefault;
        }

        // Fetch backend stats for all nodes in parallel
        const backendStatsPromises = nodes.map(async (node: any) => {
            try {
                const stats = await fetch(`nodes/${node.id}/backends/stats`);
                return { nodeId: node.id, stats };
            } catch (error) {
                return { nodeId: node.id, stats: null };
            }
        });

        const allBackendStats = await Promise.all(backendStatsPromises);
        
        // Aggregate the stats
        let totalBackends = 0;
        let runningBackends = 0;
        let nodesWithData = 0;

        allBackendStats.forEach(({ stats }) => {
            if (stats && typeof stats === 'object') {
                nodesWithData++;
                Object.values(stats).forEach((backendStat: any) => {
                    totalBackends++;
                    if (backendStat?.running === true) {
                        runningBackends++;
                    }
                });
            }
        });

        return {
            totalBackends,
            runningBackends,
            stoppedBackends: totalBackends - runningBackends,
            totalNodes: nodes.length,
            nodesWithData,
        };
    } catch (error) {
        console.error('Failed to fetch all backends stats:', error);
        return AllBackendsStatsDefault;
    }
}

export const AllBackendsStatsQueryFetchKey = "all-backends-stats";

export const useAllBackendsStatsQuery = () => {
    return useQuery({
        queryKey: [AllBackendsStatsQueryFetchKey],
        queryFn: fetchAllBackendsStats,
        initialData: AllBackendsStatsDefault,
        refetchInterval: 1000 * 10, // Refresh every 10 seconds
    })
}