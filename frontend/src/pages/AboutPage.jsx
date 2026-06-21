import React from 'react';
import { Heart, Eye, Users, Camera } from 'lucide-react';
import { Reveal, RevealStagger, RevealItem } from '../components/Reveal';
import { CTABand } from '../components/layout/CTABand';

const missionCards = [
  { icon: Heart, color: '#F5A623', title: 'Our mission (coming soon)', text: 'A short line about why Everstead exists will live here. Easy to swap out later.' },
  { icon: Eye, color: '#3DA5E0', title: 'What we believe (coming soon)', text: 'Add a friendly sentence about the values behind the product in this spot.' },
  { icon: Users, color: '#3FB06A', title: 'Who we serve (coming soon)', text: 'Describe the homeowners Everstead is built for. Placeholder text for now.' },
];

export default function AboutPage() {
  return (
    <div>
      <section className="container-px pt-16 md:pt-20 pb-6">
        <Reveal>
          <span className="inline-flex items-center gap-2 bg-leaf-500/10 text-leaf-600 font-semibold rounded-full px-4 py-1.5 text-sm">
            Our story
          </span>
          <h1 className="mt-5 font-heading font-extrabold text-4xl md:text-6xl text-navy-900">About Everstead</h1>
          <p className="mt-5 text-lg md:text-xl text-navy-700 max-w-2xl">
            This page is a friendly placeholder. The real words are coming. Everything here is styled and ready to
            fill in.
          </p>
        </Reveal>
      </section>

      {/* Founder block */}
      <section className="container-px py-12 md:py-16">
        <Reveal>
          <div className="grid md:grid-cols-[0.9fr_1.1fr] gap-8 items-center rounded-[2rem] bg-white border border-navy-900/5 shadow-soft p-6 md:p-10">
            <div className="aspect-[4/5] rounded-3xl bg-cream border-2 border-dashed border-navy-900/15 flex flex-col items-center justify-center text-center p-6">
              <span className="w-16 h-16 rounded-full bg-amber-500/15 flex items-center justify-center">
                <Camera size={28} className="text-amber-600" />
              </span>
              <p className="mt-4 font-heading font-bold text-navy-900">Photo coming soon</p>
              <p className="mt-1 text-sm text-navy-500">A founder photo will go here.</p>
            </div>
            <div>
              <span className="text-sm font-semibold uppercase tracking-wide text-navy-500">Founder note (placeholder)</span>
              <h2 className="mt-3 font-heading font-bold text-2xl md:text-3xl text-navy-900">
                This is where the founder's story will go.
              </h2>
              <p className="mt-4 text-navy-700 leading-relaxed">
                Add a short, personal note here about why Everstead was built and who it is for. Keep it warm and plain,
                the way you would tell a neighbor. This text is a placeholder and is easy to replace later.
              </p>
              <p className="mt-4 text-navy-700 leading-relaxed">
                A second paragraph can go here too, if you want a little more room for the story.
              </p>
            </div>
          </div>
        </Reveal>
      </section>

      {/* Mission strip */}
      <section className="container-px pb-8">
        <RevealStagger className="grid md:grid-cols-3 gap-6">
          {missionCards.map((c) => (
            <RevealItem key={c.title}>
              <div className="h-full rounded-3xl bg-cream border border-navy-900/5 p-8">
                <span className="w-14 h-14 rounded-2xl flex items-center justify-center" style={{ background: `${c.color}1a` }}>
                  <c.icon size={26} style={{ color: c.color }} />
                </span>
                <h3 className="mt-5 font-heading font-bold text-xl text-navy-900">{c.title}</h3>
                <p className="mt-2 text-navy-700">{c.text}</p>
              </div>
            </RevealItem>
          ))}
        </RevealStagger>
      </section>

      <CTABand />
    </div>
  );
}
