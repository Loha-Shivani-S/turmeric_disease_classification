import { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, MeshDistortMaterial, OrbitControls } from "@react-three/drei";
import * as THREE from "three";

function DiseasedLeaf() {
  const groupRef = useRef<THREE.Group>(null);
  const scanLineRef = useRef<THREE.Mesh>(null);

  // Leaf geometry
  const leafGeometry = useMemo(() => {
    const shape = new THREE.Shape();
    shape.moveTo(0, -1.2);
    shape.bezierCurveTo(0.6, -0.6, 0.8, 0.2, 0.5, 0.8);
    shape.bezierCurveTo(0.3, 1.1, 0.1, 1.3, 0, 1.4);
    shape.bezierCurveTo(-0.1, 1.3, -0.3, 1.1, -0.5, 0.8);
    shape.bezierCurveTo(-0.8, 0.2, -0.6, -0.6, 0, -1.2);
    
    return new THREE.ExtrudeGeometry(shape, {
      depth: 0.05,
      bevelEnabled: true,
      bevelThickness: 0.02,
      bevelSize: 0.02,
      bevelSegments: 3,
    });
  }, []);

  // Disease spots geometry
  const spot1 = useMemo(() => {
    const shape = new THREE.Shape();
    shape.absarc(0, 0, 0.25, 0, Math.PI * 2, false);
    return new THREE.ExtrudeGeometry(shape, { depth: 0.06, bevelEnabled: false });
  }, []);

  const spot2 = useMemo(() => {
    const shape = new THREE.Shape();
    shape.absarc(0, 0, 0.18, 0, Math.PI * 2, false);
    return new THREE.ExtrudeGeometry(shape, { depth: 0.06, bevelEnabled: false });
  }, []);

  useFrame(({ clock }) => {
    if (!groupRef.current) return;
    // Rotate the leaf continuously like a looping video
    groupRef.current.rotation.y = clock.elapsedTime * 0.5;
    groupRef.current.rotation.x = Math.sin(clock.elapsedTime * 0.5) * 0.15;
    groupRef.current.rotation.z = Math.cos(clock.elapsedTime * 0.3) * 0.1;

    // Scan line moves up and down
    if (scanLineRef.current) {
      scanLineRef.current.position.y = Math.sin(clock.elapsedTime * 1.5) * 1.3;
    }
  });

  return (
    <group ref={groupRef}>
      {/* Healthy Green Leaf */}
      <mesh geometry={leafGeometry}>
        <meshStandardMaterial
          color="#2dd475"
          emissive="#1a7a3a"
          emissiveIntensity={0.2}
          roughness={0.5}
        />
      </mesh>

      {/* Disease Spot 1 (Red/Orange) */}
      <mesh geometry={spot1} position={[0.2, 0.3, 0.01]}>
        <meshStandardMaterial
          color="#ef4444"
          emissive="#b91c1c"
          emissiveIntensity={0.5}
          roughness={0.8}
        />
      </mesh>

      {/* Disease Spot 2 (Red/Orange) */}
      <mesh geometry={spot2} position={[-0.3, -0.3, 0.01]}>
        <meshStandardMaterial
          color="#ef4444"
          emissive="#b91c1c"
          emissiveIntensity={0.5}
          roughness={0.8}
        />
      </mesh>

      {/* Center vein */}
      <mesh position={[0, 0.1, 0.05]}>
        <cylinderGeometry args={[0.015, 0.005, 2.4, 6]} />
        <meshStandardMaterial color="#1a9e4a" />
      </mesh>

      {/* Scanning Laser Ring */}
      <mesh ref={scanLineRef} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.8, 0.015, 16, 64]} />
        <meshStandardMaterial
          color="#3b82f6"
          emissive="#3b82f6"
          emissiveIntensity={2}
          transparent
          opacity={0.8}
        />
      </mesh>
    </group>
  );
}

const MiniScene3D = () => (
  <div className="w-full h-full">
    <Canvas camera={{ position: [0, 0, 4], fov: 50 }} dpr={[1, 1.5]}>
      <OrbitControls enableZoom={false} />
      <ambientLight intensity={0.5} />
      <pointLight position={[2, 2, 2]} intensity={0.8} color="#ffffff" />
      <Float speed={2} floatIntensity={0.5}>
        <DiseasedLeaf />
      </Float>
    </Canvas>
  </div>
);

export default MiniScene3D;
