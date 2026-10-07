import React, { createContext, useContext, useEffect, useState, useRef } from 'react';

const WebSocketContext = createContext(null);

export function WebSocketProvider({ children }) {
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState(null);
  const wsRef = useRef(null);
  const listenersRef = useRef(new Map());

  useEffect(() => {
    let reconnectTimeout = null;

    function connect() {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/live`;

      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setLastEvent(data);

            // Notify registered event listeners
            if (data.event && listenersRef.current.has(data.event)) {
              listenersRef.current.get(data.event).forEach((cb) => cb(data));
            }
            if (listenersRef.current.has('*')) {
              listenersRef.current.get('*').forEach((cb) => cb(data));
            }
          } catch {
            // non-json message ignored
          }
        };

        ws.onclose = () => {
          setConnected(false);
          // Reconnect after 3 seconds
          reconnectTimeout = setTimeout(connect, 3000);
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch {
        reconnectTimeout = setTimeout(connect, 4000);
      }
    }

    connect();

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const subscribe = (eventName, callback) => {
    if (!listenersRef.current.has(eventName)) {
      listenersRef.current.set(eventName, new Set());
    }
    listenersRef.current.get(eventName).add(callback);

    return () => {
      if (listenersRef.current.has(eventName)) {
        listenersRef.current.get(eventName).delete(callback);
      }
    };
  };

  const value = {
    connected,
    lastEvent,
    subscribe
  };

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>;
}

export function useWebSocket() {
  const ctx = useContext(WebSocketContext);
  if (!ctx) throw new Error('useWebSocket must be used within WebSocketProvider');
  return ctx;
}
