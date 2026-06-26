#!/usr/bin/env python3
"""
whisper-sidecar.py — Local STT bridge for JARVIS.

Serves a WebSocket endpoint at ws://localhost:5001/ws/transcribe.
Receives raw WebM/Opus audio chunks from the browser, accumulates them,
and transcribes using mlx-whisper (Apple Silicon MLX — runs fully on-device).

Audio never leaves the machine.

Usage:
    # First-time setup (installs deps into a local venv):
    python3 scripts/whisper-sidecar.py --setup

    # Normal start:
    python3 scripts/whisper-sidecar.py

    # Use a different model (default: distil-whisper-large-v3):
    python3 scripts/whisper-sidecar.py --model mlx-community/whisper-small-mlx

Requirements:
    - macOS on Apple Silicon (M1/M2/M3)
    - Python 3.10+
    - ffmpeg  (brew install ffmpeg)

The sidecar self-installs its Python deps into .venv-whisper/ on first run
(or when --setup is passed).  No global pip install needed.

WebSocket protocol:
    Client → server: raw audio/webm;codecs=opus binary frames (250 ms chunks)
    Server → client: JSON  { "text": "<transcript chunk>" }
                     JSON  { "error": "<message>" }

Health endpoint:
    GET http://localhost:5001/health  →  { "status": "ok", "model": "<name>" }
"""

import argparse
import asyncio
import io
import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────

PORT = 5001
DEFAULT_MODEL = "mlx-community/distil-whisper-large-v3"
VENV_DIR = Path(__file__).parent.parent / ".venv-whisper"

logging.basicConfig(level=logging.INFO, format="[whisper-sidecar] %(message)s")
log = logging.getLogger(__name__)

# ─── Dependency bootstrap ─────────────────────────────────────────────────────

REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn[standard]",
    "websockets",
    "mlx-whisper",
    "numpy",
]


def setup_venv() -> Path:
    """Create .venv-whisper and install deps if needed."""
    python = VENV_DIR / "bin" / "python"

    if not VENV_DIR.exists():
        log.info(f"Creating venv at {VENV_DIR}…")
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])

    log.info("Installing / verifying Python deps…")
    subprocess.check_call(
        [str(python), "-m", "pip", "install", "--quiet", "--upgrade", *REQUIRED_PACKAGES]
    )
    log.info("Deps ready.")
    return python


def ensure_ffmpeg():
    if subprocess.run(["which", "ffmpeg"], capture_output=True).returncode != 0:
        log.error("ffmpeg not found — install with: brew install ffmpeg")
        sys.exit(1)


# ─── Re-exec into venv if needed ──────────────────────────────────────────────

def reexec_in_venv():
    venv_python = VENV_DIR / "bin" / "python"
    if sys.executable != str(venv_python):
        if not venv_python.exists():
            setup_venv()
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)


# ─── Server ───────────────────────────────────────────────────────────────────

def run_server(model_name: str, port: int):
    ensure_ffmpeg()

    # These imports only work inside the venv
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect  # type: ignore
    from fastapi.middleware.cors import CORSMiddleware  # type: ignore
    import uvicorn  # type: ignore
    import mlx_whisper  # type: ignore

    app = FastAPI()

    # Allow the Vite dev server (any localhost origin) to call /health and the WebSocket.
    # In Tauri production the origin will be tauri://localhost — also matched by wildcard.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    log.info(f"Loading model: {model_name}")
    # Pre-load model (first load may download weights ~1 GB)
    # We warm it up lazily on first transcription to keep startup snappy.

    @app.get("/health")
    async def health():
        return {"status": "ok", "model": model_name}

    @app.websocket("/ws/transcribe")
    async def ws_transcribe(ws: WebSocket):
        await ws.accept()
        log.info("Client connected")
        buffer = bytearray()

        try:
            while True:
                data = await ws.receive_bytes()
                buffer.extend(data)

                # Transcribe whenever we have >= 2 seconds of audio (approx 32 KB at 128kbps)
                # to balance latency vs accuracy. Flush remaining on disconnect.
                if len(buffer) >= 32_000:
                    text = await asyncio.get_event_loop().run_in_executor(
                        None, _transcribe, bytes(buffer), model_name
                    )
                    buffer.clear()
                    if text:
                        await ws.send_text(json.dumps({"text": text}))

        except WebSocketDisconnect:
            log.info("Client disconnected")
            # Final flush
            if buffer:
                text = await asyncio.get_event_loop().run_in_executor(
                    None, _transcribe, bytes(buffer), model_name
                )
                if text:
                    try:
                        await ws.send_text(json.dumps({"text": text}))
                    except Exception:
                        pass
        except Exception as e:
            log.error(f"WebSocket error: {e}")
            try:
                await ws.send_text(json.dumps({"error": str(e)}))
            except Exception:
                pass

    log.info(f"Starting on ws://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")


def _transcribe(audio_bytes: bytes, model_name: str) -> str:
    """Convert WebM/Opus bytes → WAV temp file → mlx_whisper transcript."""
    import mlx_whisper  # type: ignore

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as src:
        src.write(audio_bytes)
        src_path = src.name

    wav_path = src_path.replace(".webm", ".wav")
    try:
        # Convert WebM/Opus → WAV 16kHz mono (whisper's native format)
        subprocess.run(
            ["ffmpeg", "-y", "-i", src_path, "-ar", "16000", "-ac", "1", wav_path],
            capture_output=True,
            check=True,
        )
        result = mlx_whisper.transcribe(wav_path, path_or_hf_repo=model_name)
        return result.get("text", "").strip()
    except subprocess.CalledProcessError as e:
        log.error(f"ffmpeg conversion failed: {e.stderr.decode()}")
        return ""
    except Exception as e:
        log.error(f"Transcription error: {e}")
        return ""
    finally:
        for p in (src_path, wav_path):
            try:
                os.unlink(p)
            except FileNotFoundError:
                pass


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JARVIS mlx-whisper STT sidecar")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="HuggingFace model repo")
    parser.add_argument("--setup", action="store_true", help="Install deps then exit")
    parser.add_argument("--port", type=int, default=PORT, help="Listen port (default 5001)")
    args = parser.parse_args()

    if args.setup:
        setup_venv()
        log.info("Setup complete. Run: python scripts/whisper-sidecar.py")
        sys.exit(0)

    # Re-exec inside venv so mlx_whisper etc. are importable
    reexec_in_venv()
    run_server(args.model, args.port)
