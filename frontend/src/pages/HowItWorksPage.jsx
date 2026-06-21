import React, { useState } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  PieChart,
  Pie,
} from 'recharts';
import {
  MapPin,
  Sun,
  Wind,
  Thermometer,
  Droplets,
  Home,
  BadgePercent,
  ArrowRight,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { Slider } from '../components/ui/slider';
import { Reveal } from '../components/Reveal';
import { CTABand } from '../components/layout/CTABand';
import { CHART, BrandTooltip } from '../components/charts/ChartBits';
import { mockAssessment } from '../mock/mockData';
import Home3D from '../components/three/Home3D';

const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const sunlightData = mockAssessment.charts.monthlySunlightKwhM2.map((v, i) => ({ month: months[i], kwh: v }));

const energyData = [
  { name: 'Solar', kwh: 9288, color: CHART.solar },
  { name: 'Wind', kwh: 13433, color: CHART.wind },
  { name: 'Geothermal', kwh: 6500, color: CHART.geo },
  { name: 'Micro-hydro', kwh: 4200, color: '#2B8FC9' },
];

function WindGauge({ value = 5.2, max = 12 }) {
  const cx = 110;
  const cy = 115;
  const r = 86;
  const toXY = (frac) => {
    const deg = 180 - frac * 180;
    const rad = (deg * Math.PI) / 180;
    return [cx + r * Math.cos(rad), cy - r * Math.sin(rad)];
  };
  const samples = (a, b, n = 48) =>
    Array.from({ length: n + 1 }, (_, i) => toXY(a + ((b - a) * i) / n).join(',')).join(' ');
  const frac = Math.min(value / max, 1);
  const [nx, ny] = toXY(frac);
  return (
    <svg viewBox="0 0 220 140" className="w-full max-w-[260px]">
      <polyline points={samples(0, 1)} fill="none" stroke="#0E223514" strokeWidth="14" strokeLinecap="round" />
      <polyline points={samples(0, frac)} fill="none" stroke={CHART.solar} strokeWidth="14" strokeLinecap="round" />
      <line x1={cx} y1={cy} x2={nx} y2={ny} stroke="#0E2235" strokeWidth="4" strokeLinecap="round" />
      <circle cx={cx} cy={cy} r="7" fill="#0E2235" />
      <text x={cx} y={cy - 26} textAnchor="middle" className="fill-navy-900" fontSize="26" fontWeight="800" fontFamily="Nunito">
        {value}
      </text>
      <text x={cx} y={cy - 8} textAnchor="middle" fill="#5d7991" fontSize="12">
        m/s wind
      </text>
    </svg>
  );
}

function PaybackInteractive() {
  const [price, setPrice] = useState(11); // cents per kWh
  const cost = 18000;
  const annualKwh = 9288;
  const annualSavings = (price / 100) * annualKwh;
  const data = Array.from({ length: 26 }, (_, y) => ({ year: y, value: Math.round(-cost + annualSavings * y) }));
  const payoff = annualSavings > 0 ? Math.round((cost / annualSavings) * 10) / 10 : null;
  return (
    <div>
      <div className="h-60">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <CartesianGrid stroke="#0E223510" vertical={false} />
            <XAxis dataKey="year" tickLine={false} axisLine={false} tick={{ fill: '#5d7991', fontSize: 12 }} />
            <YAxis tickFormatter={(v) => `${Math.round(v / 1000)}k`} tickLine={false} axisLine={false} tick={{ fill: '#5d7991', fontSize: 12 }} />
            <Tooltip content={<BrandTooltip prefix="$" labelText="Year" />} />
            <ReferenceLine y={0} stroke="#0E223530" strokeDasharray="4 4" />
            <Line type="monotone" dataKey="value" stroke={CHART.cost} strokeWidth={3} dot={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 rounded-2xl bg-cream p-4 border border-navy-900/5">
        <div className="flex items-center justify-between text-sm font-semibold text-navy-700">
          <span>Electricity price</span>
          <span className="text-amber-600">${(price / 100).toFixed(2)} / kWh</span>
        </div>
        <Slider
          value={[price]}
          min={6}
          max={30}
          step={1}
          onValueChange={(v) => setPrice(v[0])}
          className="mt-3"
          data-testid="payback-price-slider"
        />
        <p className="mt-3 text-sm text-navy-600">
          {payoff ? `At this price, this example pays off around year ${payoff}.` : 'Move the slider to see the payback shift.'}
        </p>
      </div>
    </div>
  );
}

function DonutSplit() {
  const data = [
    { name: 'What you pay', value: 16800, color: CHART.cost },
    { name: 'Rebates and savings', value: 7200, color: CHART.savings },
  ];
  return (
    <div className="flex items-center gap-6">
      <div className="w-40 h-40">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" innerRadius={48} outerRadius={70} paddingAngle={3} stroke="none">
              {data.map((d, i) => (
                <Cell key={i} fill={d.color} />
              ))}
            </Pie>
            <Tooltip content={<BrandTooltip prefix="$" />} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="space-y-3">
        {data.map((d) => (
          <div key={d.name} className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full" style={{ background: d.color }} />
            <div>
              <p className="font-heading font-bold text-navy-900">${d.value.toLocaleString()}</p>
              <p className="text-sm text-navy-600">{d.name}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Step({ index, title, children, visual, flip }) {
  return (
    <Reveal>
      <div className="grid lg:grid-cols-2 gap-8 lg:gap-14 items-center">
        <div className={flip ? 'lg:order-2' : ''}>
          <span className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-amber-500 text-white font-heading font-extrabold text-lg shadow-amber">
            {index}
          </span>
          <h2 className="mt-5 font-heading font-extrabold text-2xl md:text-4xl text-navy-900">{title}</h2>
          <div className="mt-4 text-lg text-navy-700 leading-relaxed space-y-3">{children}</div>
        </div>
        <div className={flip ? 'lg:order-1' : ''}>
          <div className="rounded-[2rem] bg-white border border-navy-900/5 shadow-soft p-6 md:p-8">{visual}</div>
        </div>
      </div>
    </Reveal>
  );
}

const measures = [
  { icon: Sun, color: '#3DA5E0', label: 'Sunlight' },
  { icon: Wind, color: '#6FBEEB', label: 'Wind speed' },
  { icon: Thermometer, color: '#329257', label: 'Ground temperature' },
  { icon: Droplets, color: '#2B8FC9', label: 'Water flow' },
  { icon: Home, color: '#F5A623', label: 'Your roof and land' },
  { icon: BadgePercent, color: '#FF8A3D', label: 'Local rebates' },
];

export default function HowItWorksPage() {
  return (
    <div>
      <section className="container-px pt-16 md:pt-20 pb-6">
        <Reveal>
          <span className="inline-flex items-center gap-2 bg-amber-500/10 text-amber-600 font-semibold rounded-full px-4 py-1.5 text-sm">
            A friendly walkthrough
          </span>
          <h1 className="mt-5 font-heading font-extrabold text-4xl md:text-6xl text-navy-900">How Everstead works</h1>
          <p className="mt-5 text-lg md:text-xl text-navy-700 max-w-2xl">
            No jargon. Here is exactly what happens after you enter your address.
          </p>
        </Reveal>
      </section>

      <div className="container-px py-12 space-y-24 md:space-y-32">
        <Step
          index={1}
          title="Tell us about your home."
          visual={
            <div>
              <div className="relative h-44 rounded-2xl bg-gradient-to-b from-azure-500/15 to-leaf-500/10 overflow-hidden flex items-center justify-center">
                <div className="absolute inset-0" style={{ backgroundImage: 'radial-gradient(#0E223510 1px, transparent 1px)', backgroundSize: '18px 18px' }} />
                <div className="relative animate-floaty">
                  <MapPin size={44} className="text-amber-500 drop-shadow" fill="#F5A623" />
                </div>
              </div>
              <div className="mt-4 space-y-2">
                <div className="rounded-xl border border-navy-900/10 bg-cream px-4 py-3 text-navy-500">123 Main St, your city</div>
                <div className="flex gap-2">
                  <span className="rounded-lg bg-amber-500/10 text-amber-600 text-sm font-semibold px-3 py-1.5">House</span>
                  <span className="rounded-lg bg-navy-900/5 text-navy-600 text-sm font-semibold px-3 py-1.5">2 floors</span>
                  <span className="rounded-lg bg-navy-900/5 text-navy-600 text-sm font-semibold px-3 py-1.5">Medium roof</span>
                </div>
              </div>
            </div>
          }
        >
          <p>Start with your address and a few simple questions: the type of home, how many floors, and the roof.</p>
          <p>A map pin drops on your spot, and your home shows up in 3D so you can see what we are working with.</p>
        </Step>

        <Step
          index={2}
          flip
          title="We pull real data for your exact spot."
          visual={
            <div>
              <div className="h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={sunlightData} margin={{ top: 10, right: 10, left: -12, bottom: 0 }}>
                    <defs>
                      <linearGradient id="sun" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={CHART.cost} stopOpacity={0.55} />
                        <stop offset="100%" stopColor={CHART.cost} stopOpacity={0.05} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#0E223510" vertical={false} />
                    <XAxis dataKey="month" tickLine={false} axisLine={false} tick={{ fill: '#5d7991', fontSize: 11 }} />
                    <YAxis tickLine={false} axisLine={false} tick={{ fill: '#5d7991', fontSize: 11 }} />
                    <Tooltip content={<BrandTooltip unit=" kWh/m²" />} />
                    <Area type="monotone" dataKey="kwh" stroke={CHART.cost} strokeWidth={3} fill="url(#sun)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              <p className="text-center text-sm text-navy-500 mt-1">Sunlight by month. Hover to see each one.</p>
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="rounded-2xl bg-cream border border-navy-900/5 p-4 flex flex-col items-center">
                  <WindGauge value={mockAssessment.site.averageWindSpeedMs} />
                </div>
                <div className="rounded-2xl bg-cream border border-navy-900/5 p-4 flex flex-col items-center justify-center text-center">
                  <Thermometer size={28} className="text-leaf-600" />
                  <p className="mt-2 font-heading font-extrabold text-3xl text-navy-900">{mockAssessment.site.groundTempC}°C</p>
                  <p className="text-sm text-navy-600">steady underground</p>
                </div>
              </div>
            </div>
          }
        >
          <p>
            We look up how much sun, wind, and ground warmth your specific location gets, using trusted public sources
            like national weather and energy records.
          </p>
        </Step>

        <Step
          index={3}
          title="We model each clean energy option."
          visual={
            <div>
              <div className="h-60">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={energyData} margin={{ top: 10, right: 10, left: -12, bottom: 0 }}>
                    <CartesianGrid stroke="#0E223510" vertical={false} />
                    <XAxis dataKey="name" tickLine={false} axisLine={false} tick={{ fill: '#5d7991', fontSize: 12 }} />
                    <YAxis tickFormatter={(v) => `${v / 1000}k`} tickLine={false} axisLine={false} tick={{ fill: '#5d7991', fontSize: 12 }} />
                    <Tooltip content={<BrandTooltip unit=" kWh/yr" />} cursor={{ fill: '#0E223508' }} />
                    <Bar dataKey="kwh" radius={[10, 10, 0, 0]}>
                      {energyData.map((d, i) => (
                        <Cell key={i} fill={d.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <p className="text-center text-sm text-navy-500 mt-1">Power each option could make in a year, in kilowatt-hours.</p>
            </div>
          }
        >
          <p>We calculate how much power solar, wind, geothermal, and micro-hydro could each make at your home.</p>
          <p>Then we line them up side by side so it is easy to see what fits best.</p>
        </Step>

        <Step
          index={4}
          flip
          title="We work out the money."
          visual={
            <div className="space-y-6">
              <PaybackInteractive />
              <div className="pt-2 border-t border-navy-900/5">
                <p className="font-heading font-bold text-navy-900 mb-3">What you pay, and what comes back</p>
                <DonutSplit />
              </div>
            </div>
          }
        >
          <p>
            We add up the cost to install, the money you save each year, the rebates you qualify for, and how long until
            it pays for itself.
          </p>
          <p>Try the slider to see how a different electricity price changes the payback.</p>
        </Step>

        <Step
          index={5}
          title="You get your plan, in 3D."
          visual={
            <div>
              <div className="h-72 rounded-2xl bg-gradient-to-b from-white to-[#fdeed6] overflow-hidden">
                <Home3D showLabels />
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="rounded-full bg-azure-500/10 text-azure-600 text-sm font-semibold px-3 py-1.5">Solar panels · $18,400</span>
                <span className="rounded-full bg-amber-600/10 text-amber-600 text-sm font-semibold px-3 py-1.5">Battery · $14,000</span>
                <span className="rounded-full bg-leaf-500/10 text-leaf-600 text-sm font-semibold px-3 py-1.5">Wind turbine · optional</span>
              </div>
            </div>
          }
        >
          <p>
            You see a ranked list of the best options for your home, a 3D view with the equipment placed where it should
            go, and a marketplace to buy what you chose.
          </p>
          <Link to="/retrofit" className="inline-flex items-center gap-2 mt-2 font-heading font-bold text-amber-600 hover:text-amber-500">
            Try it on your home <ArrowRight size={18} />
          </Link>
        </Step>
      </div>

      {/* What we measure */}
      <section className="bg-white/60 border-y border-navy-900/5">
        <div className="container-px py-16 md:py-20">
          <Reveal>
            <h2 className="font-heading font-extrabold text-2xl md:text-4xl text-navy-900">What we measure</h2>
            <p className="mt-3 text-navy-700 text-lg">Six simple things about your spot. Nothing more complicated than that.</p>
          </Reveal>
          <div className="mt-10 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {measures.map((m) => (
              <div key={m.label} className="rounded-2xl bg-white border border-navy-900/5 p-5 text-center">
                <span className="w-12 h-12 mx-auto rounded-2xl flex items-center justify-center" style={{ background: `${m.color}1a` }}>
                  <m.icon size={24} style={{ color: m.color }} />
                </span>
                <p className="mt-3 font-semibold text-navy-800 text-[15px]">{m.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <CTABand />
    </div>
  );
}
