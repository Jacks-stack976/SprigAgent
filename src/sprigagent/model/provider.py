"""The single model-swap point for SprigAgent.

Every agent obtains its model *only* through ``get_model()``. In Phase A that returns a
local, deterministic stub — no Vertex, no network, no credentials. The Phase-7 Vertex
flip is a one-line change here (see ``# PHASE-7 SWAP POINT`` below); nothing else in the
codebase changes.

The stub is INPUT-RESPONSIVE: it keys its canned answer off a scenario marker embedded in
the request, exactly as a real model reads its prompt. So the demo paths (accept vs
reject) differ only by the input flowing through identical wiring — never by hardcoded
position. ``role`` selects the output *shape*; the input marker selects the *scenario*.
"""

from __future__ import annotations

import json
import re
from typing import AsyncGenerator

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types as genai_types

# Records every real model call as (role, scenario). The security checkpoint blocks
# injected input *before* the model, so when it fires this log stays flat — which the
# tests assert as proof the model was genuinely bypassed, not merely unused.
CALL_LOG: list[tuple[str, str]] = []

# Scenario sentinel the stub keys off. Read from the (post-checkpoint) request text.
_SCENARIO_RE = re.compile(r"\[\[scenario:(\w+)\]\]")
_DEFAULT_SCENARIO = "accept"


# --- Canned responses, keyed [role][scenario]. role -> shape, marker -> scenario. ------
# These mimic what a real Detector/Rewriter LLM would return as JSON. The Rewriter's
# candidate embeds its suspect and carries the scenario forward to the Eval-Runner.

_SUSPECTS = {
    "accept": {
        "file": "CLAUDE.md",
        "locator": "L40-L79",
        "kind": "bloat",
        "reason": (
            "40 lines of formatting/style rules already enforced by the configured "
            "linter (ruff + prettier). Redundant guidance the agent re-reads every "
            "session without it changing behaviour."
        ),
    },
    "reject": {
        "file": "CLAUDE.md",
        "locator": "L12",
        "kind": "bloat",
        "reason": (
            "The single rule 'Always run typecheck after edits' looks like process "
            "boilerplate and is a candidate for removal."
        ),
    },
}

_CANDIDATES = {
    "accept": {
        "suspect": _SUSPECTS["accept"],
        "diff": (
            "--- a/CLAUDE.md\n+++ b/CLAUDE.md\n@@ -40,40 +0,0 @@\n"
            "-## Style\n-- Use 2-space indentation\n-- Max line length 100\n"
            "-- Prefer single quotes\n-  ... (36 more linter-covered style lines) ...\n"
        ),
        "removed_lines": [
            "## Style",
            "- Use 2-space indentation",
            "- Max line length 100",
            "- Prefer single quotes",
            "- ... (36 more lines, all enforced by ruff/prettier) ...",
        ],
        "rationale": (
            "Every removed line restates a rule the linter already enforces, so the "
            "coding agent loses no information — only redundant tokens."
        ),
        "scenario": "accept",
    },
    "reject": {
        "suspect": _SUSPECTS["reject"],
        "diff": (
            "--- a/CLAUDE.md\n+++ b/CLAUDE.md\n@@ -12,1 +0,0 @@\n"
            "-- Always run typecheck after edits\n"
        ),
        "removed_lines": ["- Always run typecheck after edits"],
        "rationale": (
            "Looks like boilerplate; proposing removal to save tokens. (The Eval-Runner "
            "will measure whether it is actually load-bearing.)"
        ),
        "scenario": "reject",
    },
}

CANNED: dict[str, dict[str, str]] = {
    "detector": {
        "accept": json.dumps(_SUSPECTS["accept"]),
        "reject": json.dumps(_SUSPECTS["reject"]),
    },
    "rewriter": {
        "accept": json.dumps(_CANDIDATES["accept"]),
        "reject": json.dumps(_CANDIDATES["reject"]),
    },
}


def _request_text(llm_request: LlmRequest) -> str:
    """Flatten the request's text parts (what a real model would condition on)."""
    chunks: list[str] = []
    for content in (llm_request.contents or []):
        for part in (content.parts or []):
            if getattr(part, "text", None):
                chunks.append(part.text)
    return "\n".join(chunks)


def _scenario_from(text: str) -> str:
    match = _SCENARIO_RE.search(text)
    return match.group(1) if match else _DEFAULT_SCENARIO


class StubModel(BaseLlm):
    """Deterministic, offline stand-in for a Gemini model (Phase A only).

    Implements ADK's ``BaseLlm.generate_content_async`` and yields exactly one complete
    response, chosen by ``role`` (shape) and the input scenario marker (path).
    """

    role: str = "detector"

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        text = _request_text(llm_request)
        scenario = _scenario_from(text)
        CALL_LOG.append((self.role, scenario))

        by_role = CANNED.get(self.role, {})
        payload = by_role.get(scenario) or by_role.get(_DEFAULT_SCENARIO, "{}")

        # Report rough token counts (~4 chars/token). A stub model has no real usage,
        # but providing it keeps ADK's telemetry quiet and is apt for a token-measuring
        # project — later phases read real usage from the Vertex response here.
        prompt_tokens = max(1, len(text) // 4)
        output_tokens = max(1, len(payload) // 4)
        usage = genai_types.GenerateContentResponseUsageMetadata(
            prompt_token_count=prompt_tokens,
            candidates_token_count=output_tokens,
            total_token_count=prompt_tokens + output_tokens,
        )

        yield LlmResponse(
            content=genai_types.Content(
                role="model", parts=[genai_types.Part(text=payload)]
            ),
            partial=False,
            usage_metadata=usage,
        )


def get_model(role: str) -> BaseLlm:
    """Return the model an agent should use. This is the project's single swap point.

    Phase A returns a local deterministic stub (no network, no credentials).
    """
    # PHASE-7 SWAP POINT: replace the return below with the Vertex Gemini model, e.g.
    #     import os
    #     from google.adk.models import Gemini
    #     return Gemini(model=os.environ["VERTEX_MODEL"])   # the `role` arg becomes moot
    return StubModel(model=f"sprigagent-stub/{role}", role=role)
