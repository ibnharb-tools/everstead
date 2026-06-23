import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, ContactShadows } from '@react-three/drei';
import HouseDiorama from './HouseDiorama';

export default function HomeScene({ showLabels = true, technologies }) {
  return (
    <Canvas
      shadows
      dpr={[1, 1.8]}
      camera={{ position: [6.6, 4.3, 6.6], fov: 34 }}
      gl={{ antialias: true, powerPreference: 'high-performance' }}
      style={{ width: '100%', height: '100%' }}
    >
      <ambientLight intensity={0.75} />
      <hemisphereLight args={['#fff6e6', '#cfe8d8', 0.55]} />
      <directionalLight
        position={[6, 9, 4]}
        intensity={1.5}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
        shadow-camera-near={1}
        shadow-camera-far={30}
        shadow-camera-left={-8}
        shadow-camera-right={8}
        shadow-camera-top={8}
        shadow-camera-bottom={-8}
      />
      <Suspense fallback={null}>
        <HouseDiorama showLabels={showLabels} technologies={technologies} />
        <ContactShadows position={[0, -0.62, 0]} opacity={0.32} scale={13} blur={2.6} far={5} color="#3a2a18" />
      </Suspense>
      <OrbitControls
        makeDefault
        enableZoom={false}
        enablePan={false}
        autoRotate
        autoRotateSpeed={0.7}
        enableDamping
        dampingFactor={0.08}
        minPolarAngle={Math.PI * 0.3}
        maxPolarAngle={Math.PI * 0.46}
        target={[0, 0.5, 0]}
      />
    </Canvas>
  );
}
