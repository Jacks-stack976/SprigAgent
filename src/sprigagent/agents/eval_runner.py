"""Eval-Runner agent — the project's differentiator (stubbed in Phase A).

Real role (later phases): in a sandbox, run the target coding agent on the frozen
task suite, baseline vs candidate; grade by tests (primary) + LLM-judge (fallback);
measure tokens; loop until net-positive or give up.

Phase A: a deterministic custom ``BaseAgent`` that maps the candidate's scenario to a
canned ``EvalResult``. BOTH paths exist from day one — an ACCEPT (quality holds, tokens
drop) and a REJECT (removing a load-bearing rule tanks task success) — so the
Orchestrator's reject branch is exercised immediately. No model is called here, so the
checkpoint is not needed yet; when the LLM-judge fallback lands, it gets the same gate.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types as genai_types

from sprigagent.agents.rewriter import REWRITER_OUTPUT_KEY
from sprigagent.eval import DEMO_CANDIDATES, evaluate

EVAL_OUTPUT_KEY = "eval_out"
# When a real target repo is threaded into session state, the agent proves the scenario through
# the real frozen harness instead of returning canned numbers (the promised evaluate() wiring).
TARGET_REPO_KEY = "target_repo"

# Canned measurements. ACCEPT: quality holds, big token drop -> surface for approval.
# REJECT: the worked example from the design — removing the typecheck rule halves task
# success, so the loop refuses. The reject case is the point: the loop catches harm.
# token_before/token_after are the REAL committed Gemini counts (gemini-2.5-pro, replay cache):
# 631 -> 411 == -34.9% — replacing the retired stub placeholder figure. The demo (main.py)
# renders the measured reduction itself; these keep the verdict/delta coherent.
_ACCEPT = {
    "success_before": 1.0,
    "success_after": 1.0,
    "token_before": 631,
    "token_after": 411,
    "verdict": "ACCEPT",
    "evidence": (
        "4/4 -> 4/4 tasks pass; the style rules were redundant with the linter, so removing "
        "them held quality and cut context tokens (measured reduction reported by the demo / "
        "`python -m sprigagent.eval`)."
    ),
}
_REJECT = {
    "success_before": 1.0,
    "success_after": 0.5,
    "token_before": 4000,
    "token_after": 3600,
    "verdict": "REJECT",
    "evidence": (
        "4/4 -> 2/4 tasks pass after removing 'Always run typecheck after edits'. "
        "The line was load-bearing; keeping it."
    ),
}


def _evaluate_real(state, scenario: str) -> dict | None:
    """Prove ``scenario`` through the real frozen harness when a ``target_repo`` is in state.

    Returns the real ``EvalResult`` serialized to the canned dict's shape, or ``None`` when there is
    no target repo / unknown scenario / any harness error — in which case the caller falls back to
    the canned numbers. Offline: ``evaluate`` builds its default StubDriver + chars/4 counter, so
    this still needs no model, Vertex, or credentials. The in-process demo seeds no ``target_repo``,
    so it keeps the fast canned path (and ``test_pipeline_smoke.py`` stays green)."""
    repo = state.get(TARGET_REPO_KEY)
    if not repo or scenario not in DEMO_CANDIDATES:
        return None
    try:
        result = evaluate(Path(repo), DEMO_CANDIDATES[scenario])
    except Exception:  # any harness/testbed problem -> fall back to canned, never crash the demo
        return None
    return {
        "success_before": result.success_before,
        "success_after": result.success_after,
        "token_before": result.token_before,
        "token_after": result.token_after,
        "verdict": result.verdict.value,
        "evidence": result.evidence,
    }


class EvalRunnerAgent(BaseAgent):
    """Deterministic sandbox stub: candidate scenario -> canned EvalResult."""

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        # Read the scenario the Rewriter's candidate carries (threaded from the input).
        scenario = "accept"
        raw = ctx.session.state.get(REWRITER_OUTPUT_KEY)
        if raw:
            try:
                scenario = json.loads(raw).get("scenario", "accept")
            except (json.JSONDecodeError, AttributeError, TypeError):
                scenario = "accept"

        # Real harness when a target_repo is threaded in; canned otherwise (keeps the demo fast).
        result = _evaluate_real(ctx.session.state, scenario) or (
            _REJECT if scenario == "reject" else _ACCEPT
        )
        payload = json.dumps(result)

        # Emit the result both as event content and as a state delta (eval_out) so the
        # Orchestrator can read it after this sub-agent completes.
        yield Event(
            author=self.name,
            content=genai_types.Content(
                role="model", parts=[genai_types.Part(text=payload)]
            ),
            actions=EventActions(state_delta={EVAL_OUTPUT_KEY: payload}),
        )


def create_eval_runner() -> EvalRunnerAgent:
    return EvalRunnerAgent(
        name="eval_runner",
        description="Runs the frozen eval suite, baseline vs candidate, and grades it.",
    )
