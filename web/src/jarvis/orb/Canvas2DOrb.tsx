/**
 * Canvas2DOrb.tsx
 *
 * The JARVIS orb: a three-ring gyroscope with a soft radial glow core
 * and a Lissajous particle field. Per spec: "three nested, independently
 * rotating elliptical rings around a soft radial glow core. Not a sphere."
 *
 * Used for IDLE / LISTENING / THINKING states.
 * SPEAKING hands off to VoxCorona (Three.js InstancedMesh).
 */

import { useEffect, useRef, useCallback } from 'react';
import type { OrbState } from './particleState';
import { PARTICLE_CONFIGS, ORB_SCALE } from './particleState';

// Ring rotation speeds (radians per frame at 60fps)
const RING_SPEEDS = [0.008, -0.013, 0.006] as const;

// Ring tilt angles — foreshorten ry to simulate 3-D tilt
// Each entry is [tiltDeg, baseRxFraction] where ry = rx * |cos(tilt)|
const RING_DEFS = [
  { tiltDeg: 0,   rxFrac: 0.30 },  // horizontal ring
  { tiltDeg: 60,  rxFrac: 0.28 },  // 60° tilted
  { tiltDeg: -38, rxFrac: 0.26 },  // -38° tilted
] as const;

interface Particle {
  angle:      number;
  radius:     number;
  baseRadius: number;
  speed:      number;
  size:       number;
  opacity:    number;
  lissA:      number;
  lissB:      number;
  phase:      number;
}

interface Props {
  state:  OrbState;
  size?:  number;  // logical CSS px, default 320
}

function resolveToken(token: string): string {
  const varName = token.startsWith('var(')
    ? token.slice(4, token.lastIndexOf(')'))
    : token;
  const val = getComputedStyle(document.documentElement)
    .getPropertyValue(varName.trim())
    .trim();
  return val || 'rgba(77,141,246,0.7)';
}

function withOpacity(color: string, opacity: number): string {
  if (color.startsWith('rgba')) {
    return color.replace(/,\s*[\d.]+\s*\)$/, `, ${opacity.toFixed(2)})`);
  }
  if (color.startsWith('rgb(')) {
    return color.replace('rgb(', 'rgba(').replace(')', `, ${opacity.toFixed(2)})`);
  }
  return color;
}

export function Canvas2DOrb({ state, size = 320 }: Props) {
  const canvasRef      = useRef<HTMLCanvasElement>(null);
  const particlesRef   = useRef<Particle[]>([]);
  const stateRef       = useRef<OrbState>(state);
  const ringAnglesRef  = useRef<number[]>([0, 0, 0]);
  const frameRef       = useRef<number>(0);
  const glowPhaseRef   = useRef<number>(0);

  useEffect(() => { stateRef.current = state; }, [state]);

  const initParticles = useCallback((count: number) => {
    particlesRef.current = Array.from({ length: count }, () => {
      const baseRadius = 80 + Math.random() * 40;
      return {
        angle:      Math.random() * Math.PI * 2,
        radius:     baseRadius,
        baseRadius,
        speed:      0.005 + Math.random() * 0.015,
        size:       1 + Math.random() * 1.8,
        opacity:    0.25 + Math.random() * 0.55,
        lissA:      1 + Math.floor(Math.random() * 3),
        lissB:      1 + Math.floor(Math.random() * 3),
        phase:      Math.random() * Math.PI * 2,
      };
    });
  }, []);

  // init on mount
  useEffect(() => { initParticles(PARTICLE_CONFIGS[state].count); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // main draw loop — re-runs only if logical `size` changes
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 3);
    canvas.width  = Math.round(size * dpr);
    canvas.height = Math.round(size * dpr);
    canvas.style.width  = `${size}px`;
    canvas.style.height = `${size}px`;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Absolute transform — idempotent on StrictMode double-invoke
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const cx = size / 2;
    const cy = size / 2;

    function draw() {
      const s      = stateRef.current;
      const config = PARTICLE_CONFIGS[s];
      const scale  = ORB_SCALE[s];

      ctx!.clearRect(0, 0, size, size);

      // ── 1. Soft breathing glow at centre ───────────────────────────────
      glowPhaseRef.current += 0.018;
      const glowPulse  = 0.85 + 0.15 * Math.sin(glowPhaseRef.current);
      const glowRadius = 36 * scale * glowPulse;

      const orbGlowRaw = resolveToken('var(--jarvis-orb-glow)');
      const grad = ctx!.createRadialGradient(cx, cy, 0, cx, cy, glowRadius);
      grad.addColorStop(0,    withOpacity(orbGlowRaw, 0.30));
      grad.addColorStop(0.5,  withOpacity(orbGlowRaw, 0.12));
      grad.addColorStop(1,    'transparent');
      ctx!.beginPath();
      ctx!.arc(cx, cy, glowRadius, 0, Math.PI * 2);
      ctx!.fillStyle = grad;
      ctx!.fill();

      // ── 2. Three gyroscope rings — thin stroked ellipses ───────────────
      const ringColorRaw = resolveToken('var(--jarvis-orb-ring)');

      for (let i = 0; i < 3; i++) {
        ringAnglesRef.current[i] += RING_SPEEDS[i];
        const angle    = ringAnglesRef.current[i];
        const def      = RING_DEFS[i];
        const rx       = size * def.rxFrac * scale;
        const tiltRad  = (def.tiltDeg * Math.PI) / 180;
        // Foreshorten ry so the ring looks tilted in 3-D space
        const ry       = rx * Math.abs(Math.cos(tiltRad));

        ctx!.save();
        ctx!.translate(cx, cy);
        ctx!.rotate(angle);

        ctx!.beginPath();
        ctx!.ellipse(0, 0, rx, ry, 0, 0, Math.PI * 2);
        ctx!.strokeStyle = withOpacity(ringColorRaw, 0.70);
        ctx!.lineWidth   = 1.2;
        ctx!.shadowBlur  = 5;
        ctx!.shadowColor = withOpacity(ringColorRaw, 0.45);
        ctx!.stroke();

        ctx!.restore();
      }

      // ── 3. Lissajous particle field ─────────────────────────────────────
      const particles     = particlesRef.current;
      const targetCount   = config.count;
      const particleColor = resolveToken(config.color);

      // Gradually converge count to target
      if (particles.length < targetCount) {
        const br = config.minOrbit + Math.random() * (config.maxOrbit - config.minOrbit);
        particles.push({
          angle: Math.random() * Math.PI * 2, radius: br, baseRadius: br,
          speed: 0.005 + Math.random() * 0.015, size: 1 + Math.random() * 1.8,
          opacity: 0.25 + Math.random() * 0.55,
          lissA: 1 + Math.floor(Math.random() * 3),
          lissB: 1 + Math.floor(Math.random() * 3),
          phase: Math.random() * Math.PI * 2,
        });
      } else if (particles.length > targetCount) {
        particles.splice(targetCount);
      }

      for (const p of particles) {
        p.angle += p.speed * config.speed;
        p.phase += 0.007;

        const targetR = Math.max(
          config.minOrbit * scale,
          p.baseRadius * scale * 0.5 * (1 + Math.sin(p.phase)),
        );
        p.radius += (targetR - p.radius) * 0.05;

        const x = cx + p.radius * Math.cos(p.angle * p.lissA + p.phase * 0.3);
        const y = cy + p.radius * 0.6  * Math.sin(p.angle * p.lissB);

        ctx!.beginPath();
        ctx!.arc(x, y, p.size, 0, Math.PI * 2);
        ctx!.fillStyle = withOpacity(particleColor, p.opacity);
        ctx!.fill();
      }

      frameRef.current = requestAnimationFrame(draw);
    }

    frameRef.current = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(frameRef.current);
  }, [size]);

  return (
    <div
      className="relative flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <canvas
        ref={canvasRef}
        className="absolute inset-0"
        style={{ width: size, height: size }}
      />
    </div>
  );
}
