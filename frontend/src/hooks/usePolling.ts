import { useEffect } from 'react';
import { useDashboardStore } from '../store';
import type { Vehicle, StorageTank, Alert } from '../types';

const API = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000';

export function usePolling(intervalMs = 10_000) {
  const { setVehicles, setTanks, setAlerts } = useDashboardStore();

  useEffect(() => {
    async function fetchAll() {
      try {
        const [vRes, tRes, aRes] = await Promise.all([
          fetch(`${API}/api/fleet/`),
          fetch(`${API}/api/tanks/`),
          fetch(`${API}/api/alerts/?resolved=false`),
        ]);
        const [vehicles, tanks, alerts]: [Vehicle[], StorageTank[], Alert[]] =
          await Promise.all([vRes.json(), tRes.json(), aRes.json()]);
        setVehicles(vehicles);
        setTanks(tanks);
        setAlerts(alerts);
      } catch (err) {
        console.error('Polling error:', err);
      }
    }

    fetchAll();
    const id = setInterval(fetchAll, intervalMs);
    return () => clearInterval(id);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs]);
}
