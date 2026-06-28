"""Provider-routing tests for the home/local LLM client — no network (injected factories)."""
import sys, pathlib, os, json, types
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from jarvis import llm_providers as P
from jarvis import llm


class FakeOpenAI:
    def __init__(self, base_url=None, api_key=None, default_headers=None):
        self.base_url, self.api_key, self.default_headers = base_url, api_key, default_headers
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._create))

    def _create(self, model=None, messages=None, tools=None):
        msg = types.SimpleNamespace(content=f"ok {self.base_url} {model}", tool_calls=None)
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])


class FakeAnthropic:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.messages = types.SimpleNamespace(create=self._create)

    def _create(self, model=None, max_tokens=None, system=None, messages=None, tools=None):
        return types.SimpleNamespace(content=[
            types.SimpleNamespace(type="text", text="hello "),
            types.SimpleNamespace(type="tool_use", id="t1", name="write_file", input={"path": "a.txt"}),
        ])


def test_openai_compat_endpoints():
    assert P.make_openai_client("ollama", _factory=FakeOpenAI).base_url == "http://localhost:11434/v1"
    assert P.make_openai_client("lmstudio", _factory=FakeOpenAI).base_url == "http://localhost:1234/v1"
    msg = P.complete_openai("ollama", [{"role": "user", "content": "hi"}], None, "llama3.1", _factory=FakeOpenAI)
    assert msg.content.startswith("ok http://localhost:11434/v1")
    print("  ✓ ollama / lmstudio route to their local OpenAI-compatible endpoints")


def test_bmw_bearer_header():
    os.environ["LLM_API_BEARER_TOKEN"] = "tok123"
    try:
        c = P.make_openai_client("bmw", _factory=FakeOpenAI)
        assert c.default_headers["Authorization"] == "Bearer tok123"
        assert "cloud.bmw" in c.base_url
    finally:
        del os.environ["LLM_API_BEARER_TOKEN"]
    print("  ✓ bmw provider attaches the gateway bearer token")


def test_anthropic_adapter_normalizes():
    msg = P.complete_anthropic(
        [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}],
        [{"type": "function", "function": {"name": "write_file", "description": "", "parameters": {}}}],
        "claude-sonnet-4-6", _factory=FakeAnthropic)
    assert msg.content == "hello "
    assert msg.tool_calls[0].function.name == "write_file"
    assert json.loads(msg.tool_calls[0].function.arguments)["path"] == "a.txt"
    print("  ✓ anthropic responses normalize to .content + .tool_calls")


def test_complete_routes_by_env():
    os.environ["JARVIS_LLM_PROVIDER"] = "anthropic"
    saved = P.complete_anthropic
    P.complete_anthropic = lambda m, t, mdl: types.SimpleNamespace(content="A", tool_calls=None)
    try:
        assert llm.complete([{"role": "user", "content": "hi"}]).content == "A"
    finally:
        P.complete_anthropic = saved
        del os.environ["JARVIS_LLM_PROVIDER"]
    print("  ✓ llm.complete() dispatches on JARVIS_LLM_PROVIDER (default ollama)")


if __name__ == "__main__":
    test_openai_compat_endpoints()
    test_bmw_bearer_header()
    test_anthropic_adapter_normalizes()
    test_complete_routes_by_env()
    print("\nLLM PROVIDERS TESTS PASSED ✅")
