import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import type { Vehicle, CollectionPoint } from '../types';
import { useMarkers } from '../hooks/useMarkers';

interface FleetMapProps {
  vehicles: Vehicle[];
  collectionPoints: CollectionPoint[];
}

export function FleetMap({ vehicles, collectionPoints }: FleetMapProps) {
  const { vehicleIcon, cpIcon } = useMarkers();

  return (
    <MapContainer
      center={[40.22, 28.05]}
      zoom={10}
      style={{ width: '100%', height: '100%' }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      />

      {collectionPoints.map((cp) => (
        <React.Fragment key={cp.id}>
          <Marker position={[cp.lat, cp.lng]} icon={cpIcon}>
            <Popup>
              <strong>{cp.name}</strong><br />
              {cp.address && <>{cp.address}<br /></>}
              Durum: <b>{cp.status}</b>
            </Popup>
          </Marker>
          <Circle
            center={[cp.lat, cp.lng]}
            radius={900}
            pathOptions={{ color: '#f59e0b', fillOpacity: 0.06, weight: 1 }}
          />
        </React.Fragment>
      ))}

      {vehicles.map((v) => (
        <Marker
          key={v.id}
          position={[v.current_lat, v.current_lng]}
          icon={vehicleIcon(v.status)}
        >
          <Popup>
            <strong>{v.vehicle_id}</strong> — {v.driver_name}<br />
            Durum: <b>{v.status}</b><br />
            Hız: {v.speed} km/h<br />
            Yük: {v.load_level} / {v.capacity} L<br />
            Sıcaklık: {v.temperature.toFixed(1)}°C
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
