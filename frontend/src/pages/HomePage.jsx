import React from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  Sun,
  Wind,
  Mountain,
  Waves,
  BatteryCharging,
  ClipboardList,
  Calculator,
  BadgePercent,
  Boxes,
  ShoppingBag,
  Activity,
  MapPin,
  Search,
  LayoutList,
} from 'lucide-react';
import Home3D from '../components/three/Home3D';
import { Reveal, RevealStagger, RevealItem } from '../components/Reveal';
import { AnimatedNumber } from '../components/AnimatedNumber';
import { CTABand } from '../components/layout/CTABand';
import { IMG } from '../lib/assets';

const gives = [
  { icon: ClipboardList, color: '#3DA5E0', title: 'A clear plan for your home', text: 'See which clean energy options actually fit your roof, your land, and your weather.' },
  { icon: Calculator, color: '#3FB06A', title: 'Real numbers, no guessing', text: 'Costs, yearly savings, and how long until the system pays for itself.' },
  { icon: BadgePercent, color: '#F5A623', title: 'Rebates found for you', text: 'We check which local and national rebates and credits you can get.' },
  { icon: Boxes, color: '#FF8A3D', title: 'A 3D view of your home', text: 'See exactly where panels, batteries, and other gear would go.' },
  { icon: ShoppingBag, color: '#2B8FC9', title: 'One place to buy', text: 'Compare trusted suppliers and order the equipment you chose.' },
  { icon: Activity, color: '#329257', title: 'Track it after install', text: 'Watch your system perform and find ways to save even more.' },
];

const techs = [
  { icon: Sun, color: '#3DA5E0', img: IMG.solar, title: 'Solar panels', text: 'Turn sunlight on your roof into electricity.' },
  { icon: Wind, color: '#6FBEEB', img: IMG.wind, title: 'Wind', text: 'Catch the wind on open or breezy properties.' },
  { icon: Mountain, color: '#329257', img: IMG.geothermal, title: 'Geothermal', text: 'Use the steady temperature underground to heat and cool your home.' },
  { icon: Waves, color: '#2B8FC9', img: IMG.hydro, title: 'Micro-hydro', text: 'Make power from a stream or moving water on your land.' },
  { icon: BatteryCharging, color: '#FF8A3D', img: IMG.battery, title: 'Battery storage', text: 'Store power for nighttime and keep the lights on during outages.' },
];

const steps = [
  { icon: MapPin, color: '#F5A623', title: 'Tell us about your home', text: 'Your address and a few quick details about the place.' },
  { icon: Search, color: '#3DA5E0', title: 'We check your exact spot', text: 'The sun, wind, and ground warmth at your specific location.' },
  { icon: LayoutList, color: '#3FB06A', title: 'You get a ranked plan', text: 'Costs, savings, rebates, and a 3D view of your home.' },
];

function StatChip({ className, label, children }) {
  return (
    <div className={`absolute ${className} bg-white rounded-2xl shadow-lift border border-navy-900/5 px-4 py-3`}>
      <p className="font-heading font-extrabold text-xl text-navy-900 leading-none">{children}</p>
      <p className="text-xs text-navy-500 mt-1">{label}</p>
    </div>
  );
}

export default function HomePage() {
  return (
    <div>
      {/* Hero */}
      <section className="container-px pt-12 md:pt-16 pb-8">
        <div className="grid lg:grid-cols-2 gap-10 lg:gap-6 items-center">
          <Reveal>
            <span className="inline-flex items-center gap-2 bg-amber-500/10 text-amber-600 font-semibold rounded-full px-4 py-1.5 text-sm">
              <span className="w-2 h-2 rounded-full bg-amber-500" /> Clean energy made simple
            </span>
            <h1 className="mt-5 font-heading font-extrabold text-5xl md:text-6xl leading-[1.05] text-navy-900 text-balance">
              Let's energize your home.
            </h1>
            <p className="mt-5 text-lg md:text-xl text-navy-700 leading-relaxed max-w-xl">
              Tell us your address and we will show you the cleanest, smartest way to power your home, with real
              costs, real savings, and the rebates you qualify for.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Link
                to="/retrofit"
                data-testid="hero-start-assessment"
                className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-white font-heading font-bold text-lg rounded-full px-8 py-4 shadow-amber hover:-translate-y-0.5 transition-all"
              >
                Start my assessment <ArrowRight size={20} />
              </Link>
              <Link
                to="/how-it-works"
                data-testid="hero-see-how"
                className="font-heading font-bold text-lg text-navy-800 hover:text-amber-600 px-3 py-2"
              >
                See how it works
              </Link>
            </div>
          </Reveal>

          <Reveal delay={0.15}>
            <div className="relative">
              <div className="relative h-[380px] sm:h-[460px] rounded-[2rem] bg-gradient-to-b from-white to-[#fdeed6] border border-navy-900/5 shadow-soft overflow-hidden">
                <Home3D showLabels />
              </div>
              <StatChip className="-top-3 left-2 sm:left-6 animate-floaty" label="Estimated yearly savings">
                <AnimatedNumber value={1200} prefix="$" />
              </StatChip>
              <StatChip className="top-1/3 -right-2 sm:right-2 animate-floaty" label="Clean power produced">
                <AnimatedNumber value={9288} suffix=" kWh" />
              </StatChip>
              <StatChip className="-bottom-3 left-6 animate-floaty" label="Typical payback">
                <AnimatedNumber value={9} suffix=" yr" />
              </StatChip>
            </div>
          </Reveal>
        </div>
      </section>

      {/* What Everstead gives you */}
      <section className="container-px py-20 md:py-28">
        <Reveal>
          <h2 className="font-heading font-extrabold text-3xl md:text-5xl text-navy-900 max-w-2xl">
            What Everstead gives you
          </h2>
        </Reveal>
        <RevealStagger className="mt-12 grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {gives.map((g) => (
            <RevealItem key={g.title}>
              <div className="h-full rounded-3xl bg-white border border-navy-900/5 shadow-soft p-8 hover:shadow-lift hover:-translate-y-1 transition-all duration-300">
                <span className="w-14 h-14 rounded-2xl flex items-center justify-center" style={{ background: `${g.color}1a` }}>
                  <g.icon size={26} style={{ color: g.color }} />
                </span>
                <h3 className="mt-5 font-heading font-bold text-xl text-navy-900">{g.title}</h3>
                <p className="mt-2 text-navy-700 leading-relaxed">{g.text}</p>
              </div>
            </RevealItem>
          ))}
        </RevealStagger>
      </section>

      {/* Technologies */}
      <section className="bg-white/60 border-y border-navy-900/5">
        <div className="container-px py-20 md:py-28">
          <Reveal>
            <h2 className="font-heading font-extrabold text-3xl md:text-5xl text-navy-900 max-w-3xl">
              Every clean energy option in one place
            </h2>
            <p className="mt-4 text-lg text-navy-700 max-w-2xl">
              Five ways to power a home, checked against your exact spot. Here is what each one does.
            </p>
          </Reveal>
          <RevealStagger className="mt-12 grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {techs.map((t) => (
              <RevealItem key={t.title}>
                <div className="h-full rounded-3xl bg-white border border-navy-900/5 shadow-soft overflow-hidden hover:shadow-lift hover:-translate-y-1 transition-all duration-300">
                  <div className="h-40 overflow-hidden">
                    <img src={t.img} alt={t.title} className="w-full h-full object-cover" loading="lazy" />
                  </div>
                  <div className="p-6">
                    <span className="w-11 h-11 rounded-xl flex items-center justify-center" style={{ background: `${t.color}1a` }}>
                      <t.icon size={22} style={{ color: t.color }} />
                    </span>
                    <h3 className="mt-4 font-heading font-bold text-xl text-navy-900">{t.title}</h3>
                    <p className="mt-1 text-navy-700">{t.text}</p>
                  </div>
                </div>
              </RevealItem>
            ))}
          </RevealStagger>
        </div>
      </section>

      {/* How it works preview */}
      <section className="container-px py-20 md:py-28">
        <Reveal>
          <h2 className="font-heading font-extrabold text-3xl md:text-5xl text-navy-900">How it works in three steps</h2>
        </Reveal>
        <RevealStagger className="mt-12 grid md:grid-cols-3 gap-6">
          {steps.map((s, i) => (
            <RevealItem key={s.title}>
              <div className="h-full rounded-3xl bg-cream border border-navy-900/5 p-8 relative">
                <span className="absolute top-6 right-7 font-heading font-extrabold text-5xl text-navy-900/5">{i + 1}</span>
                <span className="w-14 h-14 rounded-2xl flex items-center justify-center" style={{ background: `${s.color}1a` }}>
                  <s.icon size={26} style={{ color: s.color }} />
                </span>
                <h3 className="mt-5 font-heading font-bold text-xl text-navy-900">{s.title}</h3>
                <p className="mt-2 text-navy-700">{s.text}</p>
              </div>
            </RevealItem>
          ))}
        </RevealStagger>
        <Reveal delay={0.1}>
          <div className="mt-10">
            <Link
              to="/how-it-works"
              data-testid="home-see-how-it-works"
              className="inline-flex items-center gap-2 font-heading font-bold text-lg text-navy-900 bg-white border-2 border-navy-900/10 hover:border-navy-900/30 rounded-full px-7 py-3.5 transition-colors"
            >
              See how it works <ArrowRight size={18} />
            </Link>
          </div>
        </Reveal>
      </section>

      <CTABand />
    </div>
  );
}
