import { NodeType } from "@wildosvpn/modules/nodes";
import { useEnhancedWebSocket, WebSocketReadyState } from "@wildosvpn/common/hooks/use-enhanced-websocket";
import { joinPaths } from "@tanstack/react-router";
import * as React from "react";

export const MAX_NUMBER_OF_LOGS = 200;

export const getStatus = (status: WebSocketReadyState) => {
    return {
        [WebSocketReadyState.CONNECTING]: "connecting",
        [WebSocketReadyState.OPEN]: "connected",
        [WebSocketReadyState.CLOSING]: "closed",
        [WebSocketReadyState.CLOSED]: "closed",
    }[status] || "closed";
};

export const getWebsocketUrl = (nodeId: number, backend: string) => {
    try {
        // Получаем базовый API URL, используя fallback для Docker
        const baseApiUrl = import.meta.env.VITE_BASE_API || window.location.origin;
        
        let fullApiUrl: string;
        if (baseApiUrl.startsWith("/")) {
            // Относительный путь - добавляем origin
            fullApiUrl = window.location.origin + baseApiUrl;
        } else if (baseApiUrl.startsWith("http")) {
            // Полный URL
            fullApiUrl = baseApiUrl;
        } else {
            // Fallback для Docker - используем текущий origin
            fullApiUrl = window.location.origin;
        }
        
        const baseURL = new URL(fullApiUrl);
        const scheme = baseURL.protocol === "https:" ? "wss" : "ws";
        const websocketPath = joinPaths([baseURL.pathname, `/nodes/${nodeId}/${backend}/logs`]);
        // SECURITY: Removed token from URL query string to prevent token exposure in logs/history
        // Auth token is now injected securely via Sec-WebSocket-Protocol header
        return `${scheme}://${baseURL.host}${websocketPath}?interval=1`;
    } catch (e) {
        console.error("Unable to generate websocket url");
        console.error(e);
        // Fallback для Docker окружения с сохранением base path
        const basePath = (import.meta.env.VITE_BASE_API || '').startsWith('/') ? import.meta.env.VITE_BASE_API : '';
        const scheme = window.location.protocol === "https:" ? "wss" : "ws";
        // SECURITY: Removed token from URL query string to prevent token exposure in logs/history
        return `${scheme}://${window.location.host}${basePath}/nodes/${nodeId}/${backend}/logs?interval=1`;
    }
};

export const useNodesLog = (node: NodeType, backend: string) => {
    const [logs, setLogs] = React.useState<string[]>([]);
    const logsDiv = React.useRef<HTMLDivElement | null>(null);
    const scrollShouldStayOnEnd = React.useRef(true);

    const updateLogs = React.useCallback(
        (callback: (prevLogs: string[]) => string[]) => {
            setLogs((prevLogs) => {
                const newLogs = callback(prevLogs);
                return newLogs.length > MAX_NUMBER_OF_LOGS
                    ? newLogs.slice(-MAX_NUMBER_OF_LOGS)
                    : newLogs;
            });
        },
        [],
    );

    // Use enhanced WebSocket with secure auth token injection
    const { readyState } = useEnhancedWebSocket(
        node?.id ? getWebsocketUrl(node.id, backend) : null,
        {
            onMessage: (e: MessageEvent) => {
                updateLogs((prevLogs) => [...prevLogs, e.data]);
            },
            shouldReconnect: true,
            maxReconnectAttempts: 10,
            reconnectInterval: 1000,
            // SECURITY: Inject auth token securely via Sec-WebSocket-Protocol header
            // This prevents token exposure in URL query strings and browser history
            injectAuthToken: true,
            enableLogging: import.meta.env.DEV,
        },
    );

    React.useEffect(() => {
        if (logsDiv.current && scrollShouldStayOnEnd.current) {
            logsDiv.current.scrollTop = logsDiv.current.scrollHeight;
        }
    }, [logs]);

    React.useEffect(() => {
        return () => {
            setLogs([]);
        };
    }, []);

    const status = getStatus(readyState);

    return { status, readyState, logs, logsDiv };
}; 
