import React from 'react';

export type KpiColor = 'blue' | 'green' | 'yellow' | 'red';

interface KpiCardProps {
  title: string;
  value: string | number;
  unit?: string;
  icon: React.ReactNode;
  color: KpiColor;
  subtitle?: string;
}

// Maps to Tailwind's JIT-safe class strings using SoğukZincir Lojistik corporate colors
const card: Record<KpiColor, string> = {
  blue:   'bg-sogukzincir-blue-light   border-sogukzincir-blue/30   text-sogukzincir-blue',
  green:  'bg-sogukzincir-green-light  border-sogukzincir-green/30  text-sogukzincir-green',
  yellow: 'bg-yellow-50           border-yellow-300       text-yellow-700',
  red:    'bg-red-50              border-red-300          text-red-700',
};

const iconBg: Record<KpiColor, string> = {
  blue:   'bg-sogukzincir-blue/10',
  green:  'bg-sogukzincir-green/10',
  yellow: 'bg-yellow-100',
  red:    'bg-red-100',
};

export function KpiCard({ title, value, unit, icon, color, subtitle }: KpiCardProps) {
  return (
    <div className={`rounded-2xl border p-4 flex items-center gap-4 ${card[color]}`}>
      <div className={`p-3 rounded-xl shrink-0 ${iconBg[color]}`}>{icon}</div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-semibold uppercase tracking-widest opacity-60 truncate">
          {title}
        </p>
        <p className="text-2xl font-extrabold leading-tight mt-0.5">
          {value}
          {unit && <span className="text-sm font-medium ml-1 opacity-70">{unit}</span>}
        </p>
        {subtitle && (
          <p className="text-xs opacity-55 mt-0.5 truncate">{subtitle}</p>
        )}
      </div>
    </div>
  );
}
