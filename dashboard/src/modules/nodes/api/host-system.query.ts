import { useQuery } from "@tanstack/react-query";
import { fetch } from "@wildosvpn/common/utils";
import type { NodeType } from "@wildosvpn/modules/nodes";

// Types for host system metrics
export interface HostSystemMetrics {
    cpu: {
        usage: number;
        loadAverage: [number, number, number]; // 1, 5, 15 min averages
    };
    memory: {
        total: string; // uint64 as string to prevent overflow
        used: string; // uint64 as string to prevent overflow
        available: string; // uint64 as string to prevent overflow
        usagePercent: number;
    };
    disk: {
        rootUsagePercent: number;
        partitions: Array<{
            device: string;
            mountPoint: string;
            total: string; // uint64 as string to prevent overflow
            used: string; // uint64 as string to prevent overflow
            available: string; // uint64 as string to prevent overflow;
            usagePercent: number;
        }>;
    };
    network: {
        interfaces: Array<{
            name: string;
            ip: string;
            rxBytes: string; // uint64 as string to prevent overflow
            txBytes: string; // uint64 as string to prevent overflow;
            speed: string;
        }>;
    };
    uptime: {
        seconds: number;
        formatted: string;
    };
    openPorts: Array<{
        number: number;
        protocol: string;
        service?: string;
    }>;
}

// API function to fetch host system metrics
export async function fetchHostSystemMetrics(nodeId: number): Promise<HostSystemMetrics | null> {
    try {
        return await fetch(`/nodes/${nodeId}/host/metrics`);
    } catch (error) {
        console.error('Failed to fetch host system metrics:', error);
        return null;
    }
}

// Hook for fetching host system metrics
export const useHostSystemMetricsQuery = (node: NodeType) => {
    return useQuery({
        queryKey: ["nodes", node.id, "host", "metrics"],
        queryFn: () => fetchHostSystemMetrics(node.id),
        refetchInterval: 15000, // 15 seconds
        initialData: null,
    });
};