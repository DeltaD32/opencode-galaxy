/**
 * VoxCorona.tsx — Phase J3: Three.js particle corona layered over the Canvas2D orb.
 *
 * Renders a Three.js WebGL canvas (transparent background) absolutely positioned
 * over the orb area. Draws N particles arranged in a toroidal/ring formation
 * that:
 *   - IDLE:      slow, gentle drift — very low amplitude
 *   - LISTENING: particles scatter outward and pulse rapidly (mic input energy)
 *   - THINKING:  slow rotation, slightly tighter ring — "processing" feel
 *   - SPEAKING:  particles pulse with synthesised amplitude wave
 *
 * Sizing: matches the Canvas2D orb size prop (default 320). The Three.js canvas
 * is rendered at 2× size for retina and CSS-scaled back to `size` px.
 *
 * Performance: requestAnimationFrame loop runs at display refresh rate.
 * On unmount the renderer is disposed and the RAF is cancelled.
 */

import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import type { OrbState } from './particleState';

interface VoxCoronaProps {
  state: OrbState;
  /** Must match Canvas2DOrb size (default 320) */
  size?: number;
}

// ── Constants ─────────────────────────────────────────────────────────────────

const PARTICLE_COUNT = 180;
const TORUS_R  = 1.0;   // major radius (ring)
const TORUS_r  = 0.22;  // tube radius

// State-dependent parameters
const STATE_PARAMS: Record<OrbState, {
  speed: number;      // rotation speed rad/frame
  scatter: number;    // radial noise amplitude
  pulse: number;      // size pulse frequency (Hz approx)
  brightness: number; // particle alpha multiplier
  sizeBase: number;   // base point size
}> = {
  IDLE:      { speed: 0.003, scatter: 0.04, pulse: 0.4,  brightness: 0.22, sizeBase: 2.2 },
  LISTENING: { speed: 0.010, scatter: 0.20, pulse: 3.0,  brightness: 0.65, sizeBase: 3.2 },
  THINKING:  { speed: 0.007, scatter: 0.07, pulse: 0.8,  brightness: 0.40, sizeBase: 2.6 },
  SPEAKING:  { speed: 0.009, scatter: 0.15, pulse: 2.2,  brightness: 0.55, sizeBase: 3.0 },
};

// Theme accent colours (CSS variable fallback → hard-coded defaults per theme)
const CORONA_COLOR = new THREE.Color('#4d8df6'); // default observatory blue

// ── Component ─────────────────────────────────────────────────────────────────

export function VoxCorona({ state, size = 320 }: VoxCoronaProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  // Store mutable renderer state in a ref to survive re-renders
  const ctxRef = useRef<{
    renderer: THREE.WebGLRenderer;
    scene: THREE.Scene;
    camera: THREE.PerspectiveCamera;
    points: THREE.Points;
    basePositions: Float32Array;
    raf: number;
    clock: THREE.Clock;
    currentState: OrbState;
    targetParams: (typeof STATE_PARAMS)[OrbState];
  } | null>(null);

  // Initialise Three.js once on mount
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // ── Renderer ────────────────────────────────────────────────────────────
    const renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,          // transparent background
      antialias: true,
      powerPreference: 'high-performance',
    });
    // Let Three.js handle retina — setSize sets CSS size; setPixelRatio scales buffer
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(size, size); // sets canvas CSS width/height to size×size

    // ── Scene ────────────────────────────────────────────────────────────────
    const scene  = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 100);
    camera.position.set(0, 0.3, 4.2);
    camera.lookAt(0, 0, 0);

    // ── Geometry — torus sampling ────────────────────────────────────────────
    const positions = new Float32Array(PARTICLE_COUNT * 3);
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const u = (i / PARTICLE_COUNT) * Math.PI * 2;
      const v = Math.random() * Math.PI * 2;
      const jitter = (Math.random() - 0.5) * 0.04;
      positions[i * 3]     = (TORUS_R + (TORUS_r + jitter) * Math.cos(v)) * Math.cos(u);
      positions[i * 3 + 1] = (TORUS_R + (TORUS_r + jitter) * Math.cos(v)) * Math.sin(u);
      positions[i * 3 + 2] = (TORUS_r + jitter) * Math.sin(v);
    }

    // ── Try to read CSS accent colour ─────────────────────────────────────────
    let coronaColor = CORONA_COLOR.clone();
    try {
      const cssColor = getComputedStyle(document.documentElement)
        .getPropertyValue('--jarvis-text-accent')
        .trim();
      if (cssColor) coronaColor = new THREE.Color(cssColor);
    } catch { /* ignore */ }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions.slice(), 3));

    // ── Material ────────────────────────────────────────────────────────────
    const material = new THREE.PointsMaterial({
      color: coronaColor,
      size: STATE_PARAMS.IDLE.sizeBase,
      sizeAttenuation: true,
      transparent: true,
      opacity: STATE_PARAMS.IDLE.brightness,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });

    const points = new THREE.Points(geometry, material);
    scene.add(points);

    // ── Animation loop ──────────────────────────────────────────────────────
    const clock = new THREE.Clock();
    let currentState: OrbState = 'IDLE';
    let targetParams = STATE_PARAMS.IDLE;

    function animate() {
      const ctx = ctxRef.current;
      if (!ctx) return;

      const raf = requestAnimationFrame(animate);
      ctx.raf = raf;

      const t    = clock.getElapsedTime();
      const p    = ctx.targetParams;

      // Rotate ring
      ctx.points.rotation.y += p.speed;
      ctx.points.rotation.x  = Math.sin(t * 0.18) * 0.12;

      // Scatter positions
      const geo  = ctx.points.geometry;
      const attr = geo.attributes.position as THREE.BufferAttribute;
      const base = ctx.basePositions;

      for (let i = 0; i < PARTICLE_COUNT; i++) {
        const phase = (i / PARTICLE_COUNT) * Math.PI * 2;
        const pulse = Math.sin(t * p.pulse * 6.28 + phase) * p.scatter;
        attr.array[i * 3]     = base[i * 3]     + pulse * (Math.cos(phase));
        attr.array[i * 3 + 1] = base[i * 3 + 1] + pulse * (Math.sin(phase));
        attr.array[i * 3 + 2] = base[i * 3 + 2] + pulse * 0.5;
      }
      attr.needsUpdate = true;

      // Pulse material size
      const sizeMod = 1 + Math.sin(t * p.pulse * 6.28) * 0.18;
      (ctx.points.material as THREE.PointsMaterial).size = p.sizeBase * sizeMod;
      (ctx.points.material as THREE.PointsMaterial).opacity =
        p.brightness * (0.88 + Math.sin(t * 1.4) * 0.12);

      renderer.render(ctx.scene, ctx.camera);
    }

    ctxRef.current = {
      renderer,
      scene,
      camera,
      points,
      basePositions: positions.slice(),
      raf: 0,
      clock,
      currentState,
      targetParams,
    };

    const raf = requestAnimationFrame(animate);
    ctxRef.current.raf = raf;

    return () => {
      if (ctxRef.current) cancelAnimationFrame(ctxRef.current.raf);
      geometry.dispose();
      material.dispose();
      renderer.dispose();
      ctxRef.current = null;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // run once on mount; size is stable

  // Update target params when state changes
  useEffect(() => {
    if (!ctxRef.current) return;
    ctxRef.current.currentState = state;
    ctxRef.current.targetParams = STATE_PARAMS[state];
  }, [state]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      style={{
        position:      'absolute',
        inset:         0,
        width:         size,
        height:        size,
        pointerEvents: 'none',
      }}
    />
  );
}
