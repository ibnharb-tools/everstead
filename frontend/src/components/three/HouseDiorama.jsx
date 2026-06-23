import React, { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';

function Tree({ position, scale = 1 }) {
  return (
    <group position={position} scale={scale}>
      <mesh castShadow position={[0, 0.35, 0]}>
        <cylinderGeometry args={[0.07, 0.1, 0.72, 8]} />
        <meshStandardMaterial color="#8a5c2e" flatShading />
      </mesh>
      <mesh castShadow position={[0, 0.98, 0]}>
        <icosahedronGeometry args={[0.5, 0]} />
        <meshStandardMaterial color="#4ab86a" flatShading />
      </mesh>
      <mesh castShadow position={[0.22, 1.3, 0.14]}>
        <icosahedronGeometry args={[0.32, 0]} />
        <meshStandardMaterial color="#5fd080" flatShading />
      </mesh>
      <mesh castShadow position={[-0.2, 1.22, -0.12]}>
        <icosahedronGeometry args={[0.27, 0]} />
        <meshStandardMaterial color="#3a9a5c" flatShading />
      </mesh>
    </group>
  );
}

function Flower({ position, color }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.06, 0]}>
        <cylinderGeometry args={[0.025, 0.025, 0.12, 6]} />
        <meshStandardMaterial color="#5d9e3d" />
      </mesh>
      <mesh position={[0, 0.14, 0]}>
        <sphereGeometry args={[0.055, 8, 8]} />
        <meshStandardMaterial color={color} />
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
            <mesh position={[0, 0.55, 0]}>
              <boxGeometry args={[0.07, 1.0, 0.02]} />
              <meshStandardMaterial color="#ffffff" />
            </mesh>
          </mesh>
        ))}
      </group>
    </group>
  );
}

function Fence() {
  const posts = [];
  const count = 26;
  const radius = 2.78;
  for (let i = 0; i < count; i++) {
    const a = (i / count) * Math.PI * 2;
    if (Math.abs(a - Math.PI / 2) < 0.30) continue;
    posts.push([Math.cos(a) * radius, 0.18, Math.sin(a) * radius]);
  }
  return (
    <group>
      <mesh position={[0, 0.32, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[radius, 0.022, 8, 72]} />
        <meshStandardMaterial color="#ffffff" roughness={0.5} />
      </mesh>
      <mesh position={[0, 0.48, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[radius, 0.018, 8, 72]} />
        <meshStandardMaterial color="#ffffff" roughness={0.5} />
      </mesh>
      {posts.map((p, i) => (
        <mesh key={i} position={p} castShadow>
          <boxGeometry args={[0.07, 0.5, 0.07]} />
          <meshStandardMaterial color="#f8f8f4" roughness={0.6} />
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
          gap: 4,
          background: 'rgba(255,255,255,0.93)',
          color: '#0E2235',
          fontFamily: 'Nunito, sans-serif',
          fontWeight: 700,
          fontSize: 9.5,
          padding: '3px 7px',
          borderRadius: 999,
          whiteSpace: 'nowrap',
          boxShadow: '0 2px 8px rgba(14,34,53,0.14)',
          letterSpacing: '0.01em',
        }}
      >
        <span style={{ width: 6, height: 6, borderRadius: 999, background: color, flexShrink: 0 }} />
        {text}
      </div>
    </Html>
  );
}

// technologies: array of { type, recommended } from the assessment (or undefined for default landing view)
export default function HouseDiorama({ showLabels = true, technologies }) {
  const roofGeo = useMemo(() => {
    const shape = new THREE.Shape();
    shape.moveTo(-1.25, 0);
    shape.lineTo(1.25, 0);
    shape.lineTo(0, 1.05);
    shape.closePath();
    const geo = new THREE.ExtrudeGeometry(shape, { depth: 1.9, bevelEnabled: false });
    geo.translate(0, 0, -0.95);
    return geo;
  }, []);

  // Determine which tech elements to show
  const hasSolar = !technologies || technologies.some((t) => t.type === 'solar_pv' && t.recommended !== false);
  const hasBattery = !technologies || technologies.some((t) => t.type === 'battery' && t.recommended !== false);
  const hasWind = !technologies || technologies.some((t) => t.type === 'wind');
  const hasGeo = !technologies || technologies.some((t) => t.type === 'geothermal');

  const showSolar = hasSolar;
  const showBattery = hasBattery;
  const showWind = hasWind;
  const showGeo = hasGeo;

  // If we have real tech data, only show what's there; if no data (landing page), show all
  const realData = !!technologies;

  return (
    <group position={[0, -0.4, 0]} scale={0.92}>
      {/* Ground base */}
      <mesh receiveShadow position={[0, 0.25, 0]}>
        <cylinderGeometry args={[3, 3, 0.32, 10]} />
        <meshStandardMaterial color="#6ec87a" flatShading />
      </mesh>
      <mesh position={[0, -0.26, 0]}>
        <cylinderGeometry args={[2.9, 2.2, 0.82, 10]} />
        <meshStandardMaterial color="#7d5a3a" flatShading />
      </mesh>

      {/* Stone path */}
      {[0, 0.55, 1.1, 1.65].map((z, i) => (
        <mesh key={i} position={[i % 2 === 0 ? 0.08 : -0.08, 0.415, z + 0.3]}>
          <boxGeometry args={[0.28, 0.04, 0.28]} />
          <meshStandardMaterial color="#c8b89a" roughness={0.9} />
        </mesh>
      ))}

      {/* Flower beds */}
      {[[-0.55, 0], [-0.35, 0], [-0.15, 0], [0.15, 0], [0.35, 0], [0.55, 0]].map(([x, z], i) => (
        <Flower
          key={i}
          position={[x, 0.38, 0.92 + z]}
          color={['#e05555', '#e08c2a', '#4a8de0', '#e0c82a', '#d0405a', '#40c08a'][i % 6]}
        />
      ))}

      {/* House body */}
      <group position={[0, 0.4, 0]}>
        {/* Walls */}
        <mesh castShadow receiveShadow position={[0, 0.55, 0]}>
          <boxGeometry args={[2.25, 1.12, 1.75]} />
          <meshStandardMaterial color="#e8853a" flatShading />
        </mesh>

        {/* Base trim */}
        <mesh position={[0, -0.01, 0]}>
          <boxGeometry args={[2.32, 0.09, 1.82]} />
          <meshStandardMaterial color="#c46828" />
        </mesh>

        {/* Roof */}
        <mesh castShadow position={[0, 1.1, 0]} geometry={roofGeo}>
          <meshStandardMaterial color="#2c3f54" flatShading />
        </mesh>

        {/* Roof trim/fascia */}
        <mesh position={[0, 1.1, -0.97]}>
          <boxGeometry args={[2.55, 0.09, 0.07]} />
          <meshStandardMaterial color="#4a6075" />
        </mesh>
        <mesh position={[0, 1.1, 0.97]}>
          <boxGeometry args={[2.55, 0.09, 0.07]} />
          <meshStandardMaterial color="#4a6075" />
        </mesh>

        {showSolar && <SolarArray />}

        {/* Chimney */}
        <mesh castShadow position={[-0.7, 1.88, -0.25]}>
          <boxGeometry args={[0.23, 0.52, 0.23]} />
          <meshStandardMaterial color="#c0722e" flatShading />
        </mesh>
        <mesh position={[-0.7, 2.16, -0.25]}>
          <boxGeometry args={[0.29, 0.06, 0.29]} />
          <meshStandardMaterial color="#a85e24" />
        </mesh>

        {/* Door */}
        <mesh position={[0, 0.3, 0.89]}>
          <boxGeometry args={[0.44, 0.82, 0.07]} />
          <meshStandardMaterial color="#4a5c8a" roughness={0.3} metalness={0.1} />
        </mesh>
        {/* Door frame */}
        <mesh position={[0, 0.31, 0.89]}>
          <boxGeometry args={[0.5, 0.88, 0.05]} />
          <meshStandardMaterial color="#c46828" />
        </mesh>
        {/* Door knob */}
        <mesh position={[0.17, 0.28, 0.94]}>
          <sphereGeometry args={[0.035, 8, 8]} />
          <meshStandardMaterial color="#d4a820" metalness={0.8} roughness={0.2} />
        </mesh>

        {/* Steps */}
        <mesh position={[0, 0.02, 1.0]}>
          <boxGeometry args={[0.7, 0.1, 0.3]} />
          <meshStandardMaterial color="#b0a090" />
        </mesh>
        <mesh position={[0, -0.05, 1.14]}>
          <boxGeometry args={[0.82, 0.09, 0.26]} />
          <meshStandardMaterial color="#a09080" />
        </mesh>

        {/* Windows front */}
        <mesh position={[-0.67, 0.62, 0.89]}>
          <boxGeometry args={[0.38, 0.38, 0.06]} />
          <meshStandardMaterial color="#bfe6fb" emissive="#aad8f8" emissiveIntensity={0.3} metalness={0.1} roughness={0.0} />
        </mesh>
        <mesh position={[0.67, 0.62, 0.89]}>
          <boxGeometry args={[0.38, 0.38, 0.06]} />
          <meshStandardMaterial color="#bfe6fb" emissive="#aad8f8" emissiveIntensity={0.3} metalness={0.1} roughness={0.0} />
        </mesh>
        {/* Window frames */}
        {[[-0.67, 0.62], [0.67, 0.62]].map(([x, y], i) => (
          <mesh key={i} position={[x, y, 0.88]}>
            <boxGeometry args={[0.46, 0.46, 0.04]} />
            <meshStandardMaterial color="#c46828" />
          </mesh>
        ))}

        {/* Window box planters */}
        {[[-0.67], [0.67]].map(([x], i) => (
          <group key={i} position={[x, 0.40, 0.9]}>
            <mesh>
              <boxGeometry args={[0.44, 0.1, 0.14]} />
              <meshStandardMaterial color="#8a5c2e" />
            </mesh>
            {[-0.1, 0, 0.1].map((dx, j) => (
              <mesh key={j} position={[dx, 0.07, 0]}>
                <sphereGeometry args={[0.055, 6, 6]} />
                <meshStandardMaterial color={['#e85565', '#f5a030', '#4a9ae0'][j]} />
              </mesh>
            ))}
          </group>
        ))}

        {/* Window back */}
        <mesh position={[-0.65, 0.62, -0.89]}>
          <boxGeometry args={[0.38, 0.38, 0.06]} />
          <meshStandardMaterial color="#bfe6fb" emissive="#aad8f8" emissiveIntensity={0.2} />
        </mesh>

        {/* Side window */}
        <mesh position={[1.14, 0.62, 0]}>
          <boxGeometry args={[0.06, 0.35, 0.35]} />
          <meshStandardMaterial color="#bfe6fb" emissive="#aad8f8" emissiveIntensity={0.2} />
        </mesh>

        {/* Porch light */}
        <mesh position={[0.26, 0.78, 0.91]}>
          <boxGeometry args={[0.08, 0.14, 0.08]} />
          <meshStandardMaterial color="#d4a820" emissive="#ffcc40" emissiveIntensity={0.6} metalness={0.6} roughness={0.2} />
        </mesh>

        {/* Battery box on side wall */}
        {(showBattery || !realData) && (
          <>
            <mesh castShadow position={[-1.14, 0.46, 0.4]}>
              <boxGeometry args={[0.13, 0.65, 0.45]} />
              <meshStandardMaterial color="#eef1f4" roughness={0.4} />
            </mesh>
            <mesh position={[-1.21, 0.46, 0.4]}>
              <boxGeometry args={[0.02, 0.54, 0.34]} />
              <meshStandardMaterial color="#3FB06A" emissive="#3FB06A" emissiveIntensity={0.35} />
            </mesh>
          </>
        )}
      </group>

      {/* Geothermal loop hint underground */}
      {(showGeo || !realData) && (
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
      )}

      {(showWind || !realData) && <Turbine />}
      <Fence />

      <Tree position={[-2.1, 0.4, 0.6]} scale={1.05} />
      <Tree position={[1.9, 0.4, 1.4]} scale={0.85} />
      <Tree position={[-1.6, 0.4, -1.7]} scale={0.95} />

      {/* Bushes */}
      <mesh castShadow position={[-1.6, 0.55, 0.9]}>
        <icosahedronGeometry args={[0.28, 0]} />
        <meshStandardMaterial color="#3d9e58" flatShading />
      </mesh>
      <mesh castShadow position={[1.55, 0.55, 0.75]}>
        <icosahedronGeometry args={[0.24, 0]} />
        <meshStandardMaterial color="#4aae64" flatShading />
      </mesh>
      <mesh castShadow position={[2.1, 0.5, 1.3]}>
        <icosahedronGeometry args={[0.2, 0]} />
        <meshStandardMaterial color="#38904e" flatShading />
      </mesh>

      {showLabels && (
        <>
          {(showSolar || !realData) && (
            <Label position={[0.5, 2.78, 0]} color="#3DA5E0" text="Solar panels" />
          )}
          {(showWind || !realData) && (
            <Label position={[2.35, 3.18, -0.55]} color="#F5A623" text="Wind turbine" />
          )}
          {(showBattery || !realData) && (
            <Label position={[-1.45, 1.18, 0.4]} color="#3FB06A" text="Battery storage" />
          )}
          {(showGeo || !realData) && (
            <Label position={[-0.3, 0.48, 2.1]} color="#2B8FC9" text="Geothermal" />
          )}
        </>
      )}
    </group>
  );
}
