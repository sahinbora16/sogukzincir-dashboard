import type { Alert } from '../types';

const API = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000';

interface AlertPanelProps {
  alerts: Alert[];
  onResolve: (id: number) => void;
}

const cardClass: Record<string, string> = {
  critical: 'bg-red-50    border-red-200    text-red-900',
  high:     'bg-orange-50 border-orange-200 text-orange-900',
  medium:   'bg-yellow-50 border-yellow-200 text-yellow-900',
  low:      'bg-blue-50   border-blue-200   text-blue-900',
};

const badgeClass: Record<string, string> = {
  critical: 'bg-red-600    text-white',
  high:     'bg-orange-500 text-white',
  medium:   'bg-yellow-400 text-gray-900',
  low:      'bg-sogukzincir-blue text-white',
};

const typeLabel: Record<string, string> = {
  HIGH_RISK:     'Yüksek Risk',
  MEDIUM_RISK:   'Orta Risk',
  tank_overflow: 'Tank Doldu',
  low_tank:      'Düşük Tank',
  temperature:   'Sıcaklık',
};

export function AlertPanel({ alerts, onResolve }: AlertPanelProps) {
  const active = alerts.filter((a) => !a.resolved);

  async function handleResolve(id: number): Promise<void> {
    await fetch(`${API}/api/alerts/${id}/resolve`, { method: 'PATCH' });
    onResolve(id);
  }

  if (active.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-sogukzincir-green gap-2">
        <svg className="w-8 h-8 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="text-sm opacity-60">Aktif alarm yok</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {active.map((alert) => (
        <div
          key={alert.id}
          className={`rounded-xl border p-3 flex items-start gap-3 ${cardClass[alert.severity] ?? cardClass.low}`}
        >
          <span
            className={`text-[10px] font-bold px-2 py-0.5 rounded-full mt-0.5 uppercase tracking-wide shrink-0 ${badgeClass[alert.severity] ?? badgeClass.low}`}
          >
            {typeLabel[alert.alert_type] ?? alert.alert_type}
          </span>
          <div className="flex-1 min-w-0">
            <p className="text-sm leading-snug">{alert.message}</p>
            <p className="text-xs opacity-50 mt-1">
              {new Date(alert.created_at).toLocaleString('tr-TR')}
            </p>
          </div>
          <button
            onClick={() => void handleResolve(alert.id)}
            className="text-xs font-medium underline underline-offset-2 opacity-50 hover:opacity-100 transition-opacity whitespace-nowrap shrink-0"
          >
            Kapat
          </button>
        </div>
      ))}
    </div>
  );
}
