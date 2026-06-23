import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ReferenceDot,
} from 'recharts';
import { Sun, Wind, Mountain, Waves, BatteryCharging, ExternalLink, BadgeCheck, MapPin } from 'lucide-react';
import { fmtMoney, fmtPayback, fmtNum } from '../../lib/format';
import { CHART, BrandTooltip } from '../charts/ChartBits';
import Home3D from '../three/Home3D';

const META = {
  solar_pv: { icon: Sun, color: '#3DA5E0' },
  battery: { icon: BatteryCharging, color: '#FF8A3D' },
  wind: { icon: Wind, color: '#6FBEEB' },
  geothermal: { icon: Mountain, color: '#329257' },
  micro_hydro: { icon: Waves, color: '#2B8FC9' },
};

function TechCard({ tech, currency }) {
  const meta = META[tech.type] || META.solar_pv;
  const Icon = meta.icon;
  const dim = !tech.recommended;
  return (
    <div
      data-testid={`result-tech-card-${tech.type}`}
      className={`rounded-3xl border bg-white p-6 md:p-7 transition-all ${
        dim ? 'border-navy-900/5 opacity-80' : 'border-amber-500/25 shadow-soft'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span
            className="w-12 h-12 rounded-2xl flex items-center justify-center"
            style={{ background: `${meta.color}1a` }}
          >
            <Icon size={24} style={{ color: meta.color }} />
          </span>
          <h3 className="font-heading font-bold text-xl text-navy-900">{tech.displayName}</h3>
        </div>
        {tech.recommended && (
          <span className="inline-flex items-center gap-1 text-xs font-bold text-leaf-600 bg-leaf-500/10 rounded-full px-3 py-1">
            <BadgeCheck size={14} /> Recommended
          </span>
        )}
      </div>

      <div className="grid grid-cols-3 gap-3 mt-6">
        <div>
          <p className="text-xs text-navy-500 font-semibold uppercase tracking-wide">Cost</p>
          <p className="font-heading font-extrabold text-navy-900 text-lg mt-1">{fmtMoney(tech.netCapex, currency)}</p>
        </div>
        <div>
          <p className="text-xs text-navy-500 font-semibold uppercase tracking-wide">Saves / yr</p>
          <p className="font-heading font-extrabold text-leaf-600 text-lg mt-1">{fmtMoney(tech.yearlySavings, currency)}</p>
        </div>
        <div>
          <p className="text-xs text-navy-500 font-semibold uppercase tracking-wide">Pays off</p>
          <p className="font-heading font-extrabold text-navy-900 text-lg mt-1">{fmtPayback(tech.paybackYears)}</p>
        </div>
      </div>

      <p className="mt-5 text-navy-700 leading-relaxed">{tech.reason}</p>

      {tech.buyAt && tech.buyAt.length > 0 && (
        <div className="mt-5 flex flex-wrap gap-2">
          {tech.buyAt.map((b) => (
            <a
              key={b.name}
              href={b.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm font-semibold text-navy-700 bg-cream border border-navy-900/10 rounded-full px-3 py-1.5 hover:border-amber-500 transition-colors"
            >
              {b.name} <ExternalLink size={13} />
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

export function ResultsView({ assessment, actions = null }) {
  const currency = assessment.currency;
  const techs = assessment.technologies;
  const { paybackCurve } = assessment.charts;
  const data = paybackCurve.years.map((y, i) => ({ year: y, value: paybackCurve.cumulativeCashFlow[i] }));
  const payoffIdx = data.findIndex((d) => d.value >= 0);
  const payoffPoint = payoffIdx > -1 ? data[payoffIdx] : null;
  const site = assessment.site;

  return (
    <div className="space-y-10" data-testid="results-view">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="font-heading font-extrabold text-3xl md:text-4xl text-navy-900">
            Here is the best way to power your home.
          </h2>
          <p className="mt-2 text-navy-600 flex items-center gap-1.5">
            <MapPin size={16} className="text-amber-500" /> {site.resolvedAddress}
          </p>
        </div>
        {actions}
      </div>

      {/* 3D home + rebates */}
      <div className="grid lg:grid-cols-[1.3fr_1fr] gap-6">
        <div className="rounded-3xl bg-gradient-to-b from-white to-cream border border-navy-900/5 shadow-soft overflow-hidden">
          <div className="h-[340px]">
            <Home3D showLabels technologies={techs} />
          </div>
          <div className="px-6 pb-5 -mt-2">
            <p className="font-heading font-bold text-navy-900">Your home, with the recommended setup</p>
            <p className="text-sm text-navy-600 mt-1">Drag to spin. Showing the technologies suited to your location.</p>
          </div>
        </div>

        <div className="rounded-3xl bg-leaf-500/10 border border-leaf-500/20 p-6 md:p-7">
          <h3 className="font-heading font-bold text-xl text-navy-900">Rebates and credits we found for you</h3>
          <p className="mt-3 text-navy-700 leading-relaxed">{assessment.incentiveSummary.note}</p>
          <a
            href={assessment.incentiveSummary.moreInfoUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 inline-flex items-center gap-1.5 font-semibold text-leaf-600 hover:text-leaf-500"
          >
            Look up local rebates <ExternalLink size={15} />
          </a>

          <div className="mt-6 pt-5 border-t border-leaf-600/15 grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-navy-500">Yearly sunlight</p>
              <p className="font-heading font-bold text-navy-900">{fmtNum(site.annualSunlightKwhM2)} kWh/m²</p>
            </div>
            <div>
              <p className="text-navy-500">Average wind</p>
              <p className="font-heading font-bold text-navy-900">{site.averageWindSpeedMs} m/s</p>
            </div>
            <div>
              <p className="text-navy-500">Ground warmth</p>
              <p className="font-heading font-bold text-navy-900">{site.groundTempC}°C</p>
            </div>
            <div>
              <p className="text-navy-500">Power price</p>
              <p className="font-heading font-bold text-navy-900">{assessment.electricityPrice}/kWh</p>
            </div>
          </div>
        </div>
      </div>

      {/* Ranked options */}
      <div>
        <h3 className="font-heading font-bold text-2xl text-navy-900 mb-5">Your ranked options</h3>
        <div className="grid sm:grid-cols-2 gap-5">
          {techs.map((t) => (
            <TechCard key={t.type} tech={t} currency={currency} />
          ))}
        </div>
      </div>

      {/* Charts */}
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="rounded-3xl bg-white border border-navy-900/5 shadow-soft p-6">
          <h3 className="font-heading font-bold text-xl text-navy-900">When solar pays for itself</h3>
          <p className="text-sm text-navy-600 mt-1">The line starts as the cost, then climbs as you save.</p>
          <div style={{ height: 240 }} className="mt-4">
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid stroke="#0E223510" vertical={false} />
                <XAxis dataKey="year" tickLine={false} axisLine={false} tick={{ fill: '#5d7991', fontSize: 12 }} />
                <YAxis
                  tickFormatter={(v) => `${Math.round(v / 1000)}k`}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#5d7991', fontSize: 12 }}
                />
                <Tooltip content={<BrandTooltip prefix="$" labelText="Year" />} />
                <ReferenceLine y={0} stroke="#0E223530" strokeDasharray="4 4" />
                <Line type="monotone" dataKey="value" stroke={CHART.cost} strokeWidth={3} dot={false} />
                {payoffPoint && (
                  <ReferenceDot x={payoffPoint.year} y={payoffPoint.value} r={6} fill={CHART.savings} stroke="#fff" strokeWidth={2} />
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>
          <p className="text-sm text-navy-600 mt-2">
            {payoffPoint
              ? `Paid off near year ${payoffPoint.year}, then it is savings from there.`
              : 'This option does not fully pay back within 25 years here.'}
          </p>
        </div>

        <div className="rounded-3xl bg-white border border-navy-900/5 shadow-soft p-6">
          <h3 className="font-heading font-bold text-xl text-navy-900">Where you stand over 25 years</h3>
          <p className="text-sm text-navy-600 mt-1">Your running total, costs first, then savings.</p>
          <div style={{ height: 240 }} className="mt-4">
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="savingsFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={CHART.savings} stopOpacity={0.5} />
                    <stop offset="100%" stopColor={CHART.savings} stopOpacity={0.04} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#0E223510" vertical={false} />
                <XAxis dataKey="year" tickLine={false} axisLine={false} tick={{ fill: '#5d7991', fontSize: 12 }} />
                <YAxis
                  tickFormatter={(v) => `${Math.round(v / 1000)}k`}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#5d7991', fontSize: 12 }}
                />
                <Tooltip content={<BrandTooltip prefix="$" labelText="Year" />} />
                <ReferenceLine y={0} stroke="#0E223530" strokeDasharray="4 4" />
                <Area type="monotone" dataKey="value" stroke={CHART.savings} strokeWidth={3} fill="url(#savingsFill)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <p className="text-sm text-navy-500 italic">{assessment.disclaimer}</p>
    </div>
  );
}
