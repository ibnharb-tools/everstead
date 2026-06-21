import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { Reveal } from '../Reveal';

export function CTABand() {
  return (
    <section className="container-px py-16 md:py-24">
      <Reveal>
        <div className="relative overflow-hidden rounded-[2rem] bg-amber-500 px-8 py-14 md:px-16 md:py-20 text-center shadow-amber">
          <div className="absolute -top-10 -right-10 w-40 h-40 rounded-full bg-amber-400/40" aria-hidden="true" />
          <div className="absolute -bottom-12 -left-8 w-48 h-48 rounded-full bg-amber-600/30" aria-hidden="true" />
          <div className="relative">
            <h2 className="font-heading font-extrabold text-3xl md:text-5xl text-white text-balance">
              Ready to see what your home can do?
            </h2>
            <p className="mt-4 text-white/90 text-lg max-w-xl mx-auto">
              It takes about five minutes. No account needed to see your first results.
            </p>
            <Link
              to="/retrofit"
              data-testid="cta-band-start-assessment"
              className="mt-8 inline-flex items-center gap-2 bg-white text-navy-900 font-heading font-bold text-lg rounded-full px-8 py-4 shadow-lift hover:-translate-y-0.5 transition-transform"
            >
              Start my assessment
              <ArrowRight size={20} />
            </Link>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
