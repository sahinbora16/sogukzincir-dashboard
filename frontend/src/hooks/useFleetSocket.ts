import { useEffect, useRef } from 'react';
import { useDashboardStore } from '../store';
import type { WsMessage } from '../types';

const WS_URL = (import.meta.env.VITE_WS_URL as string | undefined) ?? 'ws://localhost:8000/ws/fleet';

export function useFleetSocket() {
  const { updateVehicle, updateTank, setWsConnected } = useDashboardStore();
  const wsRef = useRef<WebSocket | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    function connect() {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => setWsConnected(true);

      ws.onmessage = (event: MessageEvent<string>) => {
        const msg = JSON.parse(event.data) as WsMessage;
        if (msg.type === 'fleet_update') {
          updateVehicle(msg.data as Parameters<typeof updateVehicle>[0]);
        } else if (msg.type === 'tank_update') {
          updateTank(msg.data as Parameters<typeof updateTank>[0]);
        }
      };

      ws.onclose = () => {
        setWsConnected(false);
        timerRef.current = setTimeout(connect, 3000);
      };

      ws.onerror = () => ws.close();
    }

    connect();

    return () => {
      wsRef.current?.close();
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}
