"""Orchestrator agent.

Real role (later phases): drive the accept / retry / give-up loop and decide when to
stop. Phase A: a custom ``BaseAgent`` that sequences Detector -> Rewriter -> Eval-Runner
in a single pass, short-circuits on a security event, and records the decision. The
retry/give-up loop drops in behind this same interface at Phase 6.

Autonomous entry (additive): ``run_autonomous`` is the real deterministic, offline accept /
retry / give-up loop (``sprigagent.orchestrate.orchestrate``) — discover suspects, prove the
strongest prune, ladder gentler on a reject, give up (keep the rule) when exhausted, and
aggregate into the Approval-UI's ``OrchestrationResult``. Same shape as the Detector/Rewriter
rounds' ``discover()`` / ``propose()``: the stub ``create_orchestrator()`` ADK agent below is
left exactly as-is (rewiring the Track-1 LlmAgents to the engines is a separate, later step).
"""

from __future__ import annotations

from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types as genai_types

from sprigagent.agents.detector import DETECTOR_OUTPUT_KEY, create_detector
from sprigagent.agents.eval_runner import EVAL_OUTPUT_KEY, create_eval_runner
from sprigagent.agents.rewriter import REWRITER_OUTPUT_KEY, create_rewriter
from sprigagent.orchestrate import orchestrate as run_autonomous  # noqa: F401  (re-exported engine)
from sprigagent.security.checkpoint import SECURITY_EVENT_PREFIX

DECISION_KEY = "decision"
NOTES_KEY = "notes"

# Decision values the dashboard / demo surface (also stored in PipelineResult.decision).
SURFACED = "SURFACED"            # proven net-positive -> show the human a card to approve
DECLINED = "DECLINED"           # measured harm -> refuse the prune
SECURITY_EVENT = "SECURITY_EVENT"  # injection blocked before the model -> human review


class OrchestratorAgent(BaseAgent):
    """Sequences the three agents and decides the outcome (single pass in Phase A)."""

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state
        detector = self.find_sub_agent("detector")
        rewriter = self.find_sub_agent("rewriter")
        eval_runner = self.find_sub_agent("eval_runner")

        # --- Stage 1: Detector. Its model boundary is where the security checkpoint
        # fires, so a blocked/redacted input is handled before any real model call. ---
        detector_text = ""
        async for event in detector.run_async(ctx):
            if event.content and event.content.parts and event.content.parts[0].text:
                detector_text = event.content.parts[0].text
            yield event

        # Security short-circuit: trust the recorded event, with the response sentinel
        # as a belt-and-suspenders fallback. A blocked item never proceeds to a model.
        blocked = (
            state.get("security_event") is not None
            or detector_text.startswith(SECURITY_EVENT_PREFIX)
        )
        if blocked:
            reason = (state.get("security_event") or {}).get("reason", "prompt-injection")
            async for event in self._finish(
                SECURITY_EVENT,
                f"Input blocked by the security checkpoint (intent: {reason}); "
                f"routed to human review. The model was never invoked.",
            ):
                yield event
            return

        # --- Stage 2: Rewriter — proposes the candidate edit. ---
        async for event in rewriter.run_async(ctx):
            yield event

        # --- Stage 3: Eval-Runner — measures baseline vs candidate. ---
        async for event in eval_runner.run_async(ctx):
            yield event

        # --- Decide. ACCEPT -> surface; REJECT/anything-else -> decline. (A real loop
        # would, on REJECT, ask the Rewriter for a gentler edit or give up — Phase 6.) ---
        import json

        verdict = "REJECT"
        eval_raw = state.get(EVAL_OUTPUT_KEY)
        if eval_raw:
            try:
                verdict = json.loads(eval_raw).get("verdict", "REJECT")
            except (json.JSONDecodeError, AttributeError, TypeError):
                verdict = "REJECT"

        if verdict == "ACCEPT":
            decision, notes = SURFACED, "Proven net-positive: quality held, tokens dropped. Surfaced for human approval."
        else:
            decision, notes = DECLINED, "Measured harm: prune declined (the line is load-bearing)."

        async for event in self._finish(decision, notes):
            yield event

    async def _finish(self, decision: str, notes: str) -> AsyncGenerator[Event, None]:
        """Emit the terminal decision as both event content and a state delta."""
        yield Event(
            author=self.name,
            content=genai_types.Content(
                role="model", parts=[genai_types.Part(text=f"{decision}: {notes}")]
            ),
            actions=EventActions(state_delta={DECISION_KEY: decision, NOTES_KEY: notes}),
        )


def create_orchestrator() -> OrchestratorAgent:
    """Build the whole agent tree once (factories called here avoid parent conflicts)."""
    return OrchestratorAgent(
        name="orchestrator",
        description="Sequences Detector -> Rewriter -> Eval-Runner and decides the outcome.",
        sub_agents=[create_detector(), create_rewriter(), create_eval_runner()],
    )
