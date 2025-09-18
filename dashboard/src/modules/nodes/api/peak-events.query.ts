import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetch } from "@wildosvpn/common/utils";
import type { NodeType } from "@wildosvpn/modules/nodes";
import * as React from "react";

// Types for Peak Events
export interface PeakEvent {
    node_id: number;
    category: 'CPU' | 'MEMORY' | 'DISK' | 'NETWORK' | 'BACKEND';
    level: 'HIGH' | 'CRITICAL';
    value: number;
    threshold: number;
    started_at_ms: number;
    resolved_at_ms?: number;
    metric: string;
    dedupe_key: string;
    context_json: Record<string, any>;
    seq: number;
}

// API functions
export async function fetchPeakEvents(
    nodeId: number, 
    since_ms: number = 0, 
    category?: string
): Promise<PeakEvent[]> {
    try {
        const params = new URLSearchParams();
        if (since_ms > 0) params.append('since_ms', since_ms.toString());
        if (category) params.append('category', category);
        
        const queryString = params.toString();
        const url = `/nodes/${nodeId}/peak/events${queryString ? '?' + queryString : ''}`;
        
        return await fetch(url);
    } catch (error) {
        console.error('Failed to fetch peak events:', error);
        return [];
    }
}

// React Query hooks
export const usePeakEventsQuery = (
    node: NodeType, 
    since_ms: number = 0, 
    category?: string
) => {
    return useQuery({
        queryKey: ["nodes", node.id, "peak", "events", since_ms, category],
        queryFn: () => fetchPeakEvents(node.id, since_ms, category),
        refetchInterval: 30000, // 30 seconds - less frequent than real-time metrics
        initialData: [],
    });
};

// Real-time Peak Events WebSocket Hook
export const usePeakEventsStream = (node: NodeType) => {
    const [events, setEvents] = React.useState<PeakEvent[]>([]);
    const [isConnected, setIsConnected] = React.useState(false);
    const [error, setError] = React.useState<string | null>(null);
    const wsRef = React.useRef<WebSocket | null>(null);
    const queryClient = useQueryClient();

    React.useEffect(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/nodes/${node.id}/peak/events/stream`;
        
        const connectWebSocket = () => {
            try {
                wsRef.current = new WebSocket(wsUrl);
                
                wsRef.current.onopen = () => {
                    setIsConnected(true);
                    setError(null);
                    console.log(`Peak Events WebSocket connected for node ${node.id}`);
                };
                
                wsRef.current.onmessage = (event) => {
                    try {
                        const peakEvent: PeakEvent = JSON.parse(event.data);
                        setEvents(prev => [peakEvent, ...prev.slice(0, 99)]); // Keep last 100 events
                        
                        // Invalidate peak events queries to refresh historical data
                        queryClient.invalidateQueries({ 
                            queryKey: ["nodes", node.id, "peak", "events"] 
                        });
                    } catch (err) {
                        console.error('Failed to parse peak event:', err);
                    }
                };
                
                wsRef.current.onclose = (event) => {
                    setIsConnected(false);
                    console.log(`Peak Events WebSocket closed for node ${node.id}:`, event.code, event.reason);
                    
                    // Attempt to reconnect after delay (unless manually closed)
                    if (event.code !== 1000) {
                        setTimeout(connectWebSocket, 5000);
                    }
                };
                
                wsRef.current.onerror = (err) => {
                    setError('WebSocket connection failed');
                    setIsConnected(false);
                    console.error(`Peak Events WebSocket error for node ${node.id}:`, err);
                };
                
            } catch (err) {
                setError('Failed to create WebSocket connection');
                console.error('WebSocket creation failed:', err);
            }
        };

        connectWebSocket();

        // Cleanup on unmount
        return () => {
            if (wsRef.current) {
                wsRef.current.close(1000, 'Component unmounted');
            }
        };
    }, [node.id, queryClient]);

    const clearEvents = () => setEvents([]);

    return {
        events,
        isConnected,
        error,
        clearEvents
    };
};

// Helper hook for recent peak events (last 24 hours)
export const useRecentPeakEventsQuery = (node: NodeType) => {
    const last24Hours = Date.now() - (24 * 60 * 60 * 1000);
    return usePeakEventsQuery(node, last24Hours);
};

// Helper hook for specific category events
export const useCategoryPeakEventsQuery = (
    node: NodeType, 
    category: 'CPU' | 'MEMORY' | 'DISK' | 'NETWORK' | 'BACKEND'
) => {
    const last24Hours = Date.now() - (24 * 60 * 60 * 1000);
    return usePeakEventsQuery(node, last24Hours, category);
};