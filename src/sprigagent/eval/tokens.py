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

from collections.abc import Callable
from typing import Protocol

from sprigagent.eval.cache import Cache, ReplayMiss, token_key


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
        # PHASE-FLIP SWAP POINT: the real Gemini counter is `GeminiTokenCounter` below — same
        # TokenCounter Protocol, opt-in via the selection factory. CharEstimator stays the
        # default so the offline path needs no credentials and no network.
        return max(1, len(text) // 4)


# The default counter the harness uses until the Vertex flip.
DEFAULT_COUNTER: TokenCounter = CharEstimator()


# ---------------------------------------------------------------------------
# GeminiTokenCounter — the REAL token count, behind the SAME TokenCounter Protocol.
# ---------------------------------------------------------------------------
# Replaces the chars/4 heuristic with Gemini's `count_tokens`, wrapped by the same
# record-replay cache the driver uses, so each distinct text is counted (and paid for) at
# most once and the offline replay test reproduces the real numbers for free. google.genai is
# imported lazily (inside the call sites), so this module loads with no SDK and no credentials.
#
# Scope note: counting is a measurement call, not a generative one — the content is never
# interpreted as instructions — so the security checkpoint (which guards the *model* boundary)
# lives in the driver, not here. The demo's context file is clean regardless.

# (text) -> token count. Injectable; the default calls Gemini's count_tokens.
CountFn = Callable[[str], int]


class GeminiTokenCounter:
    """Real TokenCounter: Gemini `count_tokens`, record-replay cached.

    `model` is the Vertex model id; `cache` is the record-replay store (record=True allows a
    real call on a miss, replay-only raises). Pass `count_fn` to inject a fake count (offline
    tests / a shared client from the factory); when omitted, a Vertex client is built lazily.
    """

    def __init__(
        self, *, model: str, cache: Cache, count_fn: CountFn | None = None
    ) -> None:
        self._model = model
        self._cache = cache
        self._count_fn = count_fn

    def count(self, text: str) -> int:
        key = token_key(self._model, text)
        cached = self._cache.get_tokens(key)
        if cached is not None:
            return int(cached["total_tokens"])
        if not self._cache.record:
            raise ReplayMiss(
                f"no recorded token count (key {key[:12]}…); run in vertex (record) mode "
                "to capture it before replaying offline"
            )
        total = self._fn()(text)  # the paid call
        self._cache.put_tokens(key, {"total_tokens": total, "model": self._model})
        return total

    def _fn(self) -> CountFn:
        if self._count_fn is None:
            self._count_fn = _default_count(self._model)
        return self._count_fn


def gemini_count(client, model: str, text: str) -> int:
    """One real `count_tokens` call. `client` is a built google.genai client (shared)."""
    response = client.models.count_tokens(model=model, contents=text)
    return int(response.total_tokens)


def _default_count(model: str) -> CountFn:
    """A `count_fn` that builds a Vertex client lazily on first use, then reuses it."""
    # Imported lazily to dodge a driver<->tokens import cycle and to keep this module SDK-free.
    from sprigagent.eval.driver import build_vertex_client

    holder: dict[str, object] = {}

    def count(text: str) -> int:
        client = holder.get("client")
        if client is None:
            client = holder["client"] = build_vertex_client()
        return gemini_count(client, model, text)

    return count
