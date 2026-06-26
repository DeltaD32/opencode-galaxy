/**
 * audioUnlock.ts — Unlock browser autoplay policy on first user gesture.
 *
 * Browsers (Chrome, Safari) block audio.play() calls that are not initiated
 * directly inside a user-gesture event handler. Async calls (e.g. from SSE
 * handlers or setTimeout) are always blocked — even if the user interacted
 * with the page moments before.
 *
 * The fix: on the FIRST click/keydown anywhere on the document, create a
 * silent AudioContext, resume it, and play a zero-duration silent buffer.
 * This "unlocks" the audio policy for the entire page lifetime.
 *
 * After unlock, HTMLAudioElement.play() from any async context works fine.
 *
 * Usage:
 *   import { ensureAudioUnlocked } from './audioUnlock';
 *   // Call once on app init — registers the one-shot listener
 *   ensureAudioUnlocked();
 *
 *   // Or call before play() to await unlock if not yet done:
 *   await waitForAudioUnlock();
 *   audio.play();
 */

let unlocked = false;
let unlockPromise: Promise<void> | null = null;
let resolveUnlock: (() => void) | null = null;

function createUnlockPromise() {
  unlockPromise = new Promise<void>((resolve) => {
    resolveUnlock = resolve;
  });
}

createUnlockPromise();

async function doUnlock() {
  if (unlocked) return;
  try {
    const ctx = new AudioContext();
    if (ctx.state === 'suspended') {
      await ctx.resume();
    }
    // Play a silent buffer — this is the actual gesture-tied unlock
    const buf = ctx.createBuffer(1, 1, 22050);
    const src = ctx.createBufferSource();
    src.buffer = buf;
    src.connect(ctx.destination);
    src.start(0);
    await ctx.close();
    unlocked = true;
    resolveUnlock?.();
    console.log('[TTS] Audio context unlocked — autoplay enabled');
  } catch (e) {
    console.warn('[TTS] Audio unlock failed:', e);
    // Still resolve so callers don't hang
    unlocked = true;
    resolveUnlock?.();
  }
}

/** Register one-shot listener on first user interaction to unlock audio. */
export function ensureAudioUnlocked(): void {
  if (unlocked) return;

  const events = ['click', 'keydown', 'touchstart', 'pointerdown'];
  const handler = () => {
    doUnlock();
    events.forEach((e) => document.removeEventListener(e, handler, true));
  };
  events.forEach((e) => document.addEventListener(e, handler, { once: false, capture: true }));
}

/** Returns true if audio is already unlocked. */
export function isAudioUnlocked(): boolean {
  return unlocked;
}

/**
 * Await until the audio context has been unlocked by a user gesture.
 * Resolves immediately if already unlocked.
 * Times out after 30s to avoid hanging forever.
 */
export function waitForAudioUnlock(timeoutMs = 30_000): Promise<void> {
  if (unlocked) return Promise.resolve();
  return Promise.race([
    unlockPromise!,
    new Promise<void>((_, reject) =>
      setTimeout(() => reject(new Error('Audio unlock timed out — user has not interacted with page')), timeoutMs)
    ),
  ]);
}
