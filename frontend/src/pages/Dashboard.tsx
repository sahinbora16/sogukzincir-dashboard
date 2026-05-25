import { useDashboardStore } from '../store';
import { usePolling } from '../hooks/usePolling';
import { useFleetSocket } from '../hooks/useFleetSocket';
import { KpiCard } from '../components/KpiCard';
import { TankGauge } from '../components/TankGauge';
import { AlertPanel } from '../components/AlertPanel';
import { FleetMap } from '../components/FleetMap';
import { calculateSpoilage, elapsedHours } from '../types';
import type { CollectionPoint, Vehicle } from '../types';

const COLLECTION_POINTS: CollectionPoint[] = [
  { id: 1, name: 'Susurluk Merkez Toplama',    lat: 40.1833, lng: 28.1333, address: 'Susurluk, Balıkesir',       status: 'active' },
  { id: 2, name: 'Bandırma Süt Toplama',        lat: 40.3553, lng: 27.9778, address: 'Bandırma, Balıkesir',       status: 'active' },
  { id: 3, name: 'Karacabey Çiftlik Noktası',   lat: 40.2167, lng: 28.3500, address: 'Karacabey, Bursa',          status: 'active' },
  { id: 4, name: 'Mustafakemalpaşa Kooperatif', lat: 40.0333, lng: 28.4000, address: 'Mustafakemalpaşa, Bursa',   status: 'collecting' },
  { id: 5, name: 'Gönen Süt Kooperatifi',       lat: 40.1000, lng: 27.6500, address: 'Gönen, Balıkesir',          status: 'active' },
  { id: 6, name: 'Manyas Toplama Noktası',      lat: 40.0500, lng: 27.9667, address: 'Manyas, Balıkesir',         status: 'active' },
];

// ── Inline SVG icons ──────────────────────────────────────────────────────────
const TruckIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10l2 2h10zm0 0l2-2h3l1-5H13" />
  </svg>
);
const TankIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
  </svg>
);
const AlertIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
  </svg>
);
const MilkIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
      d="M9 3h6l2 5H7L9 3zm-2 5v13h10V8H7zm3 4v4m4-4v4" />
  </svg>
);

// ── Status helpers ─────────────────────────────────────────────────────────────
const STATUS_BADGE: Record<Vehicle['status'], string> = {
  en_route:    'bg-sogukzincir-blue-light    text-sogukzincir-blue',
  collecting:  'bg-sogukzincir-green-light   text-sogukzincir-green',
  maintenance: 'bg-red-100             text-red-700',
  idle:        'bg-gray-100            text-gray-500',
};

const STATUS_TR: Record<Vehicle['status'], string> = {
  en_route:    'Yolda',
  collecting:  'Toplama',
  maintenance: 'Bakım',
  idle:        'Beklemede',
};

function bkDisplay(v: Vehicle): string {
  const t = elapsedHours(v.collection_started_at);
  if (t === null) return '—';
  return calculateSpoilage(t, v.temperature).toFixed(2);
}

function bkClass(v: Vehicle): string {
  const t = elapsedHours(v.collection_started_at);
  if (t === null) return 'text-gray-400';
  const bk = calculateSpoilage(t, v.temperature);
  if (bk > 8) return 'text-red-600 font-bold';
  if (bk > 4) return 'text-orange-500 font-semibold';
  return 'text-sogukzincir-green';
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const { vehicles, tanks, alerts, wsConnected, resolveAlert } = useDashboardStore();
  usePolling(10_000);
  useFleetSocket();

  const activeVehicles  = vehicles.filter((v) => v.status === 'en_route' || v.status === 'collecting').length;
  const totalMilkKL     = tanks.reduce((s, t) => s + t.current_level, 0) / 1000;
  const activeAlerts    = alerts.filter((a) => !a.resolved).length;
  const criticalAlerts  = alerts.filter((a) => !a.resolved && (a.severity === 'critical' || a.severity === 'high')).length;
  const nearFullTanks   = tanks.filter((t) => t.current_level / t.capacity >= 0.9).length;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col font-sans">

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <header className="bg-white border-b border-gray-100 px-6 py-3 flex items-center justify-between shrink-0 sticky top-0 z-50 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-sogukzincir-blue flex items-center justify-center text-white font-extrabold text-sm select-none">
            Y
          </div>
          <div>
            <h1 className="text-sm font-bold text-gray-900 leading-tight tracking-tight">
              SoğukZincir Lojistik Dashboard
            </h1>
            <p className="text-xs text-gray-400 leading-tight">
              Soğuk Zincir Yönetim Sistemi
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-sogukzincir-green' : 'bg-red-400 animate-pulse'}`}
          />
          <span className="text-xs text-gray-500">
            {wsConnected ? 'Canlı' : 'Bağlanıyor…'}
          </span>
        </div>
      </header>

      <main className="flex-1 p-5 max-w-[1680px] w-full mx-auto flex flex-col gap-5">

        {/* ── KPI row ───────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            title="Aktif Araçlar"
            value={activeVehicles}
            unit={`/ ${vehicles.length}`}
            icon={<TruckIcon />}
            color="blue"
            subtitle={`${vehicles.filter((v) => v.status === 'en_route').length} araç yolda`}
          />
          <KpiCard
            title="Toplam Süt"
            value={totalMilkKL.toFixed(1)}
            unit="kL"
            icon={<MilkIcon />}
            color="green"
            subtitle={`${tanks.length} tankta depolanan`}
          />
          <KpiCard
            title="Aktif Alarmlar"
            value={activeAlerts}
            icon={<AlertIcon />}
            color={criticalAlerts > 0 ? 'red' : activeAlerts > 0 ? 'yellow' : 'green'}
            subtitle={criticalAlerts > 0 ? `${criticalAlerts} kritik alarm` : 'Sorun yok'}
          />
          <KpiCard
            title="Depolama Tankları"
            value={tanks.length}
            icon={<TankIcon />}
            color="blue"
            subtitle={
              nearFullTanks > 0
                ? `${nearFullTanks} tank neredeyse dolu`
                : 'Kapasite normal'
            }
          />
        </div>

        {/* ── Harita + Alarmlar ─────────────────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div
            className="lg:col-span-2 bg-white rounded-2xl border border-gray-100 flex flex-col overflow-hidden shadow-sm"
            style={{ height: 440 }}
          >
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between shrink-0">
              <h2 className="font-semibold text-sm text-gray-700">Filo Haritası</h2>
              <span className="text-xs text-gray-400">{vehicles.length} araç izleniyor</span>
            </div>
            <div className="flex-1">
              <FleetMap vehicles={vehicles} collectionPoints={COLLECTION_POINTS} />
            </div>
          </div>

          <div
            className="bg-white rounded-2xl border border-gray-100 flex flex-col shadow-sm"
            style={{ maxHeight: 440 }}
          >
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between shrink-0">
              <h2 className="font-semibold text-sm text-gray-700">Aktif Alarmlar</h2>
              {activeAlerts > 0 && (
                <span className="bg-red-500 text-white text-[10px] font-bold w-5 h-5 rounded-full flex items-center justify-center">
                  {activeAlerts}
                </span>
              )}
            </div>
            <div className="flex-1 overflow-y-auto p-3">
              <AlertPanel alerts={alerts} onResolve={resolveAlert} />
            </div>
          </div>
        </div>

        {/* ── Tank göstergeleri ─────────────────────────────────────────── */}
        <div>
          <h2 className="font-semibold text-sm text-gray-700 mb-3">Depolama Tankları</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
            {tanks.map((tank) => (
              <TankGauge key={tank.id} tank={tank} />
            ))}
          </div>
        </div>

        {/* ── Filo tablosu ──────────────────────────────────────────────── */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100">
            <h2 className="font-semibold text-sm text-gray-700">Filo Durumu</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  {['Araç', 'Sürücü', 'Durum', 'Hız', 'Yük', 'Sıcaklık', 'Bk İndeksi', 'Güncelleme'].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {vehicles.map((v) => (
                  <tr key={v.id} className="hover:bg-gray-50/60 transition-colors">
                    <td className="px-4 py-3 font-mono font-bold text-sogukzincir-blue text-xs">
                      {v.vehicle_id}
                    </td>
                    <td className="px-4 py-3 text-gray-700 whitespace-nowrap">
                      {v.driver_name}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2.5 py-1 rounded-full text-xs font-semibold ${STATUS_BADGE[v.status] ?? STATUS_BADGE.idle}`}
                      >
                        {STATUS_TR[v.status] ?? v.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600 whitespace-nowrap text-xs">
                      {v.speed} km/h
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-14 bg-gray-100 rounded-full h-1.5">
                          <div
                            className="bg-sogukzincir-blue h-1.5 rounded-full"
                            style={{ width: `${Math.min(100, (v.load_level / v.capacity) * 100)}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500 tabular-nums">
                          {((v.load_level / v.capacity) * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td
                      className={`px-4 py-3 font-mono text-xs whitespace-nowrap ${
                        v.temperature > 6 || v.temperature < 2 ? 'text-red-600 font-bold' : 'text-sogukzincir-green'
                      }`}
                    >
                      {v.temperature.toFixed(1)}°C
                    </td>
                    <td className={`px-4 py-3 font-mono text-xs whitespace-nowrap ${bkClass(v)}`}>
                      {bkDisplay(v)}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-400 whitespace-nowrap">
                      {new Date(v.last_updated).toLocaleTimeString('tr-TR')}
                    </td>
                  </tr>
                ))}
                {vehicles.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-4 py-10 text-center text-gray-400 text-sm">
                      Araç verisi yükleniyor…
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
