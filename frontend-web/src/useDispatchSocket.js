// useDispatchSocket.js
//
// A custom React hook that opens a WebSocket connection to the FastAPI
// backend and keeps a running list of live dispatch updates in state.
// Implements auto-reconnect with exponential backoff so the UI stays
// resilient even if the backend restarts.

import { useEffect, useRef, useState, useCallback } from 'react';

const INITIAL_RETRY_DELAY = 1500; // ms
const MAX_RETRY_DELAY = 30000;    // ms cap

export function useDispatchSocket(url) {
  // `dispatches` — every DispatchUpdate message received since mount.
  const [dispatches, setDispatches] = useState([]);

  // Connection state: 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error'
  const [connectionStatus, setConnectionStatus] = useState('connecting');

  const socketRef   = useRef(null);
  const retryDelay  = useRef(INITIAL_RETRY_DELAY);
  const retryTimer  = useRef(null);
  const unmounted   = useRef(false);

  useEffect(() => {
    unmounted.current = false;

    function connect() {
      if (unmounted.current) return;

      setConnectionStatus((prev) => (prev === 'connected' ? 'reconnecting' : 'connecting'));

      const socket = new WebSocket(url);
      socketRef.current = socket;

      socket.onopen = () => {
        if (unmounted.current) { socket.close(); return; }
        setConnectionStatus('connected');
        retryDelay.current = INITIAL_RETRY_DELAY; // reset backoff on success
      };

      socket.onmessage = (event) => {
        if (unmounted.current) return;
        try {
          const update = JSON.parse(event.data);
          // Prepend newest dispatch so it always appears at the top of any feed.
          setDispatches((prev) => [update, ...prev]);
        } catch (e) {
          console.error('[useDispatchSocket] Failed to parse message:', e);
        }
      };

      socket.onclose = () => {
        if (unmounted.current) return;
        setConnectionStatus('disconnected');
        // Auto-reconnect with exponential backoff.
        retryTimer.current = setTimeout(() => {
          retryDelay.current = Math.min(retryDelay.current * 2, MAX_RETRY_DELAY);
          if (socketRef.current) connect();
        }, retryDelay.current);
      };

      socket.onerror = () => {
        if (unmounted.current) return;
        setConnectionStatus('error');
        // onclose fires after onerror, which will trigger the reconnect.
      };
    }

    connect();

    return () => {
      unmounted.current = true;
      clearTimeout(retryTimer.current);
      if (socketRef.current) {
        // Prevent onclose from scheduling another reconnect during cleanup.
        socketRef.current.onclose = null;
        socketRef.current.close();
      }
    };
  }, [url]);

  // Expose a manual clear function for the UI (e.g. a "Clear feed" button).
  const clearDispatches = useCallback(() => setDispatches([]), []);

  return { dispatches, connectionStatus, clearDispatches };
}

