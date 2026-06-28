# JARVIS at home — fully local, no cloud

Run the whole multi-agent system on your own machine with **Ollama** or **LM Studio**.
No BMW gateway, no Anthropic, no data leaving the box. `JARVIS_PROFILE=home` is an
*enforced* switch: cloud providers and the cloud embedding engine are refused in code,
and the egress allowlist drops every cloud host.

## 1. Install a local model server (pick one)

**Ollama** — https://ollama.com
```bash
ollama serve                 # starts the server on http://localhost:11434
ollama pull qwen2.5-coder    # a tool-capable model (see note below)
```

**LM Studio** — https://lmstudio.ai
- Download a tool-capable model (e.g. `qwen2.5-coder-7b-instruct`).
- Start its local server (defaults to http://localhost:1234).

> **Tool-calling matters.** The agent loop uses OpenAI-style function calling, so the
> model must support tools. Known-good local models: `qwen2.5-coder`, `qwen2.5`,
> `llama3.1`, `llama3.2`, `mistral-nemo`, `command-r`, `hermes3`. A model without tool
> support will plan but fail to act.

## 2. Configure + install deps

```bash
cd jarvis-starter
cp config/home.env.example .env      # edit: pick ollama or lmstudio + your model
set -a; . ./.env; set +a             # (PowerShell: load the vars your way)
python -m venv .venv && . .venv/Scripts/activate   # or .venv/bin/activate
pip install openai sqlite-vec fastembed            # all local; fastembed = offline embeddings
```

## 3. Verify it's truly local

```bash
python -m jarvis.doctor
```
Every line must be `[OK]`. It fails if the provider is cloud, the local endpoint is
unreachable, the model isn't tool-capable, embeddings aren't local, the egress allowlist
has a cloud host, or any cloud credential is set.

## 4. Run

```bash
python run.py "create hello.txt with a greeting"        # plan only (gate holds)
python run.py --go "create hello.txt with a greeting"   # plan + execute, fully local
```

## What "home" changes vs the default build

| Concern | Default | Home (`JARVIS_PROFILE=home`) |
|---|---|---|
| LLM provider | ollama/lmstudio/bmw/anthropic | ollama/lmstudio only — cloud refused in code |
| Embeddings | local (fallback hash) | local/hash only — `bmw` engine refused |
| Egress allowlist | gateway + localhost | localhost only |
| Cloud creds | optional | none; doctor flags any that are set |

Windows note: run Python with `PYTHONUTF8=1` so the `✓`/checklist glyphs print.
