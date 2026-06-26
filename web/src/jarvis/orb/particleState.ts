/**
 * particleState.ts — Orb state machine types and particle configuration.
 * This is the canonical state enum for the entire JARVIS system.
 */

export type OrbState = 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING';

export interface ParticleConfig {
  count: number;
  minOrbit: number;  // px
  maxOrbit: number;  // px
  speed: number;     // relative, 1.0 = normal
  color: string;     // CSS variable reference or hex
}

export const PARTICLE_CONFIGS: Record<OrbState, ParticleConfig> = {
  IDLE: {
    count: 48,
    minOrbit: 80,
    maxOrbit: 120,
    speed: 0.3,
    color: 'var(--jarvis-idle-particle)',
  },
  LISTENING: {
    count: 80,
    minOrbit: 55,
    maxOrbit: 90,
    speed: 1.2,
    color: 'var(--jarvis-listen-particle)',
  },
  THINKING: {
    count: 80,
    minOrbit: 40,
    maxOrbit: 75,
    speed: 0.6,
    color: 'var(--jarvis-idle-particle)',
  },
  SPEAKING: {
    count: 120,
    minOrbit: 70,
    maxOrbit: 130,
    speed: 1.5,
    color: 'var(--jarvis-speak-particle)',
  },
};

export const ORB_SCALE: Record<OrbState, number> = {
  IDLE: 1.0,
  LISTENING: 1.23,
  THINKING: 0.95,
  SPEAKING: 1.15,
};

// Ring rotation speeds (radians per frame at 60fps)
export const RING_SPEEDS = [0.008, -0.012, 0.006] as const;

// Ring tilt angles (degrees from vertical)
export const RING_TILTS = [0, 60, -40] as const;
