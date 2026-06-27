"""Egress allowlist tests (Module E) — no network."""
import sys, pathlib, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from jarvis import egress
from jarvis import tools


def test_default_allow_and_deny():
    # gateway + local home-LLM endpoints are allowed (ports ignored)
    assert egress.is_allowed("https://api.gcp.cloud.bmw/llmapi/v1")
    assert egress.is_allowed("http://localhost:11434/v1")      # ollama
    assert egress.is_allowed("127.0.0.1:1234")                  # lmstudio
    # arbitrary host is denied
    assert not egress.is_allowed("https://evil.example.com/exfil")
    try:
        egress.check("https://evil.example.com/exfil")
        assert False, "expected PermissionError"
    except PermissionError as e:
        assert "denied" in str(e)
    print("  ✓ default-deny: gateway + localhost allowed; arbitrary host denied")


def test_env_extends_allowlist():
    os.environ["JARVIS_EGRESS_ALLOW"] = "internal.tools.example"
    try:
        assert egress.is_allowed("https://internal.tools.example/x")
    finally:
        del os.environ["JARVIS_EGRESS_ALLOW"]
    print("  ✓ JARVIS_EGRESS_ALLOW extends the allowlist")


def test_http_get_tool_enforces_egress():
    # the http_get tool routes through egress.check; a denied host comes back as a
    # tool error (dispatch never raises), and no request is attempted.
    out = tools.dispatch("http_get", {"url": "https://evil.example.com/x"},
                         tools.ToolContext(repo_root=".", file_scope=[]))
    assert out.startswith("ERROR: PermissionError") and "denied" in out, out
    print("  ✓ http_get tool blocks out-of-allowlist egress (returns error, no fetch)")


if __name__ == "__main__":
    test_default_allow_and_deny()
    test_env_extends_allowlist()
    test_http_get_tool_enforces_egress()
    print("\nEGRESS (Module E) TESTS PASSED ✅")
