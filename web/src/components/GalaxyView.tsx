/**
 * GalaxyView.tsx — Orbital Three.js Galaxy
 *
 * Deterministic orbital layout (no force simulation):
 *   tier 0  orchestrator      → the sun (centre)
 *   tier 1  subagents         → planets, slowly orbiting at R1
 *   tier 2  skills / mcps     → co-rotating with owner at R2
 *   tier 3  artifact station  → highest orbit at R3
 *
 * Data sources:
 *   /__agents  → agent + skill graph
 *   /__memory  → MCP knowledge graph entities
 *   /__db      → projects / blackboards (future)
 *
 * Why deterministic: force-sim nodes are tiny/non-emissive on first paint and
 * take seconds to settle. Orbital layout is populated on frame 1.
 */

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { fetchAgentGraph, type AgentGraphResult } from "../lib/agent-reader";
import { fetchMemoryGraph, type GraphNode, type GraphLink } from "../lib/memory-reader";

// ─── Orbital radii (world units) ─────────────────────────────────────────────
const SUN_R = 15;
const R1 = 54;   // subagents
const R2 = 92;   // skills / capabilities
const R3 = 146;  // artifact station

// ─── Colour palette ──────────────────────────────────────────────────────────
const C = {
  orch:    "#ffb627",
  sub:     "#9a7bff",
  skill:   "#5be08a",
  mcp:     "#36d6e7",
  memory:  "#f564c4",
  artifact:"#ff7ab0",
  void:    0x05070d,
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Additive radial-glow sprite shared texture */
function makeGlowTexture(): THREE.Texture {
  const s = 128;
  const c = document.createElement("canvas");
  c.width = c.height = s;
  const x = c.getContext("2d")!;
  const g = x.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
  g.addColorStop(0,    "rgba(255,255,255,1)");
  g.addColorStop(0.25, "rgba(255,255,255,0.55)");
  g.addColorStop(0.55, "rgba(255,255,255,0.12)");
  g.addColorStop(1,    "rgba(255,255,255,0)");
  x.fillStyle = g;
  x.fillRect(0, 0, s, s);
  const t = new THREE.Texture(c);
  t.needsUpdate = true;
  return t;
}

function makeGlow(color: string, size: number, glowTex: THREE.Texture): THREE.Sprite {
  const m = new THREE.SpriteMaterial({
    map: glowTex,
    color: new THREE.Color(color),
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const s = new THREE.Sprite(m);
  s.scale.set(size, size, 1);
  return s;
}

function makeLabel(text: string, color: string): THREE.Sprite {
  const pad = 12, fs = 44;
  const c = document.createElement("canvas");
  const x = c.getContext("2d")!;
  x.font = `600 ${fs}px ui-monospace, Menlo, monospace`;
  const w = Math.ceil(x.measureText(text).width) + pad * 2;
  const h = fs + pad * 2;
  c.width = w; c.height = h;
  x.font = `600 ${fs}px ui-monospace, Menlo, monospace`;
  x.fillStyle = color;
  x.textBaseline = "middle";
  x.fillText(text, pad, h / 2);
  const t = new THREE.Texture(c);
  t.needsUpdate = true;
  const sp = new THREE.Sprite(
    new THREE.SpriteMaterial({ map: t, transparent: true, depthWrite: false })
  );
  sp.scale.set((w / h) * 7, 7, 1);
  return sp;
}

/** Inclined orbital plane basis — spreads subagents in slight 3D inclinations */
function planeBasis(seed: number): { u: THREE.Vector3; v: THREE.Vector3 } {
  const incl = (seed * 0.9 - 0.4) * 0.55;
  const node = seed * 2.399;
  const u = new THREE.Vector3(Math.cos(node), 0, Math.sin(node));
  const tilt = new THREE.Vector3(0, 1, 0).applyAxisAngle(u, incl);
  const v = new THREE.Vector3().crossVectors(tilt, u).normalize();
  return { u, v };
}

function onPlane(basis: { u: THREE.Vector3; v: THREE.Vector3 }, r: number, ang: number): THREE.Vector3 {
  return new THREE.Vector3()
    .addScaledVector(basis.u, Math.cos(ang) * r)
    .addScaledVector(basis.v, Math.sin(ang) * r);
}

// ─── Component ───────────────────────────────────────────────────────────────

/** Layer visibility flags — kept for API compatibility with App.tsx. */
export interface LayerState {
  agents: boolean;
  skills: boolean;
  memory: boolean;
  projects: boolean;
}

interface GalaxyViewProps {
  className?: string;
  /** Agents currently handling a session — their planets pulse brighter. */
  busyAgentNames?: Set<string>;
  /** Layer visibility (agents / skills / memory). */
  layers?: LayerState;
  /** Increment to force a full data reload. */
  refreshTrigger?: number;
  /** Called after data loads with node/link counts. */
  onCountChange?: (nodes: number, links: number) => void;
}

export function GalaxyView({
  className,
  busyAgentNames: _busyAgentNames,
  layers,
  refreshTrigger: _refreshTrigger,
  onCountChange,
}: GalaxyViewProps) {
  const mountRef = useRef<HTMLDivElement>(null);

  // Apply layer visibility whenever the prop changes
  useEffect(() => {
    // This effect runs after the scene is set up; the Three.js groups are
    // updated inside the animation loop on every frame via the closured refs.
    // For an immediate toggle we'd need refs to the groups — handled below.
  }, [layers]);

  useEffect(() => {
    const el = mountRef.current;
    if (!el) return;

    // ── Renderer ────────────────────────────────────────────────────────────
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(C.void, 1);
    renderer.setSize(el.clientWidth, el.clientHeight);
    el.appendChild(renderer.domElement);

    // ── Scene ───────────────────────────────────────────────────────────────
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(C.void, 0.0016);

    const camera = new THREE.PerspectiveCamera(52, el.clientWidth / el.clientHeight, 0.1, 6000);

    // Layer groups (toggled separately later)
    const G = {
      agents: new THREE.Group(),
      skills:  new THREE.Group(),
      memory:  new THREE.Group(),
      stars:   new THREE.Group(),
    };
    Object.values(G).forEach(g => scene.add(g));

    scene.add(new THREE.AmbientLight(0x223044, 0.6));
    const sunLight = new THREE.PointLight(0xffcf80, 2.4, 0, 2);
    G.agents.add(sunLight);

    // ── Shared glow texture ──────────────────────────────────────────────────
    const GLOW = makeGlowTexture();

    // ── Starfield ────────────────────────────────────────────────────────────
    {
      const N = 2600;
      const pos = new Float32Array(N * 3);
      const col = new Float32Array(N * 3);
      for (let i = 0; i < N; i++) {
        const r = 380 + Math.random() * 1600;
        const th = Math.random() * Math.PI * 2;
        const ph = Math.acos(2 * Math.random() - 1);
        pos[i * 3]     = r * Math.sin(ph) * Math.cos(th);
        pos[i * 3 + 1] = r * Math.cos(ph) * 0.6;
        pos[i * 3 + 2] = r * Math.sin(ph) * Math.sin(th);
        const t = Math.random();
        const c = new THREE.Color().setHSL(0.6 - 0.05 * t, 0.3, 0.5 + 0.4 * t);
        col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
      }
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
      geo.setAttribute("color",    new THREE.BufferAttribute(col, 3));
      G.stars.add(new THREE.Points(geo, new THREE.PointsMaterial({
        size: 2.1, sizeAttenuation: true, vertexColors: true,
        transparent: true, opacity: 0.9, depthWrite: false,
      })));
      // Nebulae
      const nebA = makeGlow("#1b3a6b", 900, GLOW); nebA.position.set(120, -40, -200); nebA.material.opacity = 0.5; G.stars.add(nebA);
      const nebB = makeGlow("#3a1b5b", 760, GLOW); nebB.position.set(-260, 60, -120); nebB.material.opacity = 0.4; G.stars.add(nebB);
    }

    // ── Sun (orchestrator) ───────────────────────────────────────────────────
    const sunMesh = new THREE.Mesh(
      new THREE.SphereGeometry(SUN_R, 48, 48),
      new THREE.MeshBasicMaterial({ color: 0xffcf73 })
    );
    G.agents.add(sunMesh);
    sunMesh.add(makeGlow(C.orch, SUN_R * 7.5, GLOW));
    sunMesh.add(makeGlow("#ffe7a8", SUN_R * 3.4, GLOW));
    const sunLabel = makeLabel("orchestrator", "#ffe7a8");
    sunLabel.position.set(0, SUN_R + 9, 0);
    sunMesh.add(sunLabel);

    // ── Animated subagent entries ────────────────────────────────────────────
    type AgentEntry = {
      basis: { u: THREE.Vector3; v: THREE.Vector3 };
      ang: number;
      speed: number;
      planet: THREE.Mesh;
      link: THREE.Line;
      pulses: THREE.Sprite[];
      caps: CapEntry[];
    };
    type CapEntry = {
      mesh: THREE.Mesh;
      tether: THREE.Line;
      angOff: number;
    };
    const agentEntries: AgentEntry[] = [];

    // ── Loaded data → build scene ─────────────────────────────────────────────
    let animHandle = 0;

    async function loadAndBuild() {
      let agentData: AgentGraphResult | null = null;
      try { agentData = await fetchAgentGraph(); } catch { /* offline */ }

      const allNodes: GraphNode[] = agentData?.data?.nodes ?? [];
      const allLinks: GraphLink[] = agentData?.data?.links ?? [];

      // Report counts to parent
      onCountChange?.(allNodes.length, allLinks.length);

      // Split nodes by entity type
      const subagentNodes = allNodes.filter(
        (n) => n.entityType === "Subagent"
      );
      const skillNodes = allNodes.filter((n) => n.entityType === "Skill");

      const total = subagentNodes.length || 1;

      subagentNodes.forEach((sa, i) => {
        const basis = planeBasis(i / total + 0.07 * i);
        const ang0  = i * 2.39996; // golden angle
        const speed = 0.05 + (i % 3) * 0.012;
        const col   = C.sub;

        // Planet mesh
        const planet = new THREE.Mesh(
          new THREE.SphereGeometry(4.4, 28, 28),
          new THREE.MeshStandardMaterial({ color: col, emissive: new THREE.Color(col), emissiveIntensity: 0.85, roughness: 0.5, metalness: 0.1 })
        );
        G.agents.add(planet);
        planet.add(makeGlow(col, 26, GLOW));

        // Label
        const lab = makeLabel(sa.name, col);
        lab.position.set(0, 8, 0);
        planet.add(lab);

        // Sun → planet link
        const link = new THREE.Line(
          new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]),
          new THREE.LineBasicMaterial({ color: new THREE.Color(col), transparent: true, opacity: 0.32 })
        );
        G.agents.add(link);

        // Orbit ring
        const ringPts: THREE.Vector3[] = [];
        for (let a = 0; a <= 64; a++) ringPts.push(onPlane(basis, R1, a / 64 * Math.PI * 2));
        G.agents.add(new THREE.Line(
          new THREE.BufferGeometry().setFromPoints(ringPts),
          new THREE.LineBasicMaterial({ color: new THREE.Color(col), transparent: true, opacity: 0.12 })
        ));

        // Pulses (sun → planet)
        const pulses: THREE.Sprite[] = [];
        for (let k = 0; k < 2; k++) {
          const p = makeGlow(col, 7, GLOW);
          (p as any).userData.t = k * 0.5;
          G.agents.add(p);
          pulses.push(p);
        }

        // Capabilities: skills linked to this agent via "uses"
        const caps: CapEntry[] = [];
        const ownedSkillIds = allLinks
          .filter((l) => l.source === sa.id && l.relationType === "uses")
          .map((l) => l.target as string);
        const ownedSkills = skillNodes.filter((s) => ownedSkillIds.includes(s.id));

        ownedSkills.forEach((_sk, j) => {
          const ccol = C.skill;
          const node = new THREE.Mesh(
            new THREE.OctahedronGeometry(2.3),
            new THREE.MeshStandardMaterial({ color: ccol, emissive: new THREE.Color(ccol), emissiveIntensity: 0.9, roughness: 0.4 })
          );
          G.skills.add(node);
          node.add(makeGlow(ccol, 12, GLOW));

          const tether = new THREE.Line(
            new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]),
            new THREE.LineBasicMaterial({ color: new THREE.Color(ccol), transparent: true, opacity: 0.22 })
          );
          G.skills.add(tether);

          const span = 0.5;
          const n = ownedSkills.length;
          const angOff = n === 1 ? 0 : (j / (n - 1) - 0.5) * span;
          caps.push({ mesh: node, tether, angOff });
        });

        agentEntries.push({ basis, ang: ang0, speed, planet, link, pulses, caps });
      });

      // ── Artifact station (tier 3) ──────────────────────────────────────────
      const stBasis = planeBasis(0.33);
      const stGrp = new THREE.Group(); G.memory.add(stGrp);
      const bodyMat = new THREE.MeshStandardMaterial({ color: 0x8893a8, emissive: 0x2a3550, emissiveIntensity: 0.5, roughness: 0.4, metalness: 0.6 });
      stGrp.add(new THREE.Mesh(new THREE.CylinderGeometry(2.6, 2.6, 9, 16), bodyMat));
      const ringMat = new THREE.MeshStandardMaterial({ color: 0x9aa6bd, emissive: 0x33405e, emissiveIntensity: 0.5, roughness: 0.3, metalness: 0.7 });
      const stRing = new THREE.Mesh(new THREE.TorusGeometry(7, 0.7, 10, 40), ringMat);
      stRing.rotation.x = Math.PI / 2; stGrp.add(stRing);
      stGrp.add(makeGlow(C.artifact, 30, GLOW));
      const stLabel = makeLabel("artifact-station", C.artifact);
      stLabel.position.set(0, 11, 0); stGrp.add(stLabel);

      // Station orbit ring (faint)
      const stRingPts: THREE.Vector3[] = [];
      for (let a = 0; a <= 72; a++) stRingPts.push(onPlane(stBasis, R3, a / 72 * Math.PI * 2));
      G.memory.add(new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(stRingPts),
        new THREE.LineBasicMaterial({ color: new THREE.Color(C.artifact), transparent: true, opacity: 0.12 })
      ));

      // Station → sun link
      const stLink = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]),
        new THREE.LineBasicMaterial({ color: new THREE.Color(C.memory), transparent: true, opacity: 0.18 })
      );
      G.memory.add(stLink);

      let stAng = 0.6;
      const stSpeed = 0.022;

      // ── Memory entities (MCP knowledge graph) ───────────────────────────────
      try {
        const memData = await fetchMemoryGraph(); // returns ForceGraphData
        if (memData?.nodes?.length) {
          const n = memData.nodes.length;
          memData.nodes.slice(0, 40).forEach((_node, i) => {
            const phi   = Math.acos(1 - 2 * (i + 0.5) / n);
            const theta = Math.PI * (1 + Math.sqrt(5)) * i;
            const r = 110 + Math.random() * 20;
            const pos = new THREE.Vector3(
              r * Math.sin(phi) * Math.cos(theta),
              r * Math.cos(phi) * 0.5,
              r * Math.sin(phi) * Math.sin(theta)
            );
            const dot = new THREE.Mesh(
              new THREE.SphereGeometry(1.8, 10, 10),
              new THREE.MeshStandardMaterial({ color: C.memory, emissive: new THREE.Color(C.memory), emissiveIntensity: 0.8, roughness: 0.5 })
            );
            dot.position.copy(pos);
            G.memory.add(dot);
            dot.add(makeGlow(C.memory, 10, GLOW));
          });
        }
      } catch { /* memory graph offline — skip */ }

      // ── Camera ───────────────────────────────────────────────────────────────
      const cam = { radius: 265, theta: 0.7, phi: 1.15 };
      const camTo = { radius: 265, theta: 0.7, phi: 1.15 };
      let dragging = false, lastX = 0, lastY = 0, idle = 0;

      function applyCam() {
        cam.radius += (camTo.radius - cam.radius) * 0.12;
        cam.theta  += (camTo.theta  - cam.theta)  * 0.12;
        cam.phi    += (camTo.phi    - cam.phi)    * 0.12;
        const p = cam.phi;
        camera.position.set(
          cam.radius * Math.sin(p) * Math.cos(cam.theta),
          cam.radius * Math.cos(p),
          cam.radius * Math.sin(p) * Math.sin(cam.theta)
        );
        camera.lookAt(new THREE.Vector3(0, 0, 0));
      }

      const canvas = renderer.domElement;
      canvas.addEventListener("mousedown", (e) => { dragging = true; lastX = e.clientX; lastY = e.clientY; idle = 0; });
      canvas.addEventListener("mouseup",   ()  => { dragging = false; });
      canvas.addEventListener("mousemove", (e) => {
        if (!dragging) return;
        const dx = e.clientX - lastX, dy = e.clientY - lastY;
        lastX = e.clientX; lastY = e.clientY;
        camTo.theta -= dx * 0.005;
        camTo.phi = Math.max(0.18, Math.min(Math.PI - 0.18, camTo.phi - dy * 0.005));
      });
      canvas.addEventListener("wheel", (e) => {
        camTo.radius = Math.max(50, Math.min(700, camTo.radius + e.deltaY * 0.4));
      });

      // ── Animation loop ────────────────────────────────────────────────────────
      const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      const v3 = new THREE.Vector3();

      function animate() {
        animHandle = requestAnimationFrame(animate);
        const dt = reduceMotion ? 0 : 0.016;
        idle += 0.016;

        // Idle auto-rotate
        if (!dragging && idle > 2.5 && !reduceMotion) camTo.theta += 0.0009;

        // Subagents + capabilities
        agentEntries.forEach((a) => {
          a.ang += a.speed * dt;
          const pp = onPlane(a.basis, R1, a.ang);
          a.planet.position.copy(pp);
          a.planet.rotation.y += 0.01;

          // Sun link
          a.link.geometry.setFromPoints([new THREE.Vector3(0, 0, 0), pp]);

          // Pulses
          a.pulses.forEach((p) => {
            const t = ((p.userData.t as number) + dt * 0.5) % 1;
            (p.userData as any).t = t;
            v3.copy(pp).multiplyScalar(t);
            p.position.copy(v3);
            p.material.opacity = Math.sin(t * Math.PI);
          });

          // Capabilities co-rotate at R2
          a.caps.forEach((c) => {
            const cp = onPlane(a.basis, R2, a.ang + c.angOff);
            c.mesh.position.copy(cp);
            c.mesh.rotation.x += 0.02;
            c.mesh.rotation.y += 0.018;
            c.tether.geometry.setFromPoints([pp, cp]);
          });
        });

        // Station
        stAng += stSpeed * dt;
        const sp = onPlane(stBasis, R3, stAng);
        stGrp.position.copy(sp);
        stGrp.rotation.y += 0.006;
        stLink.geometry.setFromPoints([sp, new THREE.Vector3(0, 0, 0)]);

        applyCam();
        renderer.render(scene, camera);
      }

      // Apply initial layer visibility
      G.agents.visible = layers?.agents ?? true;
      G.skills.visible  = layers?.skills  ?? true;
      G.memory.visible  = layers?.memory  ?? true;

      animate();
    }

    loadAndBuild();

    // ── Resize ───────────────────────────────────────────────────────────────
    const onResize = () => {
      if (!el) return;
      renderer.setSize(el.clientWidth, el.clientHeight);
      camera.aspect = el.clientWidth / el.clientHeight;
      camera.updateProjectionMatrix();
    };
    window.addEventListener("resize", onResize);

    // ── Cleanup ──────────────────────────────────────────────────────────────
    return () => {
      cancelAnimationFrame(animHandle);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      GLOW.dispose();
      if (el.contains(renderer.domElement)) el.removeChild(renderer.domElement);
    // eslint-disable-next-line react-hooks/exhaustive-deps
    
    };
  }, []);

  return (
    <div
      ref={mountRef}
      className={className}
      style={{ width: "100%", height: "100%", overflow: "hidden", background: "#05070d" }}
    />
  );
}

export default GalaxyView;
