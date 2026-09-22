import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import './Cyber3DVisualizer.css';

export default function Cyber3DVisualizer({ telemetry, onSelectAgent }) {
  const mountRef = useRef(null);
  const [cameraMode, setCameraMode] = useState('TACTICAL'); // TACTICAL, TOPDOWN, ATTACKER, CORE

  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);
  const objectsRef = useRef({
    attacker: null,
    attackerLight: null,
    agent1: null,
    agent2: null,
    agent3: null,
    shieldA: null,
    shieldB: null,
    shieldC: null,
    criticalCore: null,
    criticalLight: null,
    links: [],
    packets: [],
    particles: null
  });

  const mouseRef = useRef({ isDragging: false, prevX: 0, prevY: 0, rotX: 0.3, rotY: -0.4, zoom: 14 });

  useEffect(() => {
    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight;

    // 1. Scene & Camera
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x060913);
    scene.fog = new THREE.FogExp2(0x060913, 0.035);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 4, 14);
    cameraRef.current = camera;

    // 2. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // 3. Lighting
    const ambientLight = new THREE.AmbientLight(0x1e293b, 1.5);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x00f0ff, 1.2);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // 4. Cyber Grid Floor
    const gridHelper = new THREE.GridHelper(26, 26, 0x00f0ff, 0x1e293b);
    gridHelper.position.y = -5.5;
    scene.add(gridHelper);

    // 5. Ambient Cyber Dust Particles
    const particleGeo = new THREE.BufferGeometry();
    const particleCount = 200;
    const posArray = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount * 3; i++) {
      posArray[i] = (Math.random() - 0.5) * 22;
    }
    particleGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    const particleMat = new THREE.PointsMaterial({
      size: 0.08,
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.6
    });
    const particles = new THREE.Points(particleGeo, particleMat);
    scene.add(particles);
    objectsRef.current.particles = particles;

    // Helper: Create Agent Platform & Orb
    const createAgentNode = (x, y, z, colorHex) => {
      const group = new THREE.Group();
      group.position.set(x, y, z);

      // Base Platform
      const baseGeo = new THREE.CylinderGeometry(1.2, 1.3, 0.25, 6);
      const baseMat = new THREE.MeshStandardMaterial({
        color: 0x0f172a,
        roughness: 0.3,
        metalness: 0.8
      });
      const base = new THREE.Mesh(baseGeo, baseMat);
      group.add(base);

      // Platform Ring Wireframe
      const ringGeo = new THREE.RingGeometry(1.25, 1.35, 6);
      const ringMat = new THREE.MeshBasicMaterial({ color: colorHex, side: THREE.DoubleSide });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.rotation.x = Math.PI / 2;
      ring.position.y = 0.14;
      group.add(ring);

      // Floating Defender Core Orb
      const orbGeo = new THREE.IcosahedronGeometry(0.5, 2);
      const orbMat = new THREE.MeshStandardMaterial({
        color: colorHex,
        emissive: colorHex,
        emissiveIntensity: 0.6,
        roughness: 0.1,
        metalness: 0.9
      });
      const orb = new THREE.Mesh(orbGeo, orbMat);
      orb.position.y = 0.9;
      group.add(orb);

      // Orbiting Defense Ring
      const orbitRingGeo = new THREE.TorusGeometry(0.75, 0.02, 8, 32);
      const orbitRingMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff });
      const orbitRing = new THREE.Mesh(orbitRingGeo, orbitRingMat);
      orbitRing.rotation.x = Math.PI / 3;
      orbitRing.position.y = 0.9;
      group.add(orbitRing);

      // Isolation Shield (Hidden by default)
      const shieldGeo = new THREE.SphereGeometry(1.3, 24, 24);
      const shieldMat = new THREE.MeshStandardMaterial({
        color: 0xf59e0b,
        emissive: 0xf59e0b,
        emissiveIntensity: 0.3,
        transparent: true,
        opacity: 0.0,
        wireframe: true
      });
      const shield = new THREE.Mesh(shieldGeo, shieldMat);
      shield.position.y = 0.8;
      group.add(shield);

      scene.add(group);
      return { group, orb, orbitRing, shield };
    };

    // 6. Build Nodes
    // Attacker Node (Top)
    const attackerGroup = new THREE.Group();
    attackerGroup.position.set(0, 4.2, 0);
    const attGeo = new THREE.OctahedronGeometry(0.75, 0);
    const attMat = new THREE.MeshStandardMaterial({
      color: 0xef4444,
      emissive: 0xef4444,
      emissiveIntensity: 0.8,
      wireframe: true
    });
    const attMesh = new THREE.Mesh(attGeo, attMat);
    attackerGroup.add(attMesh);

    const attCoreGeo = new THREE.SphereGeometry(0.3, 16, 16);
    const attCoreMat = new THREE.MeshBasicMaterial({ color: 0xff0000 });
    const attCore = new THREE.Mesh(attCoreGeo, attCoreMat);
    attackerGroup.add(attCore);

    const attackerLight = new THREE.PointLight(0xef4444, 2, 8);
    attackerGroup.add(attackerLight);
    scene.add(attackerGroup);

    objectsRef.current.attacker = attackerGroup;
    objectsRef.current.attackerLight = attackerLight;

    // 3 Agent Nodes
    const a1 = createAgentNode(-4.0, 1.8, 0, 0x00f0ff);
    const a2 = createAgentNode(0.0, -0.2, 0, 0x3b82f6);
    const a3 = createAgentNode(4.0, -2.2, 0, 0x8b5cf6);

    objectsRef.current.agent1 = a1;
    objectsRef.current.agent2 = a2;
    objectsRef.current.agent3 = a3;

    // Critical Server Node (Bottom Center)
    const critGroup = new THREE.Group();
    critGroup.position.set(0, -4.5, 0);
    const critGeo = new THREE.BoxGeometry(1.6, 1.4, 1.6);
    const critMat = new THREE.MeshStandardMaterial({
      color: 0x1e3a8a,
      emissive: 0x3b82f6,
      emissiveIntensity: 0.4,
      roughness: 0.2,
      metalness: 0.9
    });
    const critMesh = new THREE.Mesh(critGeo, critMat);
    critGroup.add(critMesh);

    const critRingGeo = new THREE.TorusGeometry(1.2, 0.04, 8, 32);
    const critRingMat = new THREE.MeshBasicMaterial({ color: 0x60a5fa });
    const critRing = new THREE.Mesh(critRingGeo, critRingMat);
    critRing.rotation.x = Math.PI / 2;
    critGroup.add(critRing);

    const criticalLight = new THREE.PointLight(0x3b82f6, 2, 8);
    critGroup.add(criticalLight);
    scene.add(critGroup);

    objectsRef.current.criticalCore = { group: critGroup, mesh: critMesh, ring: critRing };
    objectsRef.current.criticalLight = criticalLight;

    // 7. Network Energy Conduits (Lines between nodes)
    const createBeam = (p1, p2, colorHex) => {
      const lineGeo = new THREE.BufferGeometry().setFromPoints([p1, p2]);
      const lineMat = new THREE.LineDashedMaterial({
        color: colorHex,
        linewidth: 2,
        scale: 1,
        dashSize: 0.3,
        gapSize: 0.15
      });
      const line = new THREE.Line(lineGeo, lineMat);
      line.computeLineDistances();
      scene.add(line);
      return line;
    };

    const link1 = createBeam(new THREE.Vector3(0, 4.2, 0), new THREE.Vector3(-4.0, 1.8, 0), 0x334155);
    const link2 = createBeam(new THREE.Vector3(-4.0, 1.8, 0), new THREE.Vector3(0.0, -0.2, 0), 0x334155);
    const link3 = createBeam(new THREE.Vector3(0.0, -0.2, 0), new THREE.Vector3(4.0, -2.2, 0), 0x334155);
    const link4 = createBeam(new THREE.Vector3(4.0, -2.2, 0), new THREE.Vector3(0, -4.5, 0), 0x334155);

    objectsRef.current.links = [link1, link2, link3, link4];

    // 8. Animation & Render Loop
    let clock = new THREE.Clock();
    let animId = null;

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const delta = clock.getDelta();
      const elapsed = clock.getElapsedTime();

      // Rotate Attacker
      if (objectsRef.current.attacker) {
        objectsRef.current.attacker.rotation.y += 1.2 * delta;
        objectsRef.current.attacker.rotation.x += 0.8 * delta;
      }

      // Rotate Agent orbital rings & floating bounce
      [a1, a2, a3].forEach((agentObj, idx) => {
        if (agentObj) {
          agentObj.orbitRing.rotation.z += (1.5 + idx * 0.4) * delta;
          agentObj.orb.position.y = 0.9 + Math.sin(elapsed * 2 + idx) * 0.08;
          agentObj.orbitRing.position.y = agentObj.orb.position.y;
        }
      });

      // Rotate Critical Server Ring
      if (objectsRef.current.criticalCore) {
        objectsRef.current.criticalCore.ring.rotation.z += 0.6 * delta;
      }

      // Dust particle slow drift
      if (particles) {
        particles.rotation.y = elapsed * 0.03;
      }

      // Smooth camera interpolation based on mouse orbit
      const targetX = Math.sin(mouseRef.current.rotY) * mouseRef.current.zoom;
      const targetZ = Math.cos(mouseRef.current.rotY) * mouseRef.current.zoom;
      const targetY = mouseRef.current.rotX * 6 + 1;

      camera.position.x += (targetX - camera.position.x) * 0.08;
      camera.position.y += (targetY - camera.position.y) * 0.08;
      camera.position.z += (targetZ - camera.position.z) * 0.08;
      camera.lookAt(0, -0.4, 0);

      renderer.render(scene, camera);
    };

    animate();

    // 9. Window Resize Handling
    const handleResize = () => {
      if (!mountRef.current) return;
      const w = mountRef.current.clientWidth;
      const h = mountRef.current.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  // Update 3D Visual States when live Telemetry changes
  useEffect(() => {
    if (!telemetry || !objectsRef.current.agent1) return;
    const { environment } = telemetry;
    const segs = environment.segments || {};
    const attLoc = environment.attacker_location;
    const critical = environment.critical_resource || {};

    const a1 = objectsRef.current.agent1;
    const a2 = objectsRef.current.agent2;
    const a3 = objectsRef.current.agent3;
    const att = objectsRef.current.attacker;
    const crit = objectsRef.current.criticalCore;

    // Update Segments & Shields
    const segA = segs['Segment A'] || {};
    const segB = segs['Segment B'] || {};
    const segC = segs['Segment C'] || {};

    // Segment A Shield
    if (a1.shield) {
      a1.shield.material.opacity = segA.isolated ? 0.65 : 0.0;
      a1.orb.material.emissive.setHex(segA.threat_level > 0.5 ? 0xef4444 : 0x00f0ff);
    }
    // Segment B Shield
    if (a2.shield) {
      a2.shield.material.opacity = segB.isolated ? 0.65 : 0.0;
      a2.orb.material.emissive.setHex(segB.threat_level > 0.5 ? 0xef4444 : 0x3b82f6);
    }
    // Segment C Shield
    if (a3.shield) {
      a3.shield.material.opacity = segC.isolated ? 0.65 : 0.0;
      a3.orb.material.emissive.setHex(segC.threat_level > 0.5 ? 0xef4444 : 0x8b5cf6);
    }

    // Dynamic Attacker Position based on current location
    if (att) {
      if (attLoc === 'Segment A') {
        att.position.set(-3.8, 3.2, 0);
      } else if (attLoc === 'Segment B') {
        att.position.set(0.0, 1.2, 0);
      } else if (attLoc === 'Segment C') {
        att.position.set(3.8, -0.8, 0);
      } else {
        att.position.set(0, 4.2, 0);
      }
    }

    // Critical Server compromised state
    if (crit && crit.mesh) {
      if (critical.compromised) {
        crit.mesh.material.emissive.setHex(0xef4444);
        crit.ring.material.color.setHex(0xff0000);
        objectsRef.current.criticalLight.color.setHex(0xef4444);
      } else {
        crit.mesh.material.emissive.setHex(0x3b82f6);
        crit.ring.material.color.setHex(0x60a5fa);
        objectsRef.current.criticalLight.color.setHex(0x3b82f6);
      }
    }

    // Conduit Link Colors
    const links = objectsRef.current.links;
    if (links.length >= 4) {
      links[0].material.color.setHex(attLoc === 'Segment A' ? 0xef4444 : 0x334155);
      links[1].material.color.setHex(attLoc === 'Segment B' ? 0xef4444 : 0x334155);
      links[2].material.color.setHex(attLoc === 'Segment C' ? 0xef4444 : 0x334155);
      links[3].material.color.setHex(critical.compromised ? 0xef4444 : 0x334155);
    }
  }, [telemetry]);

  // Mouse Controls for 3D Orbiting
  const handleMouseDown = (e) => {
    mouseRef.current.isDragging = true;
    mouseRef.current.prevX = e.clientX;
    mouseRef.current.prevY = e.clientY;
  };

  const handleMouseMove = (e) => {
    if (!mouseRef.current.isDragging) return;
    const dx = e.clientX - mouseRef.current.prevX;
    const dy = e.clientY - mouseRef.current.prevY;
    mouseRef.current.rotY += dx * 0.008;
    mouseRef.current.rotX = Math.max(-0.4, Math.min(1.0, mouseRef.current.rotX + dy * 0.008));
    mouseRef.current.prevX = e.clientX;
    mouseRef.current.prevY = e.clientY;
  };

  const handleMouseUp = () => {
    mouseRef.current.isDragging = false;
  };

  const handleWheel = (e) => {
    e.preventDefault();
    mouseRef.current.zoom = Math.max(7, Math.min(22, mouseRef.current.zoom + e.deltaY * 0.01));
  };

  // Camera preset selectors
  const setCameraPreset = (mode) => {
    setCameraMode(mode);
    if (mode === 'TACTICAL') {
      mouseRef.current.rotX = 0.3;
      mouseRef.current.rotY = -0.4;
      mouseRef.current.zoom = 14;
    } else if (mode === 'TOPDOWN') {
      mouseRef.current.rotX = 0.95;
      mouseRef.current.rotY = 0.0;
      mouseRef.current.zoom = 16;
    } else if (mode === 'ATTACKER') {
      mouseRef.current.rotX = -0.1;
      mouseRef.current.rotY = 0.0;
      mouseRef.current.zoom = 10;
    } else if (mode === 'CORE') {
      mouseRef.current.rotX = 0.15;
      mouseRef.current.rotY = 3.14;
      mouseRef.current.zoom = 10;
    }
  };

  return (
    <div
      className="cyber-3d-wrapper"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onWheel={handleWheel}
    >
      {/* 3D Canvas Mount */}
      <div className="canvas-container" ref={mountRef} />

      {/* 3D HUD OVERLAY */}
      <div className="cyber-hud-top">
        <div className="hud-badge">
          <span className="hud-pulse"></span> LIVE 3D NEURAL TOPOLOGY
        </div>
        <div className="camera-presets">
          {['TACTICAL', 'TOPDOWN', 'ATTACKER', 'CORE'].map((m) => (
            <button
              key={m}
              className={`preset-btn ${cameraMode === m ? 'active' : ''}`}
              onClick={(e) => { e.stopPropagation(); setCameraPreset(m); }}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      <div className="cyber-hud-instructions">
        <span>🖱️ Drag to Orbit | Scroll to Zoom</span>
      </div>

      {/* 3D Node Labels Overlay */}
      {telemetry && (
        <div className="hud-floating-labels">
          <div className="floating-badge badge-att">
            ATTACKER [{telemetry.environment.attacker_location || 'STANDBY'}]
          </div>
          <div className="floating-badge badge-a1" onClick={() => onSelectAgent && onSelectAgent(telemetry.agents[0])}>
            AGENT 1: {telemetry.agents[0]?.current_action} ({(telemetry.environment.segments['Segment A']?.threat_level * 100).toFixed(0)}%)
          </div>
          <div className="floating-badge badge-a2" onClick={() => onSelectAgent && onSelectAgent(telemetry.agents[1])}>
            AGENT 2: {telemetry.agents[1]?.current_action} ({(telemetry.environment.segments['Segment B']?.threat_level * 100).toFixed(0)}%)
          </div>
          <div className="floating-badge badge-a3" onClick={() => onSelectAgent && onSelectAgent(telemetry.agents[2])}>
            AGENT 3: {telemetry.agents[2]?.current_action} ({(telemetry.environment.segments['Segment C']?.threat_level * 100).toFixed(0)}%)
          </div>
          <div className="floating-badge badge-core">
            CRITICAL SERVER [{telemetry.environment.critical_resource?.compromised ? 'COMPROMISED' : 'SECURE'}]
          </div>
        </div>
      )}
    </div>
  );
}
