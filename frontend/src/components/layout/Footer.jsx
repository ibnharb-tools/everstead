import React from 'react';
import { Link } from 'react-router-dom';
import { Instagram, Twitter, Youtube, Mail } from 'lucide-react';
import { LogoMark } from '../Logo';

const navLinks = [
  { to: '/', label: 'Home' },
  { to: '/how-it-works', label: 'How It Works' },
  { to: '/about', label: 'About' },
  { to: '/whats-next', label: "What's Next" },
  { to: '/retrofit', label: 'Retrofit My Home' },
];

export function Footer() {
  return (
    <footer className="bg-navy-900 text-cream" data-testid="site-footer">
      <div className="container-px py-16 md:py-20">
        <div className="grid gap-12 md:grid-cols-[1.4fr_1fr_1fr]">
          <div>
            <div className="flex items-center gap-2.5">
              <LogoMark size={40} />
              <span className="font-heading font-extrabold text-2xl text-cream">Everstead</span>
            </div>
            <p className="mt-5 font-heading font-extrabold text-3xl leading-tight text-cream max-w-sm">
              Let's energize your home.
            </p>
            <p className="mt-4 text-navy-300 text-base max-w-sm">
              Clean energy made simple, for every home.
            </p>
            <div className="flex items-center gap-3 mt-6">
              {[Instagram, Twitter, Youtube, Mail].map((Icon, i) => (
                <a
                  key={i}
                  href="#"
                  aria-label="Social link"
                  className="w-10 h-10 rounded-full bg-cream/10 hover:bg-amber-500 transition-colors flex items-center justify-center"
                >
                  <Icon size={18} className="text-cream" />
                </a>
              ))}
            </div>
          </div>

          <div>
            <h4 className="font-heading font-bold text-cream/60 text-sm uppercase tracking-wide">Pages</h4>
            <ul className="mt-4 space-y-3">
              {navLinks.map((l) => (
                <li key={l.to}>
                  <Link to={l.to} className="text-navy-300 hover:text-cream transition-colors">
                    {l.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="font-heading font-bold text-cream/60 text-sm uppercase tracking-wide">Company</h4>
            <ul className="mt-4 space-y-3">
              <li><Link to="/about" className="text-navy-300 hover:text-cream transition-colors">About us</Link></li>
              <li><Link to="/login" className="text-navy-300 hover:text-cream transition-colors">Log in</Link></li>
              <li><a href="#" className="text-navy-300 hover:text-cream transition-colors">Privacy</a></li>
              <li><a href="#" className="text-navy-300 hover:text-cream transition-colors">Terms</a></li>
            </ul>
          </div>
        </div>

        <div className="mt-14 pt-8 border-t border-cream/10 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-navy-300 text-sm">© {new Date().getFullYear()} Everstead. Made for real homes.</p>
          <p className="text-navy-300 text-sm">Built with care, not hype.</p>
        </div>
      </div>
    </footer>
  );
}
