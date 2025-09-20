import * as React from 'react';
import { useApiErrorHandler } from './use-api-error-handler';
import { useAuth } from '@wildosvpn/modules/auth';

export enum WebSocketReadyState {
  CONNECTING = 0,
  OPEN = 1,
  CLOSING = 2,
  CLOSED = 3,
}

export interface UseEnhancedWebSocketOptions {
  shouldReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  exponentialBackoff?: boolean;
  maxReconnectInterval?: number;
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onMessage?: (event: MessageEvent) => void;
  onError?: (event: Event) => void;
  onReconnectStop?: (numAttempts: number) => void;
  heartbeatInterval?: number;
  heartbeatMessage?: string;
  protocols?: string | string[];
  enableLogging?: boolean;
  // Security: Auto-inject auth token via Sec-WebSocket-Protocol header (RECOMMENDED)
  // This prevents token exposure in URL query strings and browser history
  injectAuthToken?: boolean;
}

export interface UseEnhancedWebSocketReturn {
  lastMessage: MessageEvent | null;
  readyState: WebSocketReadyState;
  sendMessage: (message: string) => void;
  sendJsonMessage: (jsonMessage: any) => void;
  reconnectCount: number;
  isConnecting: boolean;
  isConnected: boolean;
  lastError: Event | null;
  manualReconnect: () => void;
  disconnect: () => void;
}

export const useEnhancedWebSocket = (
  url: string | null,
  options: UseEnhancedWebSocketOptions = {}
): UseEnhancedWebSocketReturn => {
  const {
    shouldReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 25,
    exponentialBackoff = true,
    maxReconnectInterval = 30000,
    onOpen,
    onClose,
    onMessage,
    onError,
    onReconnectStop,
    heartbeatInterval = 30000,
    heartbeatMessage = 'ping',
    protocols,
    enableLogging = import.meta.env.DEV,
    injectAuthToken = false,
  } = options;

  const { handleError } = useApiErrorHandler({ showToast: false });

  const [lastMessage, setLastMessage] = React.useState<MessageEvent | null>(null);
  const [readyState, setReadyState] = React.useState<WebSocketReadyState>(WebSocketReadyState.CLOSED);
  const [reconnectCount, setReconnectCount] = React.useState(0);
  const [lastError, setLastError] = React.useState<Event | null>(null);

  const websocketRef = React.useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = React.useRef(shouldReconnect);
  const reconnectCountRef = React.useRef(reconnectCount);
  const urlRef = React.useRef(url);

  shouldReconnectRef.current = shouldReconnect;
  reconnectCountRef.current = reconnectCount;
  urlRef.current = url;

  const log = React.useCallback((message: string, data?: any) => {
    if (enableLogging) {
      console.log(`[WebSocket] ${message}`, data || '');
    }
  }, [enableLogging]);

  const clearTimeouts = React.useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
      heartbeatTimeoutRef.current = null;
    }
  }, []);

  const calculateReconnectDelay = React.useCallback((attempt: number): number => {
    if (!exponentialBackoff) {
      return reconnectInterval;
    }

    const delay = Math.min(
      reconnectInterval * Math.pow(2, attempt),
      maxReconnectInterval
    );
    
    // Add jitter to prevent thundering herd
    const jitter = Math.random() * 0.3 * delay;
    return delay + jitter;
  }, [exponentialBackoff, reconnectInterval, maxReconnectInterval]);

  const startHeartbeat = React.useCallback(() => {
    if (heartbeatInterval <= 0) return;

    // Безопасная очистка timeout - избегаем temporal dead zone
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
    }
    heartbeatTimeoutRef.current = setTimeout(() => {
      if (websocketRef.current?.readyState === WebSocket.OPEN) {
        websocketRef.current.send(heartbeatMessage);
        log('Heartbeat sent');
        startHeartbeat();
      }
    }, heartbeatInterval);
  }, [heartbeatInterval, heartbeatMessage, log]);

  const connect = React.useCallback(() => {
    if (!urlRef.current) {
      log('No URL provided, cannot connect');
      return;
    }

    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      log('Already connected');
      return;
    }

    try {
      log(`Connecting to ${urlRef.current}`);
      setReadyState(WebSocketReadyState.CONNECTING);
      
      // Create secure protocols array with auth token if needed
      let secureProtocols = protocols;
      if (injectAuthToken) {
        const token = useAuth.getState().getAuthToken();
        if (token) {
          // Use Sec-WebSocket-Protocol header for secure token transmission
          // This prevents token exposure in URL query strings and browser history
          const authProtocol = `bearer.${token}`;
          secureProtocols = Array.isArray(protocols) 
            ? [...protocols, authProtocol]
            : protocols 
              ? [protocols, authProtocol]
              : [authProtocol];
          log('Auth token injected via Sec-WebSocket-Protocol header');
        } else {
          log('Warning: injectAuthToken=true but no auth token available');
        }
      }
      
      websocketRef.current = new WebSocket(urlRef.current, secureProtocols);

      websocketRef.current.onopen = (event) => {
        log('Connection opened');
        setReadyState(WebSocketReadyState.OPEN);
        setReconnectCount(0);
        setLastError(null);
        reconnectCountRef.current = 0;
        startHeartbeat();
        onOpen?.(event);
      };

      websocketRef.current.onmessage = (event) => {
        setLastMessage(event);
        onMessage?.(event);
      };

      websocketRef.current.onclose = (event) => {
        log(`Connection closed: ${event.code} - ${event.reason}`);
        setReadyState(WebSocketReadyState.CLOSED);
        clearTimeouts();
        onClose?.(event);

        // Auto-reconnect logic
        if (shouldReconnectRef.current && reconnectCountRef.current < maxReconnectAttempts) {
          const delay = calculateReconnectDelay(reconnectCountRef.current);
          log(`Reconnecting in ${delay}ms (attempt ${reconnectCountRef.current + 1}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectCount(prev => {
              const newCount = prev + 1;
              reconnectCountRef.current = newCount;
              return newCount;
            });
            connect();
          }, delay);
        } else if (reconnectCountRef.current >= maxReconnectAttempts) {
          log(`Max reconnect attempts (${maxReconnectAttempts}) reached`);
          onReconnectStop?.(reconnectCountRef.current);
        }
      };

      websocketRef.current.onerror = (event) => {
        log('Connection error');
        setLastError(event);
        handleError(new Error('WebSocket connection error'), 'WebSocket');
        onError?.(event);
      };

    } catch (error) {
      log('Failed to create WebSocket connection', error);
      handleError(error as Error, 'WebSocket Connection');
    }
  }, [
    protocols, onOpen, onMessage, onClose, onError, onReconnectStop,
    maxReconnectAttempts, calculateReconnectDelay, startHeartbeat,
    clearTimeouts, log, handleError
  ]);

  const disconnect = React.useCallback(() => {
    log('Manually disconnecting');
    shouldReconnectRef.current = false;
    clearTimeouts();
    
    if (websocketRef.current) {
      if (websocketRef.current.readyState === WebSocket.OPEN) {
        setReadyState(WebSocketReadyState.CLOSING);
        websocketRef.current.close(1000, 'Manual disconnect');
      } else {
        setReadyState(WebSocketReadyState.CLOSED);
      }
    }
  }, [clearTimeouts, log]);

  const manualReconnect = React.useCallback(() => {
    log('Manual reconnect requested');
    shouldReconnectRef.current = true;
    setReconnectCount(0);
    reconnectCountRef.current = 0;
    disconnect();
    setTimeout(connect, 100);
  }, [connect, disconnect, log]);

  const sendMessage = React.useCallback((message: string) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(message);
      log('Message sent', message);
    } else {
      log('Cannot send message: WebSocket is not open');
      handleError(new Error('WebSocket is not connected'), 'Send Message');
    }
  }, [log, handleError]);

  const sendJsonMessage = React.useCallback((jsonMessage: any) => {
    try {
      const message = JSON.stringify(jsonMessage);
      sendMessage(message);
    } catch (error) {
      log('Failed to stringify JSON message', error);
      handleError(error as Error, 'Send JSON Message');
    }
  }, [sendMessage, log, handleError]);

  // Initial connection
  React.useEffect(() => {
    if (url) {
      connect();
    }
    
    return () => {
      shouldReconnectRef.current = false;
      clearTimeouts();
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, [url]); // Reconnect when URL changes

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      shouldReconnectRef.current = false;
      clearTimeouts();
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, [clearTimeouts]);

  return {
    lastMessage,
    readyState,
    sendMessage,
    sendJsonMessage,
    reconnectCount,
    isConnecting: readyState === WebSocketReadyState.CONNECTING,
    isConnected: readyState === WebSocketReadyState.OPEN,
    lastError,
    manualReconnect,
    disconnect,
  };
};