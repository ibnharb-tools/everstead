import React, { Suspense } from 'react';
import { DIORAMA_IMG } from '../../lib/assets';

const HomeScene = React.lazy(() => import('./HomeScene'));

function Poster({ className }) {
  return (
    <div className={`flex items-center justify-center ${className}`}>
      <img
        src={DIORAMA_IMG}
        alt="A friendly home with solar panels on the roof and a small wind turbine beside it"
        className="w-full h-full object-contain select-none"
        draggable={false}
      />
    </div>
  );
}

export default function Home3D({ showLabels = true, className = 'w-full h-full', technologies }) {
  return (
    <div className={className}>
      <Suspense fallback={<Poster className="w-full h-full" />}>
        <HomeScene showLabels={showLabels} technologies={technologies} />
      </Suspense>
    </div>
  );
}
