"""Voice daemon (Module B / CO-002).

FastAPI + WebSocket I/O for JARVIS voice. STT and TTS are pluggable engines; the
default Mock engines let the daemon run and be tested offline (no model download,
no audio hardware). The real engines (faster-whisper, Piper) import lazily and
raise a helpful error if their deps are absent — wire them via STT_ENGINE / TTS_ENGINE.

TTS narrates COMPLETED responses (the gateway tool-loop does not stream tokens):
a finished response is split into sentences and each is synthesized/played in
order, so playback of sentence N overlaps synthesis of N+1 (audio-side pipelining).

Run:  python -m uvicorn daemons.voice.app:app --port 8131   (from jarvis-starter/)
"""
from __future__ import annotations
import os, re
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel


# ── Pluggable engines ───────────────────────────────────────────────────────
class MockSTT:
    name = "mock-stt"
    def transcribe(self, audio: bytes) -> str:
        return f"[transcribed {len(audio)} bytes]"


class MockTTS:
    name = "mock-tts"
    def synthesize(self, text: str) -> bytes:
        return text.encode("utf-8")  # stand-in for audio bytes


class FasterWhisperSTT:  # pragma: no cover — requires the optional dep + a model
    name = "faster-whisper"
    def __init__(self):
        try:
            import faster_whisper  # noqa: F401
        except ImportError as e:
            raise RuntimeError("STT_ENGINE=faster-whisper needs `pip install faster-whisper`") from e

    def transcribe(self, audio: bytes) -> str:
        raise NotImplementedError("wire faster-whisper transcription here")


class PiperTTS:  # pragma: no cover — requires the optional dep + a voice
    name = "piper"
    def __init__(self):
        try:
            import piper  # noqa: F401
        except ImportError as e:
            raise RuntimeError("TTS_ENGINE=piper needs `pip install piper-tts`") from e

    def synthesize(self, text: str) -> bytes:
        raise NotImplementedError("wire Piper synthesis here")


_STT = {"mock": MockSTT, "faster-whisper": FasterWhisperSTT}
_TTS = {"mock": MockTTS, "piper": PiperTTS}


def _select(registry, env_var, default="mock"):
    key = os.environ.get(env_var, default)
    return registry.get(key, registry[default])()


stt = _select(_STT, "STT_ENGINE")
tts = _select(_TTS, "TTS_ENGINE")

# A sentence = run up to a terminator, or trailing text with none.
_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]+|[^.!?]+$")


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_RE.findall(text) if s.strip()]


# ── API ─────────────────────────────────────────────────────────────────────
app = FastAPI(title="JARVIS Voice")


@app.get("/health")
def health():
    return {"status": "ok", "stt": stt.name, "tts": tts.name}


class TTSRequest(BaseModel):
    text: str


@app.post("/tts")
def tts_endpoint(req: TTSRequest):
    """Split a finished response into the sentence queue + synthesize each chunk."""
    sentences = split_sentences(req.text)
    chunks = [{"index": i, "text": s, "bytes": len(tts.synthesize(s))}
              for i, s in enumerate(sentences)]
    return {"engine": tts.name, "sentences": sentences, "chunks": chunks}


@app.websocket("/stt")
async def stt_socket(ws: WebSocket):
    """Push-to-talk: receive an audio blob per turn, return its transcript."""
    await ws.accept()
    try:
        while True:
            audio = await ws.receive_bytes()
            await ws.send_json({"transcript": stt.transcribe(audio)})
    except WebSocketDisconnect:
        return
