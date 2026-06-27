# JARVIS starter — verified foundation + memory

Clean-room, opencode-free agentic core. Agents are direct LLM-API loops; a control
plane runs a task DAG concurrently with governance, file-leases, and retry; a
self-learning memory recalls before acting and records after.

## Run the tests (no network — mock LLM + offline embeddings)
    python tests/test_smoke.py              # loop, sandbox, concurrency, gate, leases
    python tests/test_decompose.py          # request -> DAG -> concurrent run
    python tests/test_memory.py             # remember/recall, dedup, singleton, KNN, decay
    python tests/test_memory_integration.py # the learning loop (record -> recall)

## Run it for real (needs BMW LLM API creds)
    cp .env.example .env     # fill LLM_API_BEARER_TOKEN / LLM_API_KEY  (manual Step 1)
    set -a; . ./.env; set +a
    export JARVIS_EMBED_ENGINE=local         # real semantic memory (installs fastembed)
    python run.py "build a hello-world FastAPI app"        # plan only (gate holds)
    python run.py --go "build a hello-world FastAPI app"   # plan + execute + learn

## Layout
    jarvis/llm.py          LLM client (OpenAI-compatible BMW gateway; default claude-sonnet-4-6)
    jarvis/db.py           SQLite state store
    jarvis/tools.py        sandboxed, file-scope-restricted tools
    jarvis/runtime.py      the agent loop (OpenAI function-calling)
    jarvis/scheduler.py    control plane: DAG + leases + governance + retry
    jarvis/decomposer.py   request -> validated DAG
    jarvis/agents.py       agent registry (agents are data)
    jarvis/orchestrator.py handle_request() — entrypoint, with the memory learning loop
    jarvis/memory/         remember()/recall() + pluggable embeddings (hash|local|bmw)
    schema/state.sql       blackboard + task DAG + audit log
    schema/memory.sql      entities/observations/relations (+ runtime sqlite-vec table)
    config/autonomy.toml   Module F autonomy policy
    run.py                 CLI

Deps: pip install openai fastembed sqlite-vec  (managed Python: add --break-system-packages)
Full step-by-step: JARVIS-BUILD-MANUAL.md.  Architecture: JARVIS-BUILD-GUIDE.md.
