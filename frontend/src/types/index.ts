export interface Vehicle {
  id: number;
  vehicle_id: string;
  driver_name: string;
  status: 'idle' | 'en_route' | 'collecting' | 'maintenance';
  current_lat: number;
  current_lng: number;
  speed: number;
  temperature: number;
  load_level: number;
  capacity: number;
  collection_started_at: string | null;
  last_updated: string;
}

export interface StorageTank {
  id: number;
  name: string;
  lat: number;
  lng: number;
  capacity: number;
  current_level: number;
  temperature: number;
  last_updated: string;
  collection_point_id?: number;
}

export interface CollectionPoint {
  id: number;
  name: string;
  lat: number;
  lng: number;
  address?: string;
  status: string;
}

export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';
export type AlertType = 'HIGH_RISK' | 'MEDIUM_RISK' | 'tank_overflow' | 'low_tank' | 'temperature';

export interface Alert {
  id: number;
  alert_type: AlertType | string;
  severity: AlertSeverity;
  message: string;
  entity_id?: number;
  entity_type?: string;
  resolved: boolean;
  created_at: string;
  resolved_at?: string;
}

export interface WsMessage {
  type: 'fleet_update' | 'tank_update' | 'alert';
  data: unknown;
}

/** Bk = t * exp(0.1 * T) — mirrors backend utils.calculate_spoilage */
export function calculateSpoilage(t: number, T: number): number {
  return t * Math.exp(0.1 * T);
}

/** Elapsed hours since collection started, or null if not collecting */
export function elapsedHours(collectionStartedAt: string | null): number | null {
  if (!collectionStartedAt) return null;
  return (Date.now() - new Date(collectionStartedAt).getTime()) / 3_600_000;
}
