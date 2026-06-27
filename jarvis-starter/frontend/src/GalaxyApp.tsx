/**
 * GalaxyApp — deterministic orbital Three.js galaxy (Module C).
 *
 * Sun = orchestrator; planets = subagents on golden-angle inclined orbits. Every
 * body is emissive and carries an additive glow sprite over a deep-space clear
 * colour, so first paint is always populated (never the "blank galaxy"). A
 * ResizeObserver drives canvas sizing so a 0×0 first paint self-corrects. The
 * task currently `active` lights its tether. Data comes from the gateway; if it
 * is unreachable the app falls back to a small mock set so it renders standalone.
 */
import { useEffect, useRef } from "react";
import * as THREE from "three";
import {
  fetchAgents,
  fetchTasks,
  toPlanets,
  MOCK_AGENTS,
  type AgentNode,
  type TaskNode,
} from "./gateway";

const VOID = 0x05070d;
const SUN_R = 14;
const R1 = 52;

type Basis = { u: THREE.Vector3; v: THREE.Vector3 };

function glowTexture(): THREE.Texture {
  const s = 128;
  const c = document.createElement("canvas");
  c.width = c.height = s;
  const x = c.getContext("2d")!;
  const g = x.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
  g.addColorStop(0, "rgba(255,255,255,1)");
  g.addColorStop(0.25, "rgba(255,255,255,0.55)");
  g.addColorStop(0.55, "rgba(255,255,255,0.12)");
  g.addColorStop(1, "rgba(255,255,255,0)");
  x.fillStyle = g;
  x.fillRect(0, 0, s, s);
  const t = new THREE.Texture(c);
  t.needsUpdate = true;
  return t;
}

function glow(color: string, size: number, tex: THREE.Texture): THREE.Sprite {
  const m = new THREE.SpriteMaterial({
    map: tex,
    color: new THREE.Color(color),
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const sprite = new THREE.Sprite(m);
  sprite.scale.set(size, size, 1);
  return sprite;
}

function planeBasis(seed: number): Basis {
  const incl = (seed * 0.9 - 0.4) * 0.5;
  const node = seed * 2.399;
  const u = new THREE.Vector3(Math.cos(node), 0, Math.sin(node));
  const tilt = new THREE.Vector3(0, 1, 0).applyAxisAngle(u, incl);
  const v = new THREE.Vector3().crossVectors(tilt, u).normalize();
  return { u, v };
}

function onPlane(b: Basis, r: number, a: number): THREE.Vector3 {
  return new THREE.Vector3()
    .addScaledVector(b.u, Math.cos(a) * r)
    .addScaledVector(b.v, Math.sin(a) * r);
}

interface Planet {
  basis: Basis;
  ang: number;
  speed: number;
  mesh: THREE.Mesh<THREE.SphereGeometry, THREE.MeshStandardMaterial>;
  link: THREE.Line;
  agent: string;
}

export function GalaxyApp() {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = mountRef.current;
    if (!el) return;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(VOID, 1);
    renderer.setSize(Math.max(1, el.clientWidth), Math.max(1, el.clientHeight));
    el.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(VOID, 0.0016);

    const camera = new THREE.PerspectiveCamera(52, 1, 0.1, 4000);
    camera.position.set(0, 120, 230);

    scene.add(new THREE.AmbientLight(0x223044, 0.6));
    scene.add(new THREE.PointLight(0xffcf80, 2.4, 0, 2));

    const tex = glowTexture();

    // Starfield
    {
      const n = 1800;
      const pos = new Float32Array(n * 3);
      for (let i = 0; i < n; i++) {
        const r = 380 + Math.random() * 1400;
        const th = Math.random() * Math.PI * 2;
        const ph = Math.acos(2 * Math.random() - 1);
        pos[i * 3] = r * Math.sin(ph) * Math.cos(th);
        pos[i * 3 + 1] = r * Math.cos(ph) * 0.6;
        pos[i * 3 + 2] = r * Math.sin(ph) * Math.sin(th);
      }
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
      scene.add(new THREE.Points(geo, new THREE.PointsMaterial({
        size: 2, color: 0x8899bb, transparent: true, opacity: 0.85, depthWrite: false,
      })));
    }

    // Sun = orchestrator
    const sun = new THREE.Mesh(
      new THREE.SphereGeometry(SUN_R, 48, 48),
      new THREE.MeshBasicMaterial({ color: 0xffcf73 }),
    );
    scene.add(sun);
    sun.add(glow("#ffb627", SUN_R * 7, tex));

    const planets: Planet[] = [];
    let active = new Set<string>();
    let raf = 0;

    function build(agents: AgentNode[], tasks: TaskNode[]) {
      const subs = toPlanets(agents);
      active = new Set(tasks.filter((t) => t.active).map((t) => t.agent));
      subs.forEach((a, i) => {
        const basis = planeBasis(i / Math.max(1, subs.length) + 0.07 * i);
        const mesh = new THREE.Mesh(
          new THREE.SphereGeometry(4.2, 24, 24),
          new THREE.MeshStandardMaterial({
            color: a.colour,
            emissive: new THREE.Color(a.colour),
            emissiveIntensity: 0.85,
            roughness: 0.5,
          }),
        );
        scene.add(mesh);
        mesh.add(glow(a.colour, 24, tex));

        const link = new THREE.Line(
          new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]),
          new THREE.LineBasicMaterial({ color: new THREE.Color(a.colour), transparent: true, opacity: 0.3 }),
        );
        scene.add(link);

        const ring: THREE.Vector3[] = [];
        for (let k = 0; k <= 64; k++) ring.push(onPlane(basis, R1, (k / 64) * Math.PI * 2));
        scene.add(new THREE.Line(
          new THREE.BufferGeometry().setFromPoints(ring),
          new THREE.LineBasicMaterial({ color: new THREE.Color(a.colour), transparent: true, opacity: 0.12 }),
        ));

        planets.push({ basis, ang: i * 2.39996, speed: 0.05 + (i % 3) * 0.012, mesh, link, agent: a.name });
      });
    }

    function resize() {
      const w = el.clientWidth;
      const h = el.clientHeight;
      if (!w || !h) return; // not laid out yet — RO fires again
      renderer.setSize(w, h);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    }
    const ro = new ResizeObserver(resize);
    ro.observe(el);
    resize();

    function animate() {
      raf = requestAnimationFrame(animate);
      for (const p of planets) {
        p.ang += p.speed * 0.016;
        const pos = onPlane(p.basis, R1, p.ang);
        p.mesh.position.copy(pos);
        const lit = active.has(p.agent);
        (p.link.material as THREE.LineBasicMaterial).opacity = lit ? 0.9 : 0.25;
        p.mesh.material.emissiveIntensity = lit ? 1.6 : 0.85;
        p.link.geometry.setFromPoints([new THREE.Vector3(), pos]);
      }
      camera.lookAt(0, 0, 0);
      renderer.render(scene, camera);
    }

    void (async () => {
      let agents: AgentNode[];
      let tasks: TaskNode[] = [];
      try {
        agents = await fetchAgents();
        tasks = await fetchTasks();
      } catch {
        agents = MOCK_AGENTS; // gateway down → render standalone
      }
      build(agents, tasks);
      animate();
    })();

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      tex.dispose();
      renderer.dispose();
      if (el.contains(renderer.domElement)) el.removeChild(renderer.domElement);
    };
  }, []);

  return <div ref={mountRef} style={{ width: "100%", height: "100%" }} />;
}
