import { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, MeshDistortMaterial } from "@react-three/drei";
import * as THREE from "three";

function LeafParticle({ position, scale, speed }: { position: [number, number, number]; scale: number; speed: number }) {
  const ref = useRef<THREE.Mesh>(null);
  
  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.rotation.x = Math.sin(clock.elapsedTime * speed) * 0.3;
    ref.current.rotation.z = Math.cos(clock.elapsedTime * speed * 0.7) * 0.2;
    ref.current.position.y = position[1] + Math.sin(clock.elapsedTime * speed * 0.5) * 0.3;
  });

  return (
    <mesh ref={ref} position={position} scale={scale}>
      <sphereGeometry args={[0.15, 8, 8]} />
      <meshStandardMaterial color="#2dd475" transparent opacity={0.6} emissive="#1a9e4a" emissiveIntensity={0.3} />
    </mesh>
  );
}

function GlowingSphere() {
  const ref = useRef<THREE.Mesh>(null);
  
  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.rotation.y = clock.elapsedTime * 0.15;
    ref.current.rotation.x = Math.sin(clock.elapsedTime * 0.1) * 0.1;
  });

  return (
    <Float speed={1.5} rotationIntensity={0.3} floatIntensity={0.5}>
      <mesh ref={ref} position={[2, 0, -1]}>
        <icosahedronGeometry args={[1.8, 4]} />
        <MeshDistortMaterial
          color="#1a7a3a"
          emissive="#0d5a2a"
          emissiveIntensity={0.4}
          roughness={0.3}
          metalness={0.6}
          distort={0.25}
          speed={2}
          transparent
          opacity={0.35}
        />
      </mesh>
    </Float>
  );
}

function FloatingRing({ position, color }: { position: [number, number, number]; color: string }) {
  const ref = useRef<THREE.Mesh>(null);
  
  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.rotation.x = clock.elapsedTime * 0.3;
    ref.current.rotation.y = clock.elapsedTime * 0.2;
  });

  return (
    <Float speed={2} floatIntensity={0.4}>
      <mesh ref={ref} position={position}>
        <torusGeometry args={[0.6, 0.08, 16, 32]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.5} transparent opacity={0.4} />
      </mesh>
    </Float>
  );
}

function Particles() {
  const count = 40;
  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 12;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 8;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 6;
    }
    return pos;
  }, []);

  const ref = useRef<THREE.Points>(null);
  
  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.rotation.y = clock.elapsedTime * 0.02;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
          count={count}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial size={0.04} color="#4ade80" transparent opacity={0.6} sizeAttenuation />
    </points>
  );
}

const Scene3D = () => (
  <div className="absolute inset-0 z-0">
    <Canvas camera={{ position: [0, 0, 5], fov: 60 }} dpr={[1, 1.5]}>
      <ambientLight intensity={0.3} />
      <directionalLight position={[5, 5, 5]} intensity={0.5} color="#4ade80" />
      <pointLight position={[-3, 2, 2]} intensity={0.8} color="#22c55e" />
      <pointLight position={[3, -2, 1]} intensity={0.4} color="#d4a42a" />

      <GlowingSphere />
      <FloatingRing position={[-2.5, 1.5, -0.5]} color="#22c55e" />
      <FloatingRing position={[3, -1.5, 0]} color="#d4a42a" />

      {[...Array(8)].map((_, i) => (
        <LeafParticle
          key={i}
          position={[(Math.random() - 0.5) * 8, (Math.random() - 0.5) * 5, (Math.random() - 0.5) * 3]}
          scale={0.5 + Math.random() * 0.8}
          speed={0.3 + Math.random() * 0.5}
        />
      ))}

      <Particles />
    </Canvas>
  </div>
);

export default Scene3D;
