import React from 'react';

export function LogoMark({ size = 36 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <circle cx="24" cy="24" r="22" fill="#FFF1DA" />
      <circle cx="24" cy="18" r="7.5" fill="#F5A623" />
      <path d="M10 28L24 17l14 11v9a2 2 0 0 1-2 2H12a2 2 0 0 1-2-2z" fill="#0E2235" />
      <path d="M21 39v-6a3 3 0 0 1 6 0v6z" fill="#FFC15E" />
      <rect x="14.5" y="30.5" width="4.5" height="4.5" rx="1" fill="#3DA5E0" />
      <rect x="29" y="30.5" width="4.5" height="4.5" rx="1" fill="#3DA5E0" />
    </svg>
  );
}

export function Logo({ className = '', onLight = false }) {
  return (
    <span className={`flex items-center gap-2.5 ${className}`}>
      <LogoMark />
      <span
        className={`font-heading font-extrabold text-2xl tracking-tight ${
          onLight ? 'text-cream' : 'text-navy-900'
        }`}
      >
        Everstead
      </span>
    </span>
  );
}
