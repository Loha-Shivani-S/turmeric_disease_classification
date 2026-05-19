import { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, MeshDistortMaterial } from "@react-three/drei";
import * as THREE from "three";

function LeafShape({ analyzing }: { analyzing: boolean }) {
  const groupRef = useRef<THREE.Group>(null);
  const glowRef = useRef<THREE.Mesh>(null);

  // Create leaf geometry from a custom shape
  const leafGeometry = useMemo(() => {
    const shape = new THREE.Shape();
    shape.moveTo(0, -1.2);
    shape.bezierCurveTo(0.6, -0.6, 0.8, 0.2, 0.5, 0.8);
    shape.bezierCurveTo(0.3, 1.1, 0.1, 1.3, 0, 1.4);
    shape.bezierCurveTo(-0.1, 1.3, -0.3, 1.1, -0.5, 0.8);
    shape.bezierCurveTo(-0.8, 0.2, -0.6, -0.6, 0, -1.2);

    const extrudeSettings = {
      depth: 0.08,
      bevelEnabled: true,
      bevelThickness: 0.02,
      bevelSize: 0.02,
      bevelSegments: 3,
    };
    return new THREE.ExtrudeGeometry(shape, extrudeSettings);
  }, []);

  useFrame(({ clock }) => {
    if (!groupRef.current) return;
    const speed = analyzing ? 2.5 : 0.5;
    groupRef.current.rotation.y = clock.elapsedTime * speed;
    groupRef.current.rotation.x = Math.sin(clock.elapsedTime * 0.5) * 0.15;
    groupRef.current.rotation.z = Math.cos(clock.elapsedTime * 0.3) * 0.1;

    if (glowRef.current) {
      const scale = analyzing
        ? 1.3 + Math.sin(clock.elapsedTime * 3) * 0.2
        : 1.1;
      glowRef.current.scale.setScalar(scale);
    }
  });

  return (
    <group ref={groupRef}>
      {/* Main leaf */}
      <mesh geometry={leafGeometry}>
        <meshStandardMaterial
          color="#2dd475"
          emissive={analyzing ? "#22c55e" : "#1a7a3a"}
          emissiveIntensity={analyzing ? 0.8 : 0.3}
          roughness={0.4}
          metalness={0.3}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Center vein */}
      <mesh position={[0, 0.1, 0.06]}>
        <cylinderGeometry args={[0.015, 0.01, 2.4, 6]} />
        <meshStandardMaterial
          color="#1a9e4a"
          emissive="#1a9e4a"
          emissiveIntensity={0.4}
        />
      </mesh>

      {/* Glow sphere behind */}
      <mesh ref={glowRef} position={[0, 0, -0.3]}>
        <sphereGeometry args={[0.9, 16, 16]} />
        <MeshDistortMaterial
          color={analyzing ? "#22c55e" : "#1a7a3a"}
          emissive={analyzing ? "#4ade80" : "#22c55e"}
          emissiveIntensity={analyzing ? 1 : 0.3}
          distort={analyzing ? 0.4 : 0.15}
          speed={analyzing ? 5 : 2}
          transparent
          opacity={analyzing ? 0.25 : 0.1}
          roughness={0.2}
          metalness={0.8}
        />
      </mesh>
    </group>
  );
}

function ScanRing({ analyzing }: { analyzing: boolean }) {
  const ref = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.rotation.z = clock.elapsedTime * 1.5;
    ref.current.rotation.x = Math.PI / 2 + Math.sin(clock.elapsedTime) * 0.3;
    const s = analyzing ? 1 + Math.sin(clock.elapsedTime * 2) * 0.15 : 1;
    ref.current.scale.setScalar(s);
  });

  if (!analyzing) return null;

  return (
    <mesh ref={ref}>
      <torusGeometry args={[1.2, 0.03, 16, 64]} />
      <meshStandardMaterial
        color="#4ade80"
        emissive="#4ade80"
        emissiveIntensity={1}
        transparent
        opacity={0.6}
      />
    </mesh>
  );
}

function OrbitalParticles({ analyzing }: { analyzing: boolean }) {
  const groupRef = useRef<THREE.Group>(null);

  useFrame(({ clock }) => {
    if (!groupRef.current) return;
    groupRef.current.rotation.y = clock.elapsedTime * (analyzing ? 1.5 : 0.3);
    groupRef.current.rotation.x = clock.elapsedTime * 0.2;
  });

  return (
    <group ref={groupRef}>
      {[...Array(12)].map((_, i) => {
        const angle = (i / 12) * Math.PI * 2;
        const r = 1.5;
        return (
          <mesh
            key={i}
            position={[
              Math.cos(angle) * r,
              Math.sin(angle) * r * 0.3,
              Math.sin(angle) * r,
            ]}
          >
            <sphereGeometry args={[0.04, 8, 8]} />
            <meshStandardMaterial
              color={i % 2 === 0 ? "#4ade80" : "#d4a42a"}
              emissive={i % 2 === 0 ? "#4ade80" : "#d4a42a"}
              emissiveIntensity={analyzing ? 1 : 0.3}
              transparent
              opacity={analyzing ? 0.8 : 0.4}
            />
          </mesh>
        );
      })}
    </group>
  );
}

const AnalysisLeaf3D = ({ analyzing = false }: { analyzing?: boolean }) => (
  <div className="w-full h-full min-h-[200px]">
    <Canvas camera={{ position: [0, 0, 3.5], fov: 45 }} dpr={[1, 1.5]}>
      <ambientLight intensity={0.4} />
      <pointLight
        position={[3, 3, 3]}
        intensity={analyzing ? 1.2 : 0.6}
        color="#4ade80"
      />
      <pointLight
        position={[-2, -1, 2]}
        intensity={0.4}
        color="#d4a42a"
      />
      <Float speed={analyzing ? 0 : 1.5} floatIntensity={analyzing ? 0 : 0.3}>
        <LeafShape analyzing={analyzing} />
      </Float>
      <ScanRing analyzing={analyzing} />
      <OrbitalParticles analyzing={analyzing} />
    </Canvas>
  </div>
);

export default AnalysisLeaf3D;
