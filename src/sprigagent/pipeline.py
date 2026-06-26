"""Wires the four agents under the Orchestrator and runs them end-to-end.

``run_pipeline()`` is a synchronous wrapper over the async ADK ``Runner`` so that both
``main.py`` and the tests can call it without any async ceremony (and without needing
``pytest-asyncio``). Everything here runs fully in-process: ``InMemorySessionService``
plus the local stub model means no credentials and no network.
"""

from __future__ import annotations

import asyncio
import json

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from sprigagent.agents.detector import DETECTOR_OUTPUT_KEY
from sprigagent.agents.eval_runner import EVAL_OUTPUT_KEY
from sprigagent.agents.orchestrator import DECISION_KEY, DECLINED, NOTES_KEY, create_orchestrator
from sprigagent.agents.rewriter import REWRITER_OUTPUT_KEY
from sprigagent.model.provider import CALL_LOG
from sprigagent.types import (
    EvalResult,
    PipelineResult,
    PruneCandidate,
    PruneSuspect,
    SecurityStatus,
    SecurityVerdict,
)

APP_NAME = "sprigagent"
USER_ID = "local"
SESSION_ID = "phase-a"


def _loads(raw):
    """Parse JSON, returning None on anything that is not a JSON object (e.g. a blocked
    item's security message, which is plain text)."""
    if not raw:
        return None
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else None
    except (json.JSONDecodeError, TypeError):
        return None


def _assemble(state: dict) -> PipelineResult:
    """Build the typed PipelineResult from the final session state."""
    # Security verdict (what the checkpoint did to the input).
    event = state.get("security_event")
    redactions = tuple(state.get("redactions", ()))
    if event is not None:
        security = SecurityVerdict(
            status=SecurityStatus.BLOCKED,
            sanitized_content=None,
            categories=tuple(event.get("categories", ())),
            reason=event.get("reason"),
        )
    elif redactions:
        security = SecurityVerdict(
            status=SecurityStatus.REDACTED, sanitized_content=None, categories=redactions
        )
    else:
        security = SecurityVerdict(status=SecurityStatus.CLEAN, sanitized_content=None)

    suspect_d = _loads(state.get(DETECTOR_OUTPUT_KEY))
    candidate_d = _loads(state.get(REWRITER_OUTPUT_KEY))
    eval_d = _loads(state.get(EVAL_OUTPUT_KEY))

    return PipelineResult(
        decision=state.get(DECISION_KEY, DECLINED),
        security=security,
        suspect=PruneSuspect.from_dict(suspect_d) if suspect_d and "file" in suspect_d else None,
        candidate=PruneCandidate.from_dict(candidate_d) if candidate_d and "diff" in candidate_d else None,
        eval_result=EvalResult.from_dict(eval_d) if eval_d and "verdict" in eval_d else None,
        redactions=redactions,
        notes=state.get(NOTES_KEY, ""),
    )


async def _run_async(content: str) -> PipelineResult:
    # Reset the model call log so each run's bypass behaviour is independently assertable.
    CALL_LOG.clear()

    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    runner = Runner(
        agent=create_orchestrator(),
        app_name=APP_NAME,
        session_service=session_service,
    )

    message = genai_types.Content(role="user", parts=[genai_types.Part(text=content)])
    async for _event in runner.run_async(
        user_id=USER_ID, session_id=SESSION_ID, new_message=message
    ):
        pass  # events drive state; we read the assembled result from final state below

    session = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )
    return _assemble(session.state)


def run_pipeline(content: str) -> PipelineResult:
    """Run the full pipeline on a context-file snippet / fake diff. Synchronous."""
    return asyncio.run(_run_async(content))
