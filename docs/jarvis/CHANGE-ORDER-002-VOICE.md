# Change Order 002 — Voice loop: faster responses, correct STT, pluggable local engines

**Audience:** an implementing coding agent (programming-expert) or a human dev.
**Repo:** `opencode-galaxy`, web app under `web/`. **Branch:** `feat/voice-loop`.
**Companion:** `CHANGE-ORDER-001.md` (galaxy), `JARVIS-ORCHESTRATION-MODEL.md`.
**Grounded in:** `src/jarvis/voice/{VoiceController.tsx,TtsPipeline.ts,TtsLocal.ts,TtsBmw.ts}`, `src/jarvis/input/SttBridge.ts`, `scripts/whisper-sidecar.py`, `vite.config.ts` (`ttsLocalPlugin`, `whisperSidecarPlugin`).

Sequenced **latency wins first** (make JARVIS respond faster), then **STT correctness** (fix the wall), then **voice-first** (wake word / VAD / barge-in), then the **pluggable local daemon** (model choice + portability). Each task: goal, files, change, acceptance, commit.

---

## Why the loop feels slow / breaks today (diagnosis)

The round trip is: `mic → STT → sendMessage → agent thinking (SSE) → step-finish → TTS synth → audio out`. Two concrete defects:

1. **TTS waits for the whole turn, then the whole clip.** `VoiceController` fires `tts.play(fullText)` on `step-finish reason=stop` (or `session.idle`). `TtsPipeline.play()` synthesizes the entire response as one blob, then plays. First audio = full generation time + full synthesis time. **Fix: stream TTS sentence-by-sentence as text arrives (V1.1).**
2. **STT streams WebM in 250 ms chunks and clears the buffer mid-stream.** `recorder.start(250)` → server accumulates → at ≥32 KB it transcribes and `buffer.clear()`. WebM writes its header only in the first chunk, so every window after the first is headerless and ffmpeg can't decode it — the first ~2 s transcribe, then nothing. Compounded by a **silence timer keyed to transcript arrival** (`SILENCE_TIMEOUT_MS=1500`) that cuts you off mid-sentence. **Fix: one-shot blob per PTT (V2.1), then proper PCM+VAD (V3).**

---

## Hard invariants — do NOT violate

1. **Audio stays on-device.** STT and TTS must run locally (BMW privacy). Only orchestration (opencode) may be remote. Never send mic audio to a cloud STT.
2. **Never use Web Speech STT** (Google cloud; blocked on BMW network).
3. **One STT instance.** `useSttBridge` is called once in `VoiceController`, published via `SttProvider`. Do not add a second recognizer/recorder.
4. **One utterance at a time.** TTS is a singleton; new playback stops/replaces current. With the new queue, `stop()` clears the queue too.
5. **Barge-in must always win.** User speech (or PTT start, or wake word) immediately stops TTS and flushes the queue.
6. **One voice per response.** Don't switch TTS backend mid-response (see V1.1 note) — it makes JARVIS change voice mid-sentence.

---

## Fast track — recommended order

| # | Task | Effort | Payoff |
|---|---|---|---|
| 1 | **V1.1** Streaming (sentence-chunked) TTS | medium | The big "responds faster" win — JARVIS starts talking ~1 sentence into generation. |
| 2 | **V1.2** Warm mic + persistent STT socket | small | Reclaims ~300–500 ms per PTT press. |
| 3 | **V2.1** One-shot blob per PTT | small | Fixes the WebM-header bug + mid-sentence cutoff. Correctness. |
| 4 | **V2.2** Sidecar: decode one-shot, drop buffer-clear | small | Server side of V2.1. |
| 5 | **V1.3** Smaller STT model for commands | trivial | Several-fold faster transcribe. Config only. |
| 6 | **V3** PCM capture + Silero VAD | large | Proper streaming + acoustic endpointing; removes ffmpeg/WebM. |
| 7 | **V4** Voice-first: wake word + barge-in + AEC | large | PTT → hands-free JARVIS. |
| 8 | **V5** Pluggable local daemon (engines + config) | large | Model choice (faster-whisper/Piper) + portability; retires `say`/vite-middleware. |

---

## PHASE V1 — Latency wins

### Task V1.1 — Streaming, sentence-chunked TTS *(the headline fix)*
- **Goal:** start speaking while the agent is still generating, instead of after the full turn + full synthesis.
- **Files:** `src/jarvis/voice/TtsPipeline.ts` (add a queue), `src/jarvis/voice/VoiceController.tsx` (drive it from streaming SSE).
- **Change:**
  1. **TtsPipeline: add a sentence queue + runner.** Extend the handle with:
     ```ts
     export interface TtsPipelineHandle {
       play: (text: string) => Promise<void>;   // keep for one-shot
       enqueue: (sentence: string) => void;      // NEW — queue a sentence
       flush: () => void;                         // NEW — speak any buffered partial, then mark turn done
       stop: () => void;                          // clears queue + stops current (barge-in)
       lastBackend: 'local' | 'bmw' | null;
     }
     ```
     Internally keep `queue: string[]`, a `running` flag, and a `backendForTurn: 'local'|'bmw'|null`. The runner pulls a sentence, synthesizes, plays, awaits `onEnd`, pulls the next. `onStart` fires when the *first* sentence begins; `onEnd` (→ orb IDLE) fires only when the queue drains **and** the turn is flushed. `stop()` empties `queue` and stops the active utterance.
     - **One voice per response (invariant 6):** decide `backendForTurn` once on the first `enqueue` of a turn (e.g. by a setting, or default `local`), and route every sentence of that turn to the same backend. Do **not** re-route per sentence by length.
  2. **VoiceController: feed the queue from `message.part.updated`.** Today it only acts on `step-finish`. Change to accumulate streaming text per `msgId`, split off complete sentences, and `enqueue` them as they complete; `flush()` on `step-finish reason=stop`.
     - Track spoken offset per message so you only enqueue new text:
       ```ts
       const spokenLenRef = useRef<{ msgId: string; len: number }>({ msgId: '', len: 0 });
       // in message.part.updated (text):
       const full = sanitizeForSpeech(accumulatedTextForMsg);
       if (spokenLenRef.current.msgId !== msgId) spokenLenRef.current = { msgId, len: 0 };
       const pending = full.slice(spokenLenRef.current.len);
       const sentences = splitCompleteSentences(pending); // returns [completeSentences[], remainderStart]
       for (const s of sentences.complete) tts.enqueue(s);
       spokenLenRef.current.len += sentences.consumedChars;
       // on step-finish stop: tts.flush();  (speaks the trailing partial, ends the turn)
       ```
     - `splitCompleteSentences`: split on `/([.!?]+["')\]]?\s)|\n+/`, keep only sentences terminated within `pending`; leave the trailing partial unspoken until more text arrives or `flush()`. Guard against speaking 1–2 char fragments (buffer until ≥ ~12 chars or terminal punctuation).
  3. Keep `ttsEnabled` / `narrationEnabled` checks (CO-001 Phase 5.1) gating `enqueue`.
- **Acceptance:** ask JARVIS something that yields 3+ sentences → audio of sentence 1 begins **before** the full text finishes streaming; sentences play back-to-back with no overlap; the voice does not change mid-response; starting to speak (or PTT) cuts it off immediately and clears the rest.
- **Commit:** `feat(voice): streaming sentence-chunked TTS for low-latency responses`

### Task V1.2 — Warm mic + persistent STT socket
- **Goal:** remove the per-press `getUserMedia` + WebSocket handshake (~300–500 ms of dead air each PTT).
- **Files:** `src/jarvis/input/SttBridge.ts` (`useMlxWhisperBridge`).
- **Change:** acquire the `MediaStream` once when the mode becomes `mlxwhisper` (after first audio-unlock gesture), and keep a persistent WebSocket with auto-reconnect/backoff. On PTT `start`, create a fresh `MediaRecorder` on the **existing** stream (and signal "utterance start" to the server); on `stop`, stop the recorder but **keep** the stream and socket open. Tear down only on unmount / mode change.
  - Note: holding the mic open keeps the browser mic indicator lit — acceptable for a voice-first app; document it.
- **Acceptance:** second and subsequent PTT presses begin capturing within ~50 ms (no visible mic re-acquire); pulling the network/sidecar and restoring it reconnects without a page reload.
- **Commit:** `perf(voice): keep mic stream + STT socket warm across presses`

### Task V1.3 — Smaller STT model for command latency *(config only)*
- **Goal:** distil-large-v3 is overkill for short commands; transcribe time dominates STT.
- **Files:** `scripts/whisper-sidecar.py` default, or env.
- **Change:** default to `mlx-community/distil-small.en` (or `whisper-small`) for the interactive path; keep large as an opt-in via `--model`. Expose `STT_MODEL` env so V5's daemon can choose.
- **Acceptance:** short command ("open the galaxy") transcribes in a few hundred ms vs ~1–2 s, with no practical accuracy loss.
- **Commit:** `perf(voice): default to small STT model for interactive latency`

---

## PHASE V2 — STT correctness (fix the wall)

### Task V2.1 — One-shot blob per PTT (client)
- **Goal:** eliminate the WebM-header-after-clear bug and the transcript-timer cutoff by sending one complete, valid WebM per utterance.
- **Files:** `src/jarvis/input/SttBridge.ts` (`useMlxWhisperBridge`).
- **Change:**
  - `recorder.start()` **with no timeslice** (remove `start(250)`). Collect chunks into an array via `ondataavailable`.
  - **Remove the client silence timer entirely** (`SILENCE_TIMEOUT_MS`, `resetSilenceTimer`, `clearSilenceTimer`) — PTT release defines end-of-utterance.
  - On `stop`: `recorder.stop()`, then in `recorder.onstop` build `new Blob(chunks, { type: recorder.mimeType })` and send it as a single message to the sidecar (one binary frame, or a small `{start}`…blob…`{end}` framing). Await the single transcript, fire `onTranscript` once, then `onStop`.
- **Acceptance:** speak a 10–15 s sentence holding PTT → the **entire** utterance transcribes (not just the first ~2 s); no mid-sentence cutoff; releasing PTT yields the transcript within one transcribe.
- **Commit:** `fix(voice): one-shot utterance capture (fixes WebM-header truncation + cutoff)`

### Task V2.2 — Sidecar: decode one complete blob, drop buffer-clear (server)
- **Goal:** server side of V2.1 — stop mid-stream clearing; decode the full utterance once.
- **Files:** `scripts/whisper-sidecar.py` (`ws_transcribe`).
- **Change:** accumulate frames until the client signals end-of-utterance (recorder stop / a `{"event":"end"}` text frame / socket idle), then `_transcribe(full_blob)` **once** and send one `{text}`. Remove the `len(buffer) >= 32_000 → transcribe → buffer.clear()` loop. (The full blob is a valid standalone WebM, so the existing ffmpeg→wav→mlx path now works for the whole utterance.)
- **Acceptance:** server logs one transcribe per utterance; no `ffmpeg` decode errors after the first window; transcript covers the full utterance.
- **Commit:** `fix(whisper-sidecar): transcribe one complete utterance, drop mid-stream buffer clear`

---

## PHASE V3 — Proper capture: PCM + Silero VAD *(the real upgrade)*

### Task V3.1 — Raw PCM capture via AudioWorklet
- **Goal:** drop MediaRecorder/WebM/ffmpeg entirely; send Whisper its native 16 kHz mono float directly. Enables true streaming + server VAD; removes the container-header class of bugs permanently.
- **Files:** new `src/jarvis/input/pcmWorklet.ts` (+ worklet processor), `SttBridge.ts` (new `mlxwhisper-pcm` path or replace the WebM path).
- **Change:** `AudioContext` + `AudioWorkletNode` capturing `Float32` at the context rate; downsample to 16 kHz mono; post `Int16`/`Float32` frames (e.g. 20–32 ms) to the bridge, which streams them over the WS as raw binary. Server feeds PCM straight to the model (no ffmpeg).
- **Acceptance:** capture works with no `ffmpeg` involvement; CPU lower than the WebM path; transcripts match or beat V2 quality.
- **Commit:** `feat(voice): raw PCM capture via AudioWorklet (no container/ffmpeg)`

### Task V3.2 — Server-side Silero VAD endpointing
- **Goal:** end an utterance on **acoustic silence**, not a timer or transcript timing. Enables hands-free (no PTT) and natural turn-taking.
- **Files:** `scripts/whisper-sidecar.py` (or V5 daemon).
- **Change:** run Silero VAD over the incoming PCM stream; buffer speech frames; on a trailing-silence threshold (e.g. 600–800 ms), cut the segment and transcribe it; emit `{text, final:true}`. Optionally emit interim partials for long utterances.
- **Acceptance:** with VAD on, speaking and pausing naturally ends the turn at the pause; background silence never triggers a transcribe; no mid-sentence cut on short pauses (< threshold).
- **Commit:** `feat(stt): Silero VAD utterance endpointing on the PCM stream`

---

## PHASE V4 — Voice-first (hands-free)

### Task V4.1 — Wake word (on-device)
- **Goal:** "Hey JARVIS" replaces PTT as the default trigger; fully local.
- **Files:** new `src/jarvis/voice/wakeWord.ts`; wire into `VoiceController`.
- **Change:** run **openWakeWord** (ONNX via `onnxruntime-web` WASM) or **Porcupine** (your roadmap named it) on a low-rate mic tap, always listening locally. On detection, trigger the same capture path as PTT start (V2/V3). Keep PTT as a fallback/override.
- **Acceptance:** saying the wake phrase starts capture within ~300 ms without touching the UI; no audio leaves the device; false-accept rate acceptable in a quiet room.
- **Commit:** `feat(voice): on-device wake word ("Hey JARVIS")`

### Task V4.2 — Barge-in while speaking + echo cancellation *(the hidden wall)*
- **Goal:** let the user interrupt JARVIS mid-response hands-free, without the mic re-triggering off JARVIS's own TTS.
- **Files:** `VoiceController.tsx`, capture setup.
- **Change:** keep wake word / VAD listening **during** TTS playback; on detected user speech, immediately `tts.stop()` (flush queue) and start capture. Enable `getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } })`. If TTS plays through speakers (not headphones), expect to need real AEC — gate wake-word sensitivity during playback and/or duck the mic tap by the known TTS envelope. Design capture so the playback signal is referenceable for cancellation.
- **Acceptance:** while JARVIS is speaking through speakers, saying the wake word (or talking over it) stops TTS and captures the new utterance; JARVIS's own voice does **not** trigger the wake word or VAD.
- **Commit:** `feat(voice): hands-free barge-in with echo cancellation`

---

## PHASE V5 — Pluggable local engines + daemon (model choice + portability)

> Goal: one **local daemon** owning STT + TTS behind clean interfaces, engine chosen by config. Retires the Mac-only / dev-only hacks (`say` via vite middleware; mlx-only STT). Keeps audio on-device; only opencode is remote.

### Task V5.1 — STT engine interface + portable backend
- **Files:** evolve `scripts/whisper-sidecar.py` into `scripts/voice-daemon/` with an `stt/` package.
- **Change:** define `class SttEngine: def transcribe(self, pcm: bytes, sample_rate=16000) -> str`. Implement: `MlxWhisperEngine` (mac), **`FasterWhisperEngine`** (CTranslate2 — CPU/GPU, runs off-Mac), optionally `WhisperCppEngine`. Select via `STT_ENGINE` / `STT_MODEL` env. The WS endpoint calls the configured engine.
- **Acceptance:** `STT_ENGINE=faster-whisper` transcribes on a non-Mac machine; switching engines is env-only, no code change.
- **Commit:** `feat(voice-daemon): pluggable STT engines (mlx | faster-whisper | whisper.cpp)`

### Task V5.2 — Streaming TTS engine interface + local backend
- **Files:** `scripts/voice-daemon/tts/`, plus a new client `TtsDaemon.ts` to replace the vite `say` path.
- **Change:** define a **streaming** interface `class TtsEngine: def synthesize(self, text: str) -> Iterator[bytes]` (yields audio chunks). Implement **`PiperEngine`** (fast, offline, many voices — default), `SayEngine` (mac batch fallback), optionally `CoquiXttsEngine` (quality/cloning); keep BMW as a remote opt-in. Serve over `POST /api/tts` (chunked/streamed audio) or a WS. Select via `TTS_ENGINE` / `TTS_VOICE`. **Designing the interface as streaming now** is what lets V1.1 start audio mid-synthesis for long sentences and avoids a later retrofit.
- **Move TTS off vite middleware:** point `TtsLocal`/new `TtsDaemon` at the daemon's `/api/tts` instead of `/api/tts-local`. The vite `ttsLocalPlugin` (`say`→aiff→ffmpeg) becomes a dev-only fallback or is removed.
- **Acceptance:** `TTS_ENGINE=piper TTS_VOICE=<x>` speaks with the chosen local voice on any OS; switching voice/engine is env-only; long sentences begin playing before synthesis completes.
- **Commit:** `feat(voice-daemon): pluggable streaming TTS engines (piper | say | xtts | bmw)`

### Task V5.3 — One daemon, one health/config surface
- **Change:** single process exposes `/health` (reports active STT+TTS engine/model), `/ws/transcribe`, `/api/tts`. `vite.config.ts` auto-start plugin launches the daemon (generalize `whisperSidecarPlugin`). Document env in a `.env.example`.
- **Acceptance:** `curl /health` reports both engines; `npm run dev` starts the daemon; the browser is a thin client (capture, render, play).
- **Commit:** `feat(voice-daemon): unified local STT/TTS service with health + config`

---

## Suggested PR breakdown

| PR | Contains | Risk |
|---|---|---|
| PR1 | V1.1 + V1.2 + V1.3 | medium — latency wins, user-visible |
| PR2 | V2.1 + V2.2 | low — correctness, isolated |
| PR3 | V3 | medium — capture rewrite |
| PR4 | V4 | higher — hands-free + AEC |
| PR5 | V5 | higher — daemon + engines |

Land PR1+PR2 first: together they make the loop both *faster* and *correct*, which is most of the felt improvement. V3–V5 are the durable architecture.

---

## What each thing buys (recap)

- **Faster responses:** mostly **V1.1 streaming TTS** (start talking mid-generation), then **V1.2 warm connection** and **V1.3 smaller model** on the STT side. The agent's thinking time is the orchestration loop and isn't addressed here.
- **Model choice, kept local:** **V5** — STT/TTS behind engine interfaces selected by env (faster-whisper, Piper, etc.), all on-device. Portability (runs off-Mac) and swappability are the same change.
- **Reliability:** **V2** (one-shot) and **V3** (PCM+VAD) remove the WebM/ffmpeg failure class and replace timer cutoffs with acoustic endpointing.
