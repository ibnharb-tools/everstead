import React from 'react';
import { FileText, Lightbulb, LineChart, KeyRound, Boxes, ShoppingBag, Gauge, TrendingUp, Glasses } from 'lucide-react';
import { Reveal, RevealStagger, RevealItem } from '../components/Reveal';
import { CTABand } from '../components/layout/CTABand';

const TAGS = {
  Soon: 'bg-amber-500/15 text-amber-600',
  Planned: 'bg-azure-500/15 text-azure-600',
  Exploring: 'bg-leaf-500/15 text-leaf-600',
};

const cards = [
  { icon: FileText, color: '#F5A623', tag: 'Soon', title: 'Read your power bill for you', text: 'Upload your utility bill and we will match your real usage to your plan, so the numbers fit your actual home.' },
  { icon: Lightbulb, color: '#F5A623', tag: 'Soon', title: 'Smart energy tips', text: 'Simple, friendly suggestions to help you save more once your system is running.' },
  { icon: LineChart, color: '#3DA5E0', tag: 'Planned', title: 'Real performance tracking', text: 'See how much power your system makes over time, day by day and month by month.' },
  { icon: KeyRound, color: '#F5A623', tag: 'Soon', title: 'Sign in with Google or Apple', text: 'Quick, easy login with the accounts you already use.' },
  { icon: Boxes, color: '#3DA5E0', tag: 'Planned', title: 'Full 3D view of your property', text: 'A richer 3D model of your home and land, with every piece of equipment placed exactly where it goes.' },
  { icon: ShoppingBag, color: '#3DA5E0', tag: 'Planned', title: 'Live marketplace', text: 'Compare trusted suppliers side by side and order everything in one place.' },
  { icon: Gauge, color: '#3DA5E0', tag: 'Planned', title: 'Monitoring dashboard', text: "One simple screen to watch your energy, your savings, and your system's health." },
  { icon: TrendingUp, color: '#3FB06A', tag: 'Exploring', title: 'Optimize and expand', text: 'Get suggestions on when to add a battery, more panels, or new equipment as your needs grow.' },
  { icon: Glasses, color: '#3FB06A', tag: 'Exploring', title: 'See it on-site with AR glasses', text: 'Stand in your yard and see your future solar and wind setup in front of you, using augmented reality.' },
];

export default function WhatsNextPage() {
  return (
    <div>
      <section className="container-px pt-16 md:pt-20 pb-6">
        <Reveal>
          <span className="inline-flex items-center gap-2 bg-azure-500/10 text-azure-600 font-semibold rounded-full px-4 py-1.5 text-sm">
            Roadmap
          </span>
          <h1 className="mt-5 font-heading font-extrabold text-4xl md:text-6xl text-navy-900">
            What we're building next.
          </h1>
          <p className="mt-5 text-lg md:text-xl text-navy-700 max-w-2xl">
            Everstead keeps getting smarter. Here is what is coming.
          </p>
        </Reveal>
      </section>

      <section className="container-px py-10">
        <RevealStagger className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {cards.map((c) => (
            <RevealItem key={c.title}>
              <div className="h-full rounded-3xl bg-white border border-navy-900/5 shadow-soft p-7 hover:shadow-lift hover:-translate-y-1 transition-all duration-300">
                <div className="flex items-center justify-between">
                  <span className="w-12 h-12 rounded-2xl flex items-center justify-center" style={{ background: `${c.color}1a` }}>
                    <c.icon size={24} style={{ color: c.color }} />
                  </span>
                  <span className={`text-xs font-bold rounded-full px-3 py-1 ${TAGS[c.tag]}`}>{c.tag}</span>
                </div>
                <h3 className="mt-5 font-heading font-bold text-lg text-navy-900">{c.title}</h3>
                <p className="mt-2 text-navy-700 text-[15px] leading-relaxed">{c.text}</p>
              </div>
            </RevealItem>
          ))}
        </RevealStagger>
      </section>

      <CTABand />
    </div>
  );
}
