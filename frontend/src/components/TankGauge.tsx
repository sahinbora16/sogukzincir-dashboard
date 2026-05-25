import type { StorageTank } from '../types';

interface TankGaugeProps {
  tank: StorageTank;
}

function fillColor(pct: number): string {
  if (pct >= 90) return 'bg-red-500';
  if (pct >= 70) return 'bg-yellow-400';
  if (pct <= 10) return 'bg-orange-400';
  return 'bg-sogukzincir-blue';
}

function badgeClass(pct: number): string {
  if (pct >= 90) return 'bg-red-100 text-red-700';
  if (pct <= 10) return 'bg-orange-100 text-orange-700';
  return 'bg-sogukzincir-blue-light text-sogukzincir-blue';
}

function tempClass(temp: number): string {
  if (temp > 6) return 'text-red-600 font-semibold';
  if (temp < 2) return 'text-blue-600 font-semibold';
  return 'text-sogukzincir-green';
}

export function TankGauge({ tank }: TankGaugeProps) {
  const pct = Math.min(100, (tank.current_level / tank.capacity) * 100);

  return (
    <div className="bg-white rounded-2xl border border-gray-200 p-4 flex flex-col gap-2 hover:shadow-sm transition-shadow">
      <div className="flex justify-between items-start gap-1">
        <div className="min-w-0">
          <p className="font-semibold text-sm text-gray-800 truncate leading-tight">
            {tank.name}
          </p>
          <p className={`text-xs mt-0.5 ${tempClass(tank.temperature)}`}>
            {tank.temperature.toFixed(1)}°C
          </p>
        </div>
        <span className={`text-xs font-bold px-2 py-0.5 rounded-full shrink-0 ${badgeClass(pct)}`}>
          {pct.toFixed(1)}%
        </span>
      </div>

      <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${fillColor(pct)}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      <p className="text-xs text-gray-400">
        {(tank.current_level / 1000).toFixed(1)}{' '}
        <span className="text-gray-300">/</span>{' '}
        {(tank.capacity / 1000).toFixed(0)} kL
      </p>
    </div>
  );
}
