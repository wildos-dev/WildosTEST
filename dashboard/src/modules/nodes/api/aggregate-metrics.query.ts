import { useQueries } from "@tanstack/react-query";
import { fetch } from "@wildosvpn/common/utils";
import { useApiErrorHandler, QUERY_INTERVALS } from "@wildosvpn/common/hooks";
import type { NodeType } from "@wildosvpn/modules/nodes";
import type { HostSystemMetrics } from "./host-system.query";
import type { PeakEvent } from "./peak-events.query";
import { useNodesQuery } from "./nodes.query";

// Aggregate types for multi-node data
export interface AggregateHostSystemMetrics {
    totalNodes: number;
    activeNodes: number;
    averageCpuUsage: number;
    averageMemoryUsage: number;
    averageDiskUsage: number;
    totalNetworkRx: string;
    totalNetworkTx: string;
    criticalNodes: number; // nodes with >80% resource usage
    healthyNodes: number;
}

export interface TopUsageNode {
    nodeId: number;
    nodeName: string;
    totalTraffic: number; // in bytes
    uplink: number;
    downlink: number;
    usagePercent: number;
}

export interface NetworkActivity {
    totalRxBytes: string;
    totalTxBytes: string;
    activeInterfaces: number;
    averageSpeed: string;
    timestamp: number;
}

// Helper function to get all nodes
export const useAllNodesQuery = () => {
    return useNodesQuery({ 
        page: 1, 
        size: 1000, // Get all nodes 
        sortBy: "created_at", 
        desc: false 
    });
};

// Aggregate Host System Metrics across all nodes
export const useAggregateHostSystemMetricsQuery = () => {
    const { data: nodesData } = useAllNodesQuery();
    const nodes = nodesData?.entities || [];
    const { handleError } = useApiErrorHandler({ showToast: false });
    
    // Fetch host metrics for all nodes
    const hostMetricsQueries = useQueries({
        queries: nodes.map((node: NodeType) => ({
            queryKey: ["nodes", node.id, "host", "metrics"],
            queryFn: async (): Promise<HostSystemMetrics | null> => {
                try {
                    return await fetch(`/nodes/${node.id}/host/metrics`);
                } catch (error) {
                    handleError(error, `Host metrics for node ${node.name || node.id}`);
                    return null;
                }
            },
            refetchInterval: QUERY_INTERVALS.FREQUENT, // 15 seconds
            initialData: null,
        })),
    });

    const aggregateData: AggregateHostSystemMetrics = {
        totalNodes: nodes.length,
        activeNodes: 0,
        averageCpuUsage: 0,
        averageMemoryUsage: 0,
        averageDiskUsage: 0,
        totalNetworkRx: "0",
        totalNetworkTx: "0",
        criticalNodes: 0,
        healthyNodes: 0,
    };

    if (hostMetricsQueries.length > 0) {
        const validMetrics = hostMetricsQueries
            .map(query => query.data)
            .filter((data): data is HostSystemMetrics => data !== null);

        if (validMetrics.length > 0) {
            aggregateData.activeNodes = validMetrics.length;
            
            // Calculate averages
            aggregateData.averageCpuUsage = 
                validMetrics.reduce((sum, metrics) => sum + (metrics?.cpu?.usage || 0), 0) / validMetrics.length;
            
            aggregateData.averageMemoryUsage = 
                validMetrics.reduce((sum, metrics) => sum + (metrics?.memory?.usagePercent || 0), 0) / validMetrics.length;
            
            aggregateData.averageDiskUsage = 
                validMetrics.reduce((sum, metrics) => sum + (metrics?.disk?.rootUsagePercent || 0), 0) / validMetrics.length;

            // Calculate totals for network
            let totalRx = 0;
            let totalTx = 0;
            
            validMetrics.forEach(metrics => {
                if (metrics?.network?.interfaces && Array.isArray(metrics.network.interfaces)) {
                    metrics.network.interfaces.forEach(iface => {
                        if (iface) {
                            totalRx += parseInt(iface.rxBytes) || 0;
                            totalTx += parseInt(iface.txBytes) || 0;
                        }
                    });
                }
            });
            
            aggregateData.totalNetworkRx = totalRx.toString();
            aggregateData.totalNetworkTx = totalTx.toString();

            // Count critical and healthy nodes
            validMetrics.forEach(metrics => {
                if (metrics?.cpu && metrics?.memory && metrics?.disk) {
                    const isCritical = (metrics.cpu.usage || 0) > 80 || 
                                     (metrics.memory.usagePercent || 0) > 80 || 
                                     (metrics.disk.rootUsagePercent || 0) > 80;
                    
                    if (isCritical) {
                        aggregateData.criticalNodes++;
                    } else {
                        aggregateData.healthyNodes++;
                    }
                }
            });
        }
    }

    return {
        data: aggregateData,
        isLoading: hostMetricsQueries.some(query => query.isLoading),
        error: hostMetricsQueries.find(query => query.error)?.error || null
    };
};

// Aggregate Peak Events from all nodes
export const useAggregatePeakEventsQuery = (hoursBack: number = 24) => {
    const { data: nodesData } = useAllNodesQuery();
    const nodes = nodesData?.entities || [];
    const since_ms = Date.now() - (hoursBack * 60 * 60 * 1000);
    const { handleError } = useApiErrorHandler({ showToast: false });
    
    // Fetch peak events for all nodes
    const peakEventsQueries = useQueries({
        queries: nodes.map((node: NodeType) => ({
            queryKey: ["nodes", node.id, "peak", "events", since_ms],
            queryFn: async (): Promise<PeakEvent[]> => {
                try {
                    const params = new URLSearchParams();
                    params.append('since_ms', since_ms.toString());
                    
                    const url = `/nodes/${node.id}/peak/events?${params.toString()}`;
                    return await fetch(url);
                } catch (error) {
                    handleError(error, `Peak events for node ${node.name || node.id}`);
                    return [];
                }
            },
            refetchInterval: QUERY_INTERVALS.NORMAL, // 30 seconds
            initialData: [],
        })),
    });

    // Combine and sort all events
    const allEvents = peakEventsQueries
        .flatMap(query => query.data || [])
        .sort((a, b) => b.started_at_ms - a.started_at_ms)
        .slice(0, 50); // Keep latest 50 events

    return {
        data: allEvents,
        isLoading: peakEventsQueries.some(query => query.isLoading),
        error: peakEventsQueries.find(query => query.error)?.error || null
    };
};

// Top Usage Nodes Query
export const useTopUsageNodesQuery = (topCount: number = 5) => {
    const { data: nodesData } = useAllNodesQuery();
    const nodes = nodesData?.entities || [];
    const { handleError } = useApiErrorHandler({ showToast: false });
    
    // Get usage for last 24 hours
    const now = new Date();
    const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    
    const usageQueries = useQueries({
        queries: nodes.map((node: NodeType) => ({
            queryKey: ["nodes", node.id, "usage", { 
                start: yesterday.toISOString(), 
                end: now.toISOString() 
            }],
            queryFn: async () => {
                try {
                    return await fetch(`/nodes/${node.id}/usage`, {
                        query: {
                            start: yesterday.toISOString(),
                            end: now.toISOString()
                        }
                    });
                } catch (error) {
                    handleError(error, `Usage data for node ${node.name || node.id}`);
                    return { total: 0, usages: [] };
                }
            },
            refetchInterval: QUERY_INTERVALS.SLOW, // 1 minute - less frequent for usage data
            initialData: { total: 0, usages: [] },
        })),
    });

    const topUsageNodes: TopUsageNode[] = usageQueries
        .map((query, index) => {
            const node = nodes[index];
            if (!node) return null;
            
            const usage = query.data?.total || 0;
            
            return {
                nodeId: node.id || 0,
                nodeName: node.name || `Node ${index + 1}`,
                totalTraffic: usage,
                uplink: node.uplink || 0,
                downlink: node.downlink || 0,
                usagePercent: 0 // Will be calculated after getting max
            };
        })
        .filter((node): node is TopUsageNode => node !== null)
        .sort((a, b) => b.totalTraffic - a.totalTraffic)
        .slice(0, topCount);

    // Calculate usage percentages based on top node
    const maxTraffic = topUsageNodes[0]?.totalTraffic || 1;
    topUsageNodes.forEach(node => {
        node.usagePercent = (node.totalTraffic / maxTraffic) * 100;
    });

    return {
        data: topUsageNodes,
        isLoading: usageQueries.some(query => query.isLoading),
        error: usageQueries.find(query => query.error)?.error || null
    };
};

// Network Activity aggregated from host metrics
export const useNetworkActivityQuery = () => {
    const { data: metricsData, isLoading, error } = useAggregateHostSystemMetricsQuery();
    
    const networkActivity: NetworkActivity = {
        totalRxBytes: metricsData?.totalNetworkRx || "0",
        totalTxBytes: metricsData?.totalNetworkTx || "0",
        activeInterfaces: (metricsData?.activeNodes || 0) * 2, // Approximate
        averageSpeed: "1000", // Default to 1Gbps
        timestamp: Date.now(),
    };

    return {
        data: networkActivity,
        isLoading,
        error
    };
};