"""Home-profile tests — enforced local-only; no network (injected probe/providers)."""
import sys, pathlib, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from jarvis import profile, egress, doctor, llm
from jarvis import llm_providers as providers


def _set(**env):
    for k, v in env.items():
        os.environ[k] = v


def _clear(*keys):
    for k in keys:
        os.environ.pop(k, None)


def test_home_egress_drops_gateway():
    _set(JARVIS_PROFILE="home")
    try:
        al = egress.allowlist()
        assert egress.GATEWAY_HOST not in al and "localhost" in al, al
        try:
            egress.check(f"https://{egress.GATEWAY_HOST}/llmapi/v1")
            assert False, "gateway egress should be denied in home mode"
        except PermissionError:
            pass
    finally:
        _clear("JARVIS_PROFILE")
    # non-home keeps the gateway allowed (no regression)
    assert egress.GATEWAY_HOST in egress.allowlist()
    print("  ✓ home egress is localhost-only; non-home still allows the gateway")


def test_enforce_provider_and_embed():
    _set(JARVIS_PROFILE="home")
    try:
        assert profile.enforce_provider("ollama") == "ollama"
        assert profile.enforce_embed("local") == "local"
        for bad in ("bmw", "anthropic"):
            try:
                profile.enforce_provider(bad)
                assert False
            except RuntimeError:
                pass
    finally:
        _clear("JARVIS_PROFILE")
    # no-op when not in home mode
    assert profile.enforce_provider("bmw") == "bmw"
    print("  ✓ home mode refuses cloud provider/embeddings; no-op otherwise")


def test_complete_refuses_cloud_before_network():
    _set(JARVIS_PROFILE="home", JARVIS_LLM_PROVIDER="bmw")
    reached = {"openai": 0, "anthropic": 0}
    saved_o, saved_a = providers.complete_openai, providers.complete_anthropic
    providers.complete_openai = lambda *a, **k: reached.__setitem__("openai", 1)
    providers.complete_anthropic = lambda *a, **k: reached.__setitem__("anthropic", 1)
    try:
        try:
            llm.complete([{"role": "user", "content": "hi"}])
            assert False, "home mode must refuse provider=bmw"
        except RuntimeError:
            pass
        assert reached == {"openai": 0, "anthropic": 0}, "no network path should be reached"
    finally:
        providers.complete_openai, providers.complete_anthropic = saved_o, saved_a
        _clear("JARVIS_PROFILE", "JARVIS_LLM_PROVIDER")
    print("  ✓ llm.complete() raises on a cloud provider in home mode, before any call")


def test_doctor_pass_and_fail():
    ok_probe = lambda url, timeout=2.0: {"data": [{"id": "qwen2.5-coder:7b"}]}
    fail_probe = lambda url, timeout=2.0: None
    _set(JARVIS_PROFILE="home", JARVIS_LLM_PROVIDER="ollama",
         JARVIS_MODEL="qwen2.5-coder", JARVIS_EMBED_ENGINE="local")
    try:
        assert doctor.check(probe=ok_probe)["ok"], "healthy local setup should pass"
        assert not doctor.check(probe=fail_probe)["ok"], "unreachable endpoint should fail"
        _set(JARVIS_LLM_PROVIDER="bmw")
        assert not doctor.check(probe=ok_probe)["ok"], "cloud provider should fail the doctor"
    finally:
        _clear("JARVIS_PROFILE", "JARVIS_LLM_PROVIDER", "JARVIS_MODEL", "JARVIS_EMBED_ENGINE")
    print("  ✓ doctor passes a healthy local setup; fails unreachable/cloud")


if __name__ == "__main__":
    test_home_egress_drops_gateway()
    test_enforce_provider_and_embed()
    test_complete_refuses_cloud_before_network()
    test_doctor_pass_and_fail()
    print("\nHOME PROFILE TESTS PASSED ✅")
