import { useMemo } from 'react';
import L from 'leaflet';

const STATUS_COLOR: Record<string, string> = {
  en_route:    '#3b82f6',
  collecting:  '#22c55e',
  maintenance: '#ef4444',
  idle:        '#9ca3af',
};

let _iconFixed = false;
function ensureLeafletIcons(): void {
  if (_iconFixed) return;
  delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  });
  _iconFixed = true;
}

export interface UseMarkersResult {
  vehicleIcon: (status: string) => L.DivIcon;
  cpIcon: L.DivIcon;
}

export function useMarkers(): UseMarkersResult {
  ensureLeafletIcons();

  const vehicleIcon = useMemo(
    () => (status: string): L.DivIcon =>
      L.divIcon({
        className: '',
        html: `<div style="width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:15px;background:${STATUS_COLOR[status] ?? STATUS_COLOR.idle};box-shadow:0 2px 8px rgba(0,0,0,.35)">🚛</div>`,
        iconSize:   [30, 30],
        iconAnchor: [15, 15],
      }),
    [],
  );

  const cpIcon = useMemo(
    () =>
      L.divIcon({
        className: '',
        html: `<div style="width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;background:#f59e0b;box-shadow:0 2px 8px rgba(0,0,0,.3)">📍</div>`,
        iconSize:   [26, 26],
        iconAnchor: [13, 13],
      }),
    [],
  );

  return { vehicleIcon, cpIcon };
}
