import React from 'react';

export const CHART = {
  solar: '#3DA5E0',
  savings: '#3FB06A',
  cost: '#F5A623',
  baseline: '#0E2235',
  wind: '#6FBEEB',
  geo: '#329257',
  battery: '#FF8A3D',
};

export function BrandTooltip({ active, payload, label, unit = '', prefix = '', labelText }) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="bg-white rounded-2xl shadow-lift border border-navy-900/5 px-4 py-3">
      {label != null && (
        <p className="font-heading font-bold text-navy-900 text-sm mb-1">
          {labelText ? `${labelText} ${label}` : label}
        </p>
      )}
      {payload.map((p, i) => (
        <p key={i} className="text-sm font-body text-navy-700 flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full" style={{ background: p.color || p.fill }} />
          <span className="font-semibold text-navy-900">
            {prefix}
            {typeof p.value === 'number' ? p.value.toLocaleString() : p.value}
            {unit}
          </span>
        </p>
      ))}
    </div>
  );
}
