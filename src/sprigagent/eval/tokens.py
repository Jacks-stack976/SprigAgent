"""Offline token measurement for the Eval-Runner — the demo's headline savings number.

Two distinct token numbers flow through Phase 3 and must not be conflated:

  * context-file tokens — measured HERE, harness-side, on the full vs pruned config file.
    This is the headline: "the prune cut N tokens of always-loaded context." It is
    deterministic and offline, so the discrimination and determinism tests can pin it.
  * agent-usage tokens — the coding agent's own input/output spend, reported driver-side
    on AgentResult. Secondary cost; folded into EvalResult.evidence only.

The estimator below is intentionally crude and documented as approximate. It mirrors the
Phase-A StubModel convention (`len(text) // 4`) so the whole project speaks one dialect of
"a token is ~4 characters" until the real tokenizer lands at the Vertex flip.
"""

from __future__ import annotations

from typing import Protocol


class TokenCounter(Protocol):
    """The swappable seam for turning text into a token count."""

    def count(self, text: str) -> int: ...


class CharEstimator:
    """Offline, deterministic, dependency-free token estimate (~chars / 4).

    Approximate ON PURPOSE: a stand-in for a real tokenizer, not a substitute. It is
    honest about being a heuristic — good enough to rank "is the pruned file smaller, and
    by roughly how much," which is exactly the headline the demo needs. Counts tokens
    (an integer count), never characters as the reported unit.
    """

    def count(self, text: str) -> int:
        # PHASE-FLIP SWAP POINT: replace this body with Gemini's real token count, e.g.
        #     from vertexai.preview import tokenization
        #     tok = tokenization.get_tokenizer_for_model(MODEL)
        #     return tok.count_tokens(text).total_tokens
        # The TokenCounter Protocol stays identical; only this implementation changes.
        return max(1, len(text) // 4)


# The default counter the harness uses until the Vertex flip.
DEFAULT_COUNTER: TokenCounter = CharEstimator()
