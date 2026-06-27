"""Opt-in selection of the eval driver + token counter — the one place real mode turns on.

`make_driver_and_counter()` reads ``SPRIG_DRIVER`` (default ``stub``) and returns the
``(driver, counter)`` pair the CLI hands to ``evaluate()``. The default path is unchanged
from Phase 3: offline, free, deterministic, no credentials. Real mode is strictly opt-in.

  * ``stub``   -> ``(None, CharEstimator())``. ``evaluate`` builds its StubDriver from the
                  bundled fixtures; the headline counter is the chars/4 estimator. Offline.
  * ``vertex`` -> ``(VertexAgentDriver, GeminiTokenCounter)`` in **record** mode. Requires a
                  configured Vertex environment; raises ``CredentialsMissing`` BEFORE any call
                  if it is absent. One lazily-built client is shared by both.
  * ``replay`` -> the same real classes in **replay-only** mode. Offline: every value comes
                  from the committed cache, a miss raises rather than reaching the network, so
                  no credentials are needed (only ``VERTEX_MODEL``, to match the recorded keys).

This module performs the credential pre-check; the harness, sandbox, and grader never learn
which driver they are running.
"""

from __future__ import annotations

import os

import sprigagent.eval.driver as driver_mod
import sprigagent.eval.tokens as tokens_mod
from sprigagent.eval.cache import Cache
from sprigagent.eval.driver import AgentDriver, VertexAgentDriver
from sprigagent.eval.tokens import CharEstimator, GeminiTokenCounter, TokenCounter

ENV_VAR = "SPRIG_DRIVER"
_PROJECT = "GOOGLE_CLOUD_PROJECT"
_LOCATION = "GOOGLE_CLOUD_LOCATION"
_MODEL = "VERTEX_MODEL"

_HOW_TO_ENABLE = (
    "Enable real Vertex mode before any paid call:\n"
    "  gcloud auth application-default login\n"
    f"  export {_PROJECT}=<your-gcp-project>\n"
    f"  export {_LOCATION}=<region, e.g. us-central1>\n"
    f"  export {_MODEL}=<model, e.g. gemini-2.0-flash-001>\n"
    f"  export {ENV_VAR}=vertex"
)


class CredentialsMissing(RuntimeError):
    """Real mode requested, but the Vertex environment is not configured (raised PRE-call)."""


def _require(*names: str) -> dict[str, str]:
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        raise CredentialsMissing(
            "real Vertex mode needs these unset variable(s): "
            + ", ".join(missing)
            + ".\n"
            + _HOW_TO_ENABLE
        )
    return {n: os.environ[n] for n in names}


def _lazy_vertex_client():
    """A zero-arg getter that builds one google.genai client on first use, then reuses it."""
    holder: dict[str, object] = {}

    def get():
        client = holder.get("client")
        if client is None:
            client = holder["client"] = driver_mod.build_vertex_client()
        return client

    return get


def make_driver_and_counter(
    mode: str | None = None, *, cache_dir=None
) -> tuple[AgentDriver | None, TokenCounter]:
    """Return the ``(driver, counter)`` pair for ``mode`` (or ``$SPRIG_DRIVER``, default stub).

    A ``None`` driver means "let ``evaluate`` build the default StubDriver" — kept so the
    stub path stays byte-for-byte the Phase-3 behaviour.
    """
    mode = (mode or os.environ.get(ENV_VAR, "stub")).lower()

    if mode == "stub":
        return None, CharEstimator()

    if mode == "replay":
        # Offline: real classes, replay-only cache. Needs only the model id (it is hashed
        # into the keys), never credentials — a miss raises before any client is built.
        model = _require(_MODEL)[_MODEL]
        cache = Cache(cache_dir, record=False)
        driver = VertexAgentDriver(model=model, cache=cache)
        counter = GeminiTokenCounter(model=model, cache=cache)
        return driver, counter

    if mode == "vertex":
        env = _require(_PROJECT, _LOCATION, _MODEL)  # hard pre-call error if absent
        model = env[_MODEL]
        cache = Cache(cache_dir, record=True)
        client = _lazy_vertex_client()  # one client shared by driver + counter
        driver = VertexAgentDriver(
            model=model,
            cache=cache,
            generate=lambda system, user: driver_mod.gemini_generate(
                client(), model, system, user
            ),
        )
        counter = GeminiTokenCounter(
            model=model,
            cache=cache,
            count_fn=lambda text: tokens_mod.gemini_count(client(), model, text),
        )
        return driver, counter

    raise ValueError(f"unknown {ENV_VAR}={mode!r}; expected one of: stub, vertex, replay")
