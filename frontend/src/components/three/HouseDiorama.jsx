import React, { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';

function Tree({ position, scale = 1 }) {
  return (
    <group position={position} scale={scale}>
      <mesh castShadow position={[0, 0.35, 0]}>
        <cylinderGeometry args={[0.07, 0.09, 0.7, 8]} />
        <meshStandardMaterial color="#9a6238" flatShading />
      </mesh>
      <mesh castShadow position={[0, 0.95, 0]}>
        <icosahedronGeometry args={[0.48, 0]} />
        <meshStandardMaterial color="#4faf6a" flatShading />
      </mesh>
      <mesh castShadow position={[0.2, 1.28, 0.12]}>
        <icosahedronGeometry args={[0.3, 0]} />
        <meshStandardMaterial color="#62c082" flatShading />
      </mesh>
      <mesh castShadow position={[-0.22, 1.18, -0.1]}>
        <icosahedronGeometry args={[0.26, 0]} />
        <meshStandardMaterial color="#3f9d5d" flatShading />
      </mesh>
    </group>
  );
}

function SolarArray() {
  const matRef = useRef();
  useFrame((state) => {
    if (matRef.current) {
      matRef.current.emissiveIntensity = 0.18 + Math.sin(state.clock.elapsedTime * 1.5) * 0.12;
    }
  });
  // angle of the right roof slope (down toward +x)
  const angle = Math.atan2(1.0, 1.25);
  const cells = [];
  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 2; j++) {
      cells.push([i * 0.4 - 0.4, j * 0.62 - 0.31]);
    }
  }
  return (
    <group position={[0.58, 1.66, 0]} rotation={[0, 0, -angle]}>
      <mesh castShadow>
        <boxGeometry args={[1.25, 0.05, 1.4]} />
        <meshStandardMaterial color="#16335f" metalness={0.45} roughness={0.3} />
      </mesh>
      {cells.map(([x, z], idx) => (
        <mesh key={idx} position={[x, 0.04, z]}>
          <boxGeometry args={[0.34, 0.02, 0.56]} />
          <meshStandardMaterial
            ref={idx === 0 ? matRef : undefined}
            color="#2e6fc0"
            emissive="#4ea4ff"
            emissiveIntensity={0.2}
            metalness={0.6}
            roughness={0.25}
          />
        </mesh>
      ))}
    </group>
  );
}

function Turbine() {
  const blades = useRef();
  useFrame((_, dt) => {
    if (blades.current) blades.current.rotation.z += dt * 1.1;
  });
  return (
    <group position={[2.55, 0, -0.55]}>
      <mesh castShadow position={[0, 1.15, 0]}>
        <cylinderGeometry args={[0.05, 0.09, 2.3, 12]} />
        <meshStandardMaterial color="#f3f6f8" roughness={0.4} />
      </mesh>
      <mesh castShadow position={[0, 2.3, 0.05]}>
        <boxGeometry args={[0.2, 0.18, 0.34]} />
        <meshStandardMaterial color="#e3eaee" />
      </mesh>
      <group ref={blades} position={[0, 2.3, 0.26]}>
        <mesh position={[0, 0, 0]}>
          <sphereGeometry args={[0.08, 12, 12]} />
          <meshStandardMaterial color="#cfd8dd" />
        </mesh>
        {[0, 1, 2].map((i) => (
          <mesh key={i} rotation={[0, 0, (i * Math.PI * 2) / 3]} position={[0, 0, 0.02]} castShadow>
            <group>
              <mesh position={[0, 0.55, 0]}>
                <boxGeometry args={[0.07, 1.0, 0.02]} />
                <meshStandardMaterial color="#ffffff" />
              </mesh>
            </group>
          </mesh>
        ))}
      </group>
    </group>
  );
}

function Fence() {
  const posts = [];
  const count = 22;
  const radius = 2.78;
  for (let i = 0; i < count; i++) {
    const a = (i / count) * Math.PI * 2;
    // leave a gap at the front for the path
    if (Math.abs(a - Math.PI / 2) < 0.34) continue;
    posts.push([Math.cos(a) * radius, 0.18, Math.sin(a) * radius]);
  }
  return (
    <group>
      <mesh position={[0, 0.32, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[radius, 0.025, 8, 60]} />
        <meshStandardMaterial color="#ffffff" />
      </mesh>
      {posts.map((p, i) => (
        <mesh key={i} position={p} castShadow>
          <boxGeometry args={[0.07, 0.42, 0.07]} />
          <meshStandardMaterial color="#fbfbf7" />
        </mesh>
      ))}
    </group>
  );
}

function Label({ position, color, text }) {
  return (
    <Html position={position} center distanceFactor={9} zIndexRange={[20, 0]} style={{ pointerEvents: 'none' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          background: 'rgba(255,255,255,0.96)',
          color: '#0E2235',
          fontFamily: 'Nunito, sans-serif',
          fontWeight: 800,
          fontSize: 12,
          padding: '5px 10px',
          borderRadius: 999,
          whiteSpace: 'nowrap',
          boxShadow: '0 6px 18px rgba(14,34,53,0.18)',
        }}
      >
        <span style={{ width: 8, height: 8, borderRadius: 999, background: color }} />
        {text}
      </div>
    </Html>
  );
}

export default function HouseDiorama({ showLabels = true }) {
  const roofGeo = useMemo(() => {
    const shape = new THREE.Shape();
    shape.moveTo(-1.25, 0);
    shape.lineTo(1.25, 0);
    shape.lineTo(0, 1.0);
    shape.closePath();
    const geo = new THREE.ExtrudeGeometry(shape, { depth: 1.85, bevelEnabled: false });
    geo.translate(0, 0, -0.925);
    return geo;
  }, []);

  return (
    <group position={[0, -0.4, 0]} scale={0.92}>
      {/* Ground diorama */}
      <mesh receiveShadow position={[0, 0.25, 0]}>
        <cylinderGeometry args={[3, 3, 0.3, 8]} />
        <meshStandardMaterial color="#74c485" flatShading />
      </mesh>
      <mesh position={[0, -0.25, 0]}>
        <cylinderGeometry args={[2.85, 2.2, 0.8, 8]} />
        <meshStandardMaterial color="#7d5a3a" flatShading />
      </mesh>

      {/* Path */}
      <mesh position={[0, 0.41, 1.85]}>
        <boxGeometry args={[0.55, 0.05, 1.7]} />
        <meshStandardMaterial color="#e0cba6" />
      </mesh>

      {/* House body */}
      <group position={[0, 0.4, 0]}>
        <mesh castShadow receiveShadow position={[0, 0.55, 0]}>
          <boxGeometry args={[2.2, 1.1, 1.7]} />
          <meshStandardMaterial color="#ef9540" flatShading />
        </mesh>

        {/* Roof */}
        <mesh castShadow position={[0, 1.1, 0]} geometry={roofGeo}>
          <meshStandardMaterial color="#3a4f63" flatShading />
        </mesh>

        <SolarArray />

        {/* Chimney */}
        <mesh castShadow position={[-0.7, 1.85, -0.2]}>
          <boxGeometry args={[0.22, 0.5, 0.22]} />
          <meshStandardMaterial color="#c97b3c" />
        </mesh>

        {/* Door */}
        <mesh position={[0, 0.35, 0.86]}>
          <boxGeometry args={[0.4, 0.7, 0.06]} />
          <meshStandardMaterial color="#8a4f23" />
        </mesh>
        {/* Windows front */}
        <mesh position={[-0.65, 0.62, 0.86]}>
          <boxGeometry args={[0.36, 0.36, 0.05]} />
          <meshStandardMaterial color="#bfe6fb" emissive="#7cc6f0" emissiveIntensity={0.25} />
        </mesh>
        <mesh position={[0.65, 0.62, 0.86]}>
          <boxGeometry args={[0.36, 0.36, 0.05]} />
          <meshStandardMaterial color="#bfe6fb" emissive="#7cc6f0" emissiveIntensity={0.25} />
        </mesh>

        {/* Battery box on side wall */}
        <mesh castShadow position={[-1.12, 0.45, 0.4]}>
          <boxGeometry args={[0.12, 0.6, 0.42]} />
          <meshStandardMaterial color="#eef1f3" />
        </mesh>
        <mesh position={[-1.19, 0.45, 0.4]}>
          <boxGeometry args={[0.02, 0.5, 0.32]} />
          <meshStandardMaterial color="#3FB06A" emissive="#3FB06A" emissiveIntensity={0.3} />
        </mesh>
      </group>

      {/* Geothermal loop hint underground (front-left) */}
      <group position={[-0.9, 0.15, 1.5]}>
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[0.4, 0.05, 8, 24]} />
          <meshStandardMaterial color="#3DA5E0" />
        </mesh>
        <mesh rotation={[Math.PI / 2, 0, 0]} position={[0.18, -0.12, 0]}>
          <torusGeometry args={[0.28, 0.045, 8, 24]} />
          <meshStandardMaterial color="#6FBEEB" />
        </mesh>
      </group>

      <Turbine />
      <Fence />
      <Tree position={[-2.1, 0.4, 0.6]} scale={1.05} />
      <Tree position={[1.9, 0.4, 1.4]} scale={0.85} />
      <Tree position={[-1.6, 0.4, -1.7]} scale={0.95} />

      {showLabels && (
        <>
          <Label position={[0.5, 2.75, 0]} color="#3DA5E0" text="Solar panels" />
          <Label position={[2.35, 3.15, -0.55]} color="#F5A623" text="Wind turbine" />
          <Label position={[-1.4, 1.15, 0.4]} color="#3FB06A" text="Battery storage" />
          <Label position={[-0.3, 0.45, 2.05]} color="#2B8FC9" text="Geothermal loop underground" />
        </>
      )}
    </group>
  );
}
