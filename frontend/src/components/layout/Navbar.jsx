import React, { useState, useEffect } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { Logo } from '../Logo';
import { useAuth } from '../../context/AuthContext';

const links = [
  { to: '/', label: 'Home' },
  { to: '/how-it-works', label: 'How It Works' },
  { to: '/about', label: 'About' },
  { to: '/whats-next', label: "What's Next" },
  { to: '/retrofit', label: 'Retrofit My Home' },
];

export function Navbar() {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const { user } = useAuth();

  useEffect(() => {
    setOpen(false);
  }, [location.pathname]);

  return (
    <header className="sticky top-0 z-50 bg-cream/80 backdrop-blur-xl border-b border-navy-900/5">
      <nav className="container-px flex items-center justify-between h-[72px]" data-testid="main-nav">
        <Link to="/" data-testid="nav-logo-link" aria-label="Everstead home">
          <Logo />
        </Link>

        <div className="hidden lg:flex items-center gap-1">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              data-testid={`nav-link-${l.label.toLowerCase().replace(/[^a-z]+/g, '-')}`}
              className={({ isActive }) =>
                `px-4 py-2 rounded-full text-[15px] font-body font-medium transition-colors ${
                  isActive ? 'text-amber-600 bg-amber-500/10' : 'text-navy-700 hover:text-navy-900 hover:bg-navy-900/5'
                }`
              }
            >
              {l.label}
            </NavLink>
          ))}
        </div>

        <div className="hidden lg:flex items-center gap-3">
          <Link
            to={user ? '/dashboard' : '/login'}
            data-testid="nav-login-link"
            className="text-[15px] font-body font-semibold text-navy-700 hover:text-navy-900 px-3 py-2"
          >
            {user ? 'My homes' : 'Log in'}
          </Link>
          <Link
            to="/retrofit"
            data-testid="nav-start-assessment"
            className="bg-amber-500 hover:bg-amber-600 text-white font-heading font-bold text-[15px] rounded-full px-6 py-3 shadow-amber transition-all duration-300 hover:-translate-y-0.5"
          >
            Start my assessment
          </Link>
        </div>

        <button
          className="lg:hidden p-2 rounded-full text-navy-900 hover:bg-navy-900/5"
          onClick={() => setOpen((v) => !v)}
          data-testid="mobile-menu-toggle"
          aria-label="Toggle menu"
        >
          {open ? <X size={26} /> : <Menu size={26} />}
        </button>
      </nav>

      {open && (
        <div className="lg:hidden border-t border-navy-900/5 bg-cream" data-testid="mobile-menu">
          <div className="container-px py-4 flex flex-col gap-1">
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.to === '/'}
                className={({ isActive }) =>
                  `px-4 py-3 rounded-xl font-body font-medium ${
                    isActive ? 'text-amber-600 bg-amber-500/10' : 'text-navy-800'
                  }`
                }
              >
                {l.label}
              </NavLink>
            ))}
            <div className="flex flex-col gap-2 pt-3">
              <Link
                to={user ? '/dashboard' : '/login'}
                className="px-4 py-3 rounded-xl font-semibold text-navy-800 border border-navy-900/10 text-center"
              >
                {user ? 'My homes' : 'Log in'}
              </Link>
              <Link
                to="/retrofit"
                className="px-4 py-3 rounded-full bg-amber-500 text-white font-heading font-bold text-center shadow-amber"
              >
                Start my assessment
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
