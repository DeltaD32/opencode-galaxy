"""
BMW Advisor-Enhanced ReAct Agent
=================================
A client-side implementation of the Advisor Tool pattern for BMW LLM API.

A fast, cheap EXECUTOR model does the work turn-by-turn. At configurable
checkpoints it calls a higher-intelligence ADVISOR model, which sees the full
conversation transcript and returns concise strategic guidance before the
executor continues.

This mirrors the Anthropic native advisor-tool-2026-03-01 pattern but works
entirely client-side — no Opus required, any two BMW LLM API models can pair.

Usage:
    from bmw_advisor import run_agent_advised, AdvisorConfig, PROFILES, pick_profile

    # Quick start — use a named profile
    result = run_agent_advised(
        prompt="Analyse Jira epic AI4D-100 and summarise blockers",
        tools=TOOLS,
        dispatch=DISPATCH,
        profile="balanced",          # see PROFILES below
    )

    # Full control — override any parameter
    result = run_agent_advised(
        prompt="...",
        tools=TOOLS,
        dispatch=DISPATCH,
        executor_model="anthropic/claude-sonnet-4-6",
        advisor_model="openai/gpt-5",
        advisor_every_n_steps=2,
        advisor_max_tokens=2048,
        advisor_on_completion=True,
        max_steps=15,
    )

    # Interactive model picker (CLI)
    cfg = pick_profile()
    result = run_agent_advised(prompt="...", tools=TOOLS, dispatch=DISPATCH, **cfg)
"""

from __future__ import annotations

import json
import os
import pathlib
import time
import textwrap
from dataclasses import dataclass, field, asdict
from typing import Callable

import httpx
from openai import OpenAI


# ─────────────────────────────────────────────────────────────────────────────
# Model catalogue  (refreshed 2026-06-24 from BMW LLM API /v1/models)
# ─────────────────────────────────────────────────────────────────────────────

#: All models available on the BMW LLM API with their capability tier.
#: Tier 1 = highest intelligence / cost, Tier 3 = fastest / cheapest.
BMW_MODELS: dict[str, dict] = {
    # ── Claude ────────────────────────────────────────────────────────────────
    "anthropic/claude-sonnet-4-6": {
        "tier": 1,
        "provider": "anthropic",
        "family": "claude",
        "strengths": ["reasoning", "coding", "long-context", "tool-calling"],
        "cost": "medium",
        "speed": "medium",
        "tools": True,
        "note": "Best Claude available on BMW LLM API. Excellent for complex multi-step reasoning.",
    },
    "anthropic/claude-sonnet-4-5": {
        "tier": 2,
        "provider": "anthropic",
        "family": "claude",
        "strengths": ["reasoning", "coding", "tool-calling"],
        "cost": "medium",
        "speed": "medium",
        "tools": True,
        "note": "Slightly older Sonnet. Solid all-rounder.",
    },
    "anthropic/claude-sonnet-4": {
        "tier": 2,
        "provider": "anthropic",
        "family": "claude",
        "strengths": ["tool-calling", "coding"],
        "cost": "medium",
        "speed": "medium",
        "tools": True,
        "note": "Earlier Sonnet generation. Use sonnet-4-6 instead where possible.",
    },
    "anthropic/claude-haiku-4-5": {
        "tier": 3,
        "provider": "anthropic",
        "family": "claude",
        "strengths": ["speed", "simple-tasks", "tool-calling"],
        "cost": "low",
        "speed": "fast",
        "tools": True,
        "note": "Fastest Claude. Good executor for mechanical steps; benefits most from an advisor.",
    },
    # ── GPT-5 family ──────────────────────────────────────────────────────────
    "openai/gpt-5": {
        "tier": 1,
        "provider": "openai",
        "family": "gpt-5",
        "strengths": ["reasoning", "coding", "planning", "tool-calling"],
        "cost": "high",
        "speed": "medium",
        "tools": True,
        "note": "Highest-intelligence GPT on BMW LLM API. Best advisor for complex planning.",
    },
    "openai/gpt-5.4": {
        "tier": 1,
        "provider": "openai",
        "family": "gpt-5",
        "strengths": ["reasoning", "coding", "planning", "tool-calling"],
        "cost": "high",
        "speed": "medium",
        "tools": True,
        "note": "Latest GPT-5 variant. Strong planner and advisor.",
    },
    "openai/gpt-5.1": {
        "tier": 2,
        "provider": "openai",
        "family": "gpt-5",
        "strengths": ["reasoning", "tool-calling", "coding"],
        "cost": "medium-high",
        "speed": "medium",
        "tools": True,
        "note": "GPT-5.1 — good balance of intelligence and cost.",
    },
    "openai/gpt-5-mini": {
        "tier": 3,
        "provider": "openai",
        "family": "gpt-5",
        "strengths": ["speed", "tool-calling", "simple-tasks"],
        "cost": "low",
        "speed": "fast",
        "tools": True,
        "note": "Fast and cheap. Good lightweight executor.",
    },
    "openai/gpt-5-nano": {
        "tier": 3,
        "provider": "openai",
        "family": "gpt-5",
        "strengths": ["speed", "simple-tasks"],
        "cost": "very-low",
        "speed": "very-fast",
        "tools": True,
        "note": "Fastest/cheapest GPT-5. For trivial mechanical steps only.",
    },
    # ── GPT-4o family ─────────────────────────────────────────────────────────
    "openai/gpt-4o": {
        "tier": 2,
        "provider": "openai",
        "family": "gpt-4o",
        "strengths": ["tool-calling", "coding", "reasoning"],
        "cost": "medium",
        "speed": "medium",
        "tools": True,
        "note": "Proven workhorse. Reliable tool-caller; good executor for most workflows.",
    },
    "openai/gpt-4o-mini": {
        "tier": 3,
        "provider": "openai",
        "family": "gpt-4o",
        "strengths": ["speed", "tool-calling", "simple-tasks"],
        "cost": "low",
        "speed": "fast",
        "tools": True,
        "note": "Cheap and fast. Adequate executor for simple single-tool workflows.",
    },
    # ── GPT-4.1 family ────────────────────────────────────────────────────────
    "openai/gpt-4.1": {
        "tier": 2,
        "provider": "openai",
        "family": "gpt-4.1",
        "strengths": ["coding", "tool-calling", "instruction-following"],
        "cost": "medium",
        "speed": "medium",
        "tools": True,
        "note": "Strong coder. Good executor for code-heavy agentic tasks.",
    },
    "openai/gpt-4.1-mini": {
        "tier": 3,
        "provider": "openai",
        "family": "gpt-4.1",
        "strengths": ["speed", "tool-calling"],
        "cost": "low",
        "speed": "fast",
        "tools": True,
        "note": "Lightweight GPT-4.1. Reasonable executor for structured data tasks.",
    },
    # ── Reasoning models ──────────────────────────────────────────────────────
    "openai/o3": {
        "tier": 1,
        "provider": "openai",
        "family": "o-series",
        "strengths": ["deep-reasoning", "planning", "math", "complex-decisions"],
        "cost": "very-high",
        "speed": "slow",
        "tools": True,
        "note": "Best reasoning model on BMW LLM API. Ideal advisor for high-stakes or "
                "mathematically complex decisions. Slow — use sparingly.",
    },
    "openai/o4-mini": {
        "tier": 2,
        "provider": "openai",
        "family": "o-series",
        "strengths": ["reasoning", "planning", "math"],
        "cost": "medium",
        "speed": "medium",
        "tools": True,
        "note": "Lighter reasoning model. Good advisor when o3 cost is prohibitive.",
    },
    "openai/o3-mini": {
        "tier": 2,
        "provider": "openai",
        "family": "o-series",
        "strengths": ["reasoning", "planning"],
        "cost": "medium",
        "speed": "medium",
        "tools": True,
        "note": "Budget reasoning advisor. Useful when o4-mini feels heavy.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Named profiles  — ready-to-use executor/advisor pairings
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AdvisorConfig:
    """Full configuration for an advisor-enhanced agent run."""
    executor_model: str          = "openai/gpt-4o"
    advisor_model: str           = "anthropic/claude-sonnet-4-6"
    advisor_every_n_steps: int   = 1      # call advisor on step 1, then every N
    advisor_on_completion: bool  = True   # extra advisor call when executor is about to return
    advisor_max_tokens: int      = 2048   # matches Anthropic's recommended cap
    advisor_word_limit: int      = 80     # soft word-limit injected into advisor prompt
    max_steps: int               = 10
    system: str                  = (
        "You are a helpful assistant with access to tools. "
        "Think step by step. Use your advisor for strategic guidance before "
        "committing to an approach and when you hit difficulty."
    )

    def as_kwargs(self) -> dict:
        return asdict(self)


#: Ready-to-use profiles. Pass profile="<name>" to run_agent_advised().
PROFILES: dict[str, AdvisorConfig] = {

    # ── Speed-first ───────────────────────────────────────────────────────────
    "speed": AdvisorConfig(
        executor_model         = "anthropic/claude-haiku-4-5",
        advisor_model          = "openai/gpt-4o",
        advisor_every_n_steps  = 3,
        advisor_on_completion  = False,
        advisor_max_tokens     = 1024,
        advisor_word_limit     = 50,
        max_steps              = 8,
    ),

    # ── Balanced (default) ────────────────────────────────────────────────────
    "balanced": AdvisorConfig(
        executor_model         = "openai/gpt-4o",
        advisor_model          = "anthropic/claude-sonnet-4-6",
        advisor_every_n_steps  = 1,
        advisor_on_completion  = True,
        advisor_max_tokens     = 2048,
        advisor_word_limit     = 80,
        max_steps              = 10,
    ),

    # ── Quality — best intelligence, cross-provider diversity ─────────────────
    "quality": AdvisorConfig(
        executor_model         = "anthropic/claude-sonnet-4-6",
        advisor_model          = "openai/gpt-5",
        advisor_every_n_steps  = 1,
        advisor_on_completion  = True,
        advisor_max_tokens     = 2048,
        advisor_word_limit     = 80,
        max_steps              = 15,
    ),

    # ── Deep reasoning — best for SAP/financial/risk decisions ────────────────
    "deep": AdvisorConfig(
        executor_model         = "anthropic/claude-sonnet-4-6",
        advisor_model          = "openai/o3",
        advisor_every_n_steps  = 2,        # o3 is slow; use sparingly
        advisor_on_completion  = True,
        advisor_max_tokens     = 2048,
        advisor_word_limit     = 100,
        max_steps              = 12,
    ),

    # ── Same-provider Claude — pure Anthropic stack ───────────────────────────
    "claude": AdvisorConfig(
        executor_model         = "anthropic/claude-haiku-4-5",
        advisor_model          = "anthropic/claude-sonnet-4-6",
        advisor_every_n_steps  = 1,
        advisor_on_completion  = True,
        advisor_max_tokens     = 2048,
        advisor_word_limit     = 80,
        max_steps              = 10,
    ),

    # ── Same-provider GPT — pure OpenAI stack ────────────────────────────────
    "gpt": AdvisorConfig(
        executor_model         = "openai/gpt-4o",
        advisor_model          = "openai/gpt-5",
        advisor_every_n_steps  = 1,
        advisor_on_completion  = True,
        advisor_max_tokens     = 2048,
        advisor_word_limit     = 80,
        max_steps              = 10,
    ),

    # ── Economy — minimal cost, still advised ─────────────────────────────────
    "economy": AdvisorConfig(
        executor_model         = "openai/gpt-4o-mini",
        advisor_model          = "openai/gpt-4o",
        advisor_every_n_steps  = 3,
        advisor_on_completion  = False,
        advisor_max_tokens     = 1024,
        advisor_word_limit     = 50,
        max_steps              = 8,
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# System prompt fragments
# ─────────────────────────────────────────────────────────────────────────────

_ADVISOR_SYSTEM = textwrap.dedent("""\
    You are a strategic advisor reviewing an executor agent's progress.
    You will receive the executor's full conversation transcript.
    Your job is NOT to do the work yourself — it is to give the executor
    concise, actionable guidance on:
      - The best approach to take next
      - Risks, edge cases, or failure modes to watch for
      - Whether the current direction is correct
      - Any course corrections needed before the executor commits

    Be direct and specific. Avoid generic advice.
    Focus on what the executor might miss or get wrong.
""")

_ADVISOR_USER_TEMPLATE = textwrap.dedent("""\
    The executor has reached a decision point. Review the transcript above and
    provide strategic guidance in under {word_limit} words.

    Answer ONLY: what should the executor do next, and why?
    Flag any risk or assumption that could cause failure.
    Do not repeat what the executor has already done correctly.
""")

_COMPLETION_ADVISOR_USER = textwrap.dedent("""\
    The executor believes it has completed the task. Review the full transcript.
    In under {word_limit} words:
      1. Is the answer correct and complete?
      2. Is anything missing, wrong, or insufficiently handled?
      3. Should the executor revise before returning, or is it safe to finish?
""")


# ─────────────────────────────────────────────────────────────────────────────
# Usage / cost tracking
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class UsageRecord:
    model: str
    role: str          # "executor" | "advisor"
    input_tokens: int  = 0
    output_tokens: int = 0
    latency_s: float   = 0.0

@dataclass
class RunStats:
    executor_model: str
    advisor_model: str
    executor_calls: int              = 0
    advisor_calls: int               = 0
    total_executor_input_tokens: int = 0
    total_executor_output_tokens: int= 0
    total_advisor_input_tokens: int  = 0
    total_advisor_output_tokens: int = 0
    total_wall_s: float              = 0.0
    records: list[UsageRecord]       = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"── Run stats ──────────────────────────────",
            f"  Executor : {self.executor_model}",
            f"  Advisor  : {self.advisor_model}",
            f"  Executor calls : {self.executor_calls}  "
            f"({self.total_executor_input_tokens} in / {self.total_executor_output_tokens} out tokens)",
            f"  Advisor calls  : {self.advisor_calls}  "
            f"({self.total_advisor_input_tokens} in / {self.total_advisor_output_tokens} out tokens)",
            f"  Wall time      : {self.total_wall_s:.1f}s",
            f"───────────────────────────────────────────",
        ]
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Auth client
# ─────────────────────────────────────────────────────────────────────────────

def _bmw_client() -> OpenAI:
    """Single shared OpenAI client configured for BMW LLM API."""
    ca = (
        os.environ.get("BMW_CA_BUNDLE")
        or str(pathlib.Path.home() / ".opencode/plugins/clipjoint/BMW_Trusted_Certificates_Latest.pem")
    )
    return OpenAI(
        base_url=os.environ.get("LLM_API_BASE_URL", "https://api.gcp.cloud.bmw/llmapi/v1"),
        api_key=os.environ.get("LLM_API_KEY", "unused"),
        http_client=httpx.Client(
            headers={"x-apikey": os.environ["LLM_API_KEY"]},
            verify=ca if pathlib.Path(ca).exists() else True,
        ),
        default_headers={"Authorization": f"Bearer {os.environ['LLM_API_BEARER_TOKEN']}"},
    )


# ─────────────────────────────────────────────────────────────────────────────
# Core advisor call
# ─────────────────────────────────────────────────────────────────────────────

def _call_advisor(
    client: OpenAI,
    advisor_model: str,
    transcript: list[dict],
    user_instruction: str,
    max_tokens: int,
    stats: RunStats,
) -> str:
    """
    Call the advisor model with the full executor transcript.
    Returns the advisor's guidance text.
    Gracefully degrades — on any error returns empty string so the
    executor continues uninterrupted.

    BMW LLM API note: Claude models reject multiple system prompts.
    We use a single system message (advisor's own) and inline the
    executor's system prompt + transcript as quoted user-turn context.
    """
    # Normalise transcript entries to plain dicts, stripping tool objects
    def _norm(m) -> dict | None:
        if isinstance(m, dict):
            role    = m.get("role", "")
            content = m.get("content") or ""
        else:
            role    = getattr(m, "role", "")
            content = getattr(m, "content", "") or ""

        # Skip system messages from executor — we'll inline them below
        if role == "system":
            return None
        # Tool result messages — keep as assistant context
        if role == "tool":
            return {"role": "user",
                    "content": f"[Tool result for {m.get('tool_call_id','?')}]: {content}"}
        # Assistant messages with tool_calls — summarise as text
        if role == "assistant":
            tool_calls = (m.get("tool_calls") if isinstance(m, dict)
                          else getattr(m, "tool_calls", None))
            if tool_calls and not content:
                names = [tc.function.name if hasattr(tc, "function")
                         else tc.get("function", {}).get("name", "?")
                         for tc in tool_calls]
                content = f"[Called tools: {', '.join(names)}]"
        return {"role": role, "content": str(content)}

    # Extract executor system prompt text to inline as context
    exec_system = next(
        (
            (m.get("content") if isinstance(m, dict) else getattr(m, "content", ""))
            for m in transcript
            if (m.get("role") if isinstance(m, dict) else getattr(m, "role", "")) == "system"
        ),
        "",
    )

    context_header = (
        f"EXECUTOR CONTEXT\n"
        f"Executor system prompt: {exec_system}\n\n"
        f"Executor conversation transcript follows:\n"
        f"{'─' * 50}\n"
    )

    normed = [_norm(m) for m in transcript]
    normed = [m for m in normed if m is not None]

    messages = [
        {"role": "system", "content": _ADVISOR_SYSTEM},
        # First user turn: inline executor context + transcript as quoted text
        {"role": "user",   "content": context_header},
        # Remaining turns: the normalised transcript (user/assistant alternation)
        *normed,
        # Final user turn: the actual advisory question
        {"role": "user", "content": user_instruction},
    ]

    t0 = time.monotonic()
    try:
        resp = client.chat.completions.create(
            model=advisor_model,
            messages=messages,
            max_tokens=max_tokens,
        )
        latency = time.monotonic() - t0
        advice  = resp.choices[0].message.content or ""
        usage   = resp.usage

        rec = UsageRecord(
            model         = advisor_model,
            role          = "advisor",
            input_tokens  = usage.prompt_tokens     if usage else 0,
            output_tokens = usage.completion_tokens if usage else 0,
            latency_s     = latency,
        )
        stats.records.append(rec)
        stats.advisor_calls               += 1
        stats.total_advisor_input_tokens  += rec.input_tokens
        stats.total_advisor_output_tokens += rec.output_tokens

        return advice

    except Exception as exc:
        # Advisor failure is non-fatal — executor continues without advice
        return f"[advisor unavailable: {exc}]"


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def run_agent_advised(
    prompt: str,
    tools: list[dict],
    dispatch: dict[str, Callable[[dict], str]],
    *,
    # ── Model selection ───────────────────────────────────────────────────────
    profile: str | None              = None,    # named profile (overrides model args)
    executor_model: str              = "openai/gpt-4o",
    advisor_model: str               = "anthropic/claude-sonnet-4-6",
    # ── Advisor behaviour ─────────────────────────────────────────────────────
    advisor_every_n_steps: int       = 1,       # advise on step 1, then every N steps
    advisor_on_completion: bool      = True,    # advise when executor is about to finish
    advisor_max_tokens: int          = 2048,    # hard cap on advisor output tokens
    advisor_word_limit: int          = 80,      # soft word-limit in advisor prompt
    # ── Executor behaviour ────────────────────────────────────────────────────
    system: str | None               = None,
    max_steps: int                   = 10,
    # ── Observability ─────────────────────────────────────────────────────────
    verbose: bool                    = False,   # print advisor guidance + step logs
    return_stats: bool               = False,   # return (answer, RunStats) instead of answer
) -> str | tuple[str, RunStats]:
    """
    Run a ReAct agent with an advisor model providing strategic guidance.

    Args:
        prompt:               The user's task description.
        tools:                OpenAI function-calling tool definitions (use make_tool()).
        dispatch:             {"tool_name": callable(args: dict) -> str}
        profile:              Named profile from PROFILES dict. Overrides model args.
                              Options: "speed", "balanced", "quality", "deep",
                                       "claude", "gpt", "economy"
        executor_model:       Model that executes tool calls and generates the answer.
        advisor_model:        Model consulted for strategic guidance mid-run.
        advisor_every_n_steps: Call advisor on step 1, then every N steps after.
                              1 = every step (maximum guidance, higher cost)
                              2 = every other step
                              0 = only on completion (if advisor_on_completion=True)
        advisor_on_completion: Call advisor one final time when executor is about
                               to return — catches mistakes before they reach the user.
        advisor_max_tokens:   Hard cap on advisor output per call (tokens).
                              Recommended: 2048 (≈630–840 actual output tokens, ~0% truncation)
        advisor_word_limit:   Soft word-limit injected into advisor's user prompt.
        system:               Executor system prompt. Defaults to AdvisorConfig.system.
        max_steps:            Safety cap on executor iterations.
        verbose:              Print step-by-step advisor guidance and token usage.
        return_stats:         If True, return (answer, RunStats) tuple.

    Returns:
        answer (str) — the executor's final response, OR
        (answer, RunStats) if return_stats=True
    """
    # ── Apply profile if requested ────────────────────────────────────────────
    if profile is not None:
        if profile not in PROFILES:
            available = ", ".join(PROFILES.keys())
            raise ValueError(f"Unknown profile '{profile}'. Available: {available}")
        cfg = PROFILES[profile]
        executor_model        = cfg.executor_model
        advisor_model         = cfg.advisor_model
        advisor_every_n_steps = cfg.advisor_every_n_steps
        advisor_on_completion = cfg.advisor_on_completion
        advisor_max_tokens    = cfg.advisor_max_tokens
        advisor_word_limit    = cfg.advisor_word_limit
        max_steps             = cfg.max_steps
        if system is None:
            system = cfg.system

    if system is None:
        system = AdvisorConfig().system

    # ── Init ──────────────────────────────────────────────────────────────────
    client = _bmw_client()
    stats  = RunStats(executor_model=executor_model, advisor_model=advisor_model)
    run_t0 = time.monotonic()

    messages: list[dict] = [
        {"role": "system", "content": system},
        {"role": "user",   "content": prompt},
    ]

    def _should_advise(step: int) -> bool:
        if advisor_every_n_steps <= 0:
            return False
        return step % advisor_every_n_steps == 0

    def _inject_advice(advice: str) -> None:
        """Inject advisor guidance as a synthetic user message."""
        if not advice or advice.startswith("[advisor unavailable"):
            return
        messages.append({
            "role": "user",
            "content": (
                f"[Strategic guidance from your advisor — give this serious weight]\n"
                f"{advice}\n"
                f"[End advisor guidance]"
            ),
        })
        if verbose:
            print(f"\n  💡 Advisor ({advisor_model}):\n"
                  f"  {textwrap.fill(advice, width=72, subsequent_indent='  ')}\n")

    # ── Agent loop ────────────────────────────────────────────────────────────
    for step in range(max_steps):

        # Advisory pass (before executor turn)
        if _should_advise(step):
            user_instr = _ADVISOR_USER_TEMPLATE.format(word_limit=advisor_word_limit)
            advice = _call_advisor(
                client, advisor_model, messages, user_instr, advisor_max_tokens, stats
            )
            _inject_advice(advice)

        # Executor pass
        if verbose:
            print(f"  🔄 Executor step {step + 1}/{max_steps} ({executor_model})")

        t0 = time.monotonic()
        response = client.chat.completions.create(
            model=executor_model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        latency = time.monotonic() - t0
        msg     = response.choices[0].message
        usage   = response.usage

        rec = UsageRecord(
            model         = executor_model,
            role          = "executor",
            input_tokens  = usage.prompt_tokens     if usage else 0,
            output_tokens = usage.completion_tokens if usage else 0,
            latency_s     = latency,
        )
        stats.records.append(rec)
        stats.executor_calls                += 1
        stats.total_executor_input_tokens   += rec.input_tokens
        stats.total_executor_output_tokens  += rec.output_tokens

        # Append executor message (handle both dict and object forms)
        messages.append(msg if isinstance(msg, dict) else msg)

        # ── No tool calls → executor is done ──────────────────────────────────
        if not msg.tool_calls:
            answer = msg.content or ""

            # Optional completion advisory pass
            if advisor_on_completion:
                comp_instr = _COMPLETION_ADVISOR_USER.format(word_limit=advisor_word_limit)
                comp_advice = _call_advisor(
                    client, advisor_model, messages, comp_instr, advisor_max_tokens, stats
                )
                if comp_advice and not comp_advice.startswith("[advisor unavailable"):
                    # If advisor flags issues, let executor revise
                    _inject_advice(comp_advice)
                    # One more executor pass to incorporate feedback
                    t0 = time.monotonic()
                    revision = client.chat.completions.create(
                        model=executor_model,
                        messages=messages,
                        tools=tools,
                        tool_choice="none",  # no more tool calls — just revise the answer
                    )
                    latency = time.monotonic() - t0
                    rev_msg = revision.choices[0].message
                    rev_usage = revision.usage
                    rec = UsageRecord(
                        model         = executor_model,
                        role          = "executor",
                        input_tokens  = rev_usage.prompt_tokens     if rev_usage else 0,
                        output_tokens = rev_usage.completion_tokens if rev_usage else 0,
                        latency_s     = latency,
                    )
                    stats.records.append(rec)
                    stats.executor_calls                += 1
                    stats.total_executor_input_tokens   += rec.input_tokens
                    stats.total_executor_output_tokens  += rec.output_tokens
                    answer = rev_msg.content or answer

            stats.total_wall_s = time.monotonic() - run_t0
            if verbose:
                print(f"\n{stats.summary()}")

            return (answer, stats) if return_stats else answer

        # ── Execute tool calls ─────────────────────────────────────────────────
        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)
            if verbose:
                print(f"    🔧 Tool call: {name}({json.dumps(args)[:80]})")
            try:
                fn     = dispatch.get(name)
                result = fn(args) if fn else f"Unknown tool: {name}"
            except Exception as exc:
                result = f"Tool error ({name}): {exc}"
            messages.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      str(result),
            })

    stats.total_wall_s = time.monotonic() - run_t0
    if verbose:
        print(f"\n{stats.summary()}")

    answer = "Agent did not converge within max_steps."
    return (answer, stats) if return_stats else answer


# ─────────────────────────────────────────────────────────────────────────────
# Interactive model picker  (CLI helper)
# ─────────────────────────────────────────────────────────────────────────────

def pick_profile(default: str = "balanced") -> dict:
    """
    Interactive CLI helper that prints model recommendations and lets the
    user pick a named profile or custom executor/advisor pair.

    Returns a kwargs dict suitable for run_agent_advised(**kwargs).
    """
    print("\n" + "═" * 60)
    print("  BMW Advisor-Enhanced Agent — Model Picker")
    print("═" * 60)

    print("\n  ── Named profiles (recommended) ──────────────────────")
    profile_descriptions = {
        "speed":    "Haiku executor + GPT-4o advisor. Fastest, cheapest.",
        "economy":  "GPT-4o-mini executor + GPT-4o advisor. Low cost.",
        "balanced": "GPT-4o executor + Claude Sonnet advisor. Best default. [DEFAULT]",
        "claude":   "Haiku executor + Sonnet advisor. Pure Anthropic stack.",
        "gpt":      "GPT-4o executor + GPT-5 advisor. Pure OpenAI stack.",
        "quality":  "Claude Sonnet executor + GPT-5 advisor. Cross-provider, high quality.",
        "deep":     "Claude Sonnet executor + o3 advisor. Best for planning/reasoning tasks.",
    }
    for name, desc in profile_descriptions.items():
        marker = " ◀" if name == default else ""
        print(f"    {name:<10} {desc}{marker}")

    print("\n  ── Model recommendations by use-case ─────────────────")
    recommendations = [
        ("Simple lookup / Q&A",          "economy or speed",      "Single tool call, low stakes"),
        ("Jira / SAP data workflows",     "balanced",              "Multi-step, reliable tool-calling"),
        ("Code generation / review",      "quality",               "Cross-provider diversity helps"),
        ("Risk / financial decisions",    "deep",                  "o3 advisor catches edge cases"),
        ("Long research pipelines",       "quality or deep",       "GPT-5 plans well over many steps"),
        ("Batch / high-volume",           "economy",               "Minimise cost at scale"),
        ("Fastest possible response",     "speed",                 "Haiku is very fast"),
    ]
    print(f"    {'Use-case':<32} {'Profile':<20} {'Why'}")
    print(f"    {'─'*32} {'─'*20} {'─'*30}")
    for use, profile_name, why in recommendations:
        print(f"    {use:<32} {profile_name:<20} {why}")

    print("\n  ── Executor / Advisor model tiers ────────────────────")
    print(f"    {'Model':<40} {'Tier':<6} {'Cost':<12} {'Speed':<10} {'Best as'}")
    print(f"    {'─'*40} {'─'*6} {'─'*12} {'─'*10} {'─'*20}")
    for model_id, meta in BMW_MODELS.items():
        if not meta["tools"]:
            continue
        best_as = []
        if meta["tier"] == 1:
            best_as = ["executor (complex)", "advisor"]
        elif meta["tier"] == 2:
            best_as = ["executor", "advisor (light)"]
        else:
            best_as = ["executor (simple)"]
        print(f"    {model_id:<40} {meta['tier']:<6} {meta['cost']:<12} "
              f"{meta['speed']:<10} {', '.join(best_as)}")

    print()
    choice = input(
        f"  Enter profile name or 'custom' [{default}]: "
    ).strip().lower() or default

    if choice == "custom":
        print("\n  Available models:")
        tool_models = [m for m, meta in BMW_MODELS.items() if meta["tools"]]
        for i, m in enumerate(tool_models, 1):
            print(f"    {i:>2}. {m}")

        exec_input = input("  Executor model (name or number): ").strip()
        adv_input  = input("  Advisor model  (name or number): ").strip()

        def _resolve(val: str) -> str:
            if val.isdigit():
                return tool_models[int(val) - 1]
            return val

        return {
            "executor_model": _resolve(exec_input),
            "advisor_model":  _resolve(adv_input),
        }

    if choice not in PROFILES:
        print(f"  Unknown profile '{choice}', using '{default}'.")
        choice = default

    return {"profile": choice}


def recommend(task_description: str) -> str:
    """
    Return a recommended profile name for a given task description.
    Simple keyword-based heuristic — no API call needed.

    Examples:
        recommend("query SAP order status")     → "balanced"
        recommend("generate python code")       → "quality"
        recommend("financial risk assessment")  → "deep"
    """
    desc = task_description.lower()

    # Deep reasoning signals
    if any(w in desc for w in ["risk", "financial", "compliance", "audit", "legal",
                                "architecture", "design decision", "plan"]):
        return "deep"

    # Quality signals
    if any(w in desc for w in ["code", "review", "generate", "implement", "refactor",
                                "debug", "test", "analyse", "analyze", "research"]):
        return "quality"

    # Speed signals
    if any(w in desc for w in ["quick", "fast", "simple", "lookup", "fetch", "get",
                                "list", "check", "ping", "status"]):
        return "speed"

    # Economy signals
    if any(w in desc for w in ["batch", "bulk", "many", "volume", "repeat"]):
        return "economy"

    # Default
    return "balanced"


# ─────────────────────────────────────────────────────────────────────────────
# Re-export make_tool from original bmw_tool_agent for convenience
# ─────────────────────────────────────────────────────────────────────────────

def make_tool(name: str, description: str, parameters: dict) -> dict:
    """Build a tool definition in OpenAI function-calling format."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
    }
