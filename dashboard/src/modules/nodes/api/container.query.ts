import { useMutation, useQueryClient } from "@tanstack/react-query";
import { fetch } from "@wildosvpn/common/utils";
import { useWidgetQuery, QUERY_INTERVALS } from "@wildosvpn/common/hooks";
import type { NodeType } from "@wildosvpn/modules/nodes";

// Types for container operations
export interface ContainerLog {
    timestamp: string;
    level: string;
    message: string;
    source?: string;
}

export interface ContainerFile {
    name: string;
    type: 'file' | 'directory';
    size?: string; // uint64 as string to prevent overflow
    modified?: string;
    permissions?: string;
}

// API functions
export async function fetchContainerLogs(nodeId: number): Promise<ContainerLog[]> {
    return await fetch(`/nodes/${nodeId}/container/logs?tail=100`);
}

export async function fetchContainerFiles(nodeId: number, path: string): Promise<ContainerFile[]> {
    return await fetch(`/nodes/${nodeId}/container/files`, {
        query: { path }
    });
}

export async function restartContainer(nodeId: number): Promise<boolean> {
    await fetch(`/nodes/${nodeId}/container/restart`, { method: 'POST' });
    return true;
}

// Hooks with enhanced error handling
export const useContainerLogsQuery = (node: NodeType) => {
    return useWidgetQuery(
        ["nodes", node.id, "container", "logs"],
        () => fetchContainerLogs(node.id),
        {
            widgetName: 'Container Logs',
            baseRefetchInterval: QUERY_INTERVALS.REAL_TIME,
            showErrorToast: true,
            errorRetryCount: 3,
            staleTime: 2000, // Logs should be fresh
        }
    );
};

export const useContainerFilesQuery = (node: NodeType, path: string) => {
    return useWidgetQuery(
        ["nodes", node.id, "container", "files", path],
        () => fetchContainerFiles(node.id, path),
        {
            widgetName: 'Container Files',
            baseRefetchInterval: QUERY_INTERVALS.SLOW, // Files don't change often
            showErrorToast: true,
            staleTime: 60000, // 1 minute
        }
    );
};

export const useContainerRestartMutation = (node: NodeType) => {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: () => restartContainer(node.id),
        onSuccess: () => {
            // Invalidate container-related queries
            queryClient.invalidateQueries({ 
                queryKey: ["nodes", node.id, "container"] 
            });
        },
    });
};