"""Voice daemon tests (Module B) — FastAPI TestClient, mock engines, no audio/network."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from daemons.voice.app import app, split_sentences, MockSTT

client = TestClient(app)


def test_health_reports_engines():
    h = client.get("/health").json()
    assert h["status"] == "ok" and h["stt"] and h["tts"]
    print("  ✓ /health reports active STT/TTS engines")


def test_sentence_pipeline():
    assert split_sentences("Hello world. How are you? I am fine") == \
        ["Hello world.", "How are you?", "I am fine"]
    r = client.post("/tts", json={"text": "One. Two. Three"}).json()
    assert r["sentences"] == ["One.", "Two.", "Three"]
    assert [c["index"] for c in r["chunks"]] == [0, 1, 2] and all(c["bytes"] > 0 for c in r["chunks"])
    print("  ✓ TTS splits a finished response into an ordered sentence queue")


def test_mock_stt_and_ws():
    assert "transcribed" in MockSTT().transcribe(b"abc")
    with client.websocket_connect("/stt") as ws:
        ws.send_bytes(b"some-audio")
        msg = ws.receive_json()
        assert "transcript" in msg and "transcribed" in msg["transcript"]
    print("  ✓ push-to-talk STT websocket returns a transcript")


if __name__ == "__main__":
    test_health_reports_engines()
    test_sentence_pipeline()
    test_mock_stt_and_ws()
    print("\nVOICE (Module B) TESTS PASSED ✅")
