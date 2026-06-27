"""The single seam between the harness and whatever produces task patches.

Phase 3 ships `StubDriver` (deterministic fixture replay — no model, no network, no cost).
The next phase adds a `VertexAgentDriver` behind this same Protocol — running the real
Gemini coding agent against the task and capturing its diff — and the harness does not
change. This mirrors Phase A's `get_model()` / `# PHASE-7 SWAP POINT` discipline: one swap
site, stable callers.
"""

from __future__ import annotations

import difflib
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from sprigagent.eval.cache import Cache, ReplayMiss, patch_key
from sprigagent.eval.tasks import Task
from sprigagent.eval.tokens import DEFAULT_COUNTER, TokenCounter
from sprigagent.security import checkpoint
from sprigagent.types import SecurityStatus

_log = logging.getLogger("sprigagent.eval.driver")


@dataclass(frozen=True)
class AgentResult:
    """What a driver returns: the edit, plus the agent's own token spend."""

    patch: str         # a unified diff the HARNESS applies; the driver never mutates repo_dir
    input_tokens: int  # agent-side usage (secondary cost, not the headline)
    output_tokens: int


class AgentDriver(Protocol):
    """Given a repo, the context file to obey, and a task, produce a patch.

    Contract: the driver must NOT mutate `repo_dir` (it is a read-only view). It returns a
    unified diff; the harness applies that diff inside an isolated sandbox.
    """

    def run(self, repo_dir: Path, context_file_text: str, task: Task) -> AgentResult: ...


# What the StubDriver scans the context for to decide the cents rule is "present". The
# anchor lives only inside CLAUDE.md's money-convention block, so pruning that block (the
# REJECT candidate) makes this go absent and flips the dependent tasks to their naive fix.
_CENTS_RULE_ANCHOR = "integer cents"


class StubDriver:
    """Deterministic AgentDriver: replays a cached fixture patch per (task, context).

    The whole point is to reproduce Phase 2's discrimination THROUGH the harness without a
    model: if the load-bearing cents rule is present in the context, every task gets its
    convention-following `reference.patch`; if the rule has been pruned away, the tasks
    that depend on it (`targets_rule == "money-integer-cents"`) get the convention-ignoring
    `naive.patch` and so fail their hidden tests, while convention-neutral tasks still get
    `reference.patch`. Offline and deterministic.
    """

    def __init__(
        self, fixtures_dir: Path, counter: TokenCounter = DEFAULT_COUNTER
    ) -> None:
        self._fixtures = Path(fixtures_dir)
        self._counter = counter

    def run(self, repo_dir: Path, context_file_text: str, task: Task) -> AgentResult:
        # repo_dir is unused by the stub (it replays fixtures); it is part of the seam so
        # a real driver can read the repo to give the agent context.
        del repo_dir
        cents_present = _CENTS_RULE_ANCHOR in context_file_text.lower()
        depends_on_cents = task.targets_rule == "money-integer-cents"
        variant = "naive" if (depends_on_cents and not cents_present) else "reference"
        patch = (self._fixtures / task.id / f"{variant}.patch").read_text()
        # Stub "usage": deterministic, offline, illustrative only. The headline token
        # numbers come from the harness-side TokenCounter, never from here.
        input_tokens = self._counter.count(context_file_text) + self._counter.count(
            task.prompt
        )
        output_tokens = self._counter.count(patch)
        return AgentResult(
            patch=patch, input_tokens=input_tokens, output_tokens=output_tokens
        )


# ---------------------------------------------------------------------------
# VertexAgentDriver — the real coding agent behind the SAME AgentDriver Protocol.
# ---------------------------------------------------------------------------
# This is the Phase-7 flip target. The harness, sandbox, and grader do not change; only
# this implementation calls a real Gemini model. Every paid call is guarded: the security
# checkpoint runs FIRST (untrusted context never reaches the model on a hit), temperature is
# zero, output is bounded, and a record-replay cache means each request is paid for at most
# once. google.genai is imported lazily (inside the call sites), so this module imports — and
# the security/parse/diff logic below stays unit-testable — with no SDK and no credentials.

# Bounded output (cost guard): a hard ceiling, not a target. Sized with headroom for a
# *thinking* model — on Gemini 2.5 the reasoning tokens are billed against this SAME budget, so
# the budget must cover thinking + the answer or the JSON truncates mid-string and fails to
# parse. Measured: a single sprig-demo task spent ~7.9k tokens thinking, so a flash-sized 2048
# (or even 8192) starved the ~300-800 token answer. 16384 leaves ample room for both while
# keeping the call bounded; an updated src file itself is only a few hundred tokens.
MAX_OUTPUT_TOKENS = 16384

# The agent edits exactly one file and returns the whole file, so the harness's `git apply`
# always applies. Versioned by cache.TEMPLATE_VERSION: editing this text invalidates old
# recordings (it is hashed into the patch key) instead of replaying a stale prompt's answer.
_INSTRUCTIONS = (
    "You are editing the repository `sprig-demo`. Implement the TASK by modifying exactly "
    "ONE of the source files shown below. Obey every convention in the system instructions. "
    "Return ONLY a JSON object with two string fields:\n"
    '  "path":    the repo-relative path of the file you changed (e.g. "src/invoice.ts")\n'
    '  "content": the COMPLETE updated contents of that file\n'
    "Change only what the task requires; preserve everything else byte-for-byte."
)


@dataclass(frozen=True)
class _ModelReply:
    """What a `generate` callable returns — decoupled from the SDK so tests inject a fake."""

    text: str           # the model's raw JSON text ({"path":..., "content":...})
    input_tokens: int   # real prompt_token_count from usage_metadata
    output_tokens: int  # real candidates_token_count from usage_metadata


# (system_instruction, user_content) -> _ModelReply. Injectable; the default calls Gemini.
GenerateFn = Callable[[str, str], _ModelReply]

# Returned when the security checkpoint BLOCKS a call: an empty patch the harness scores as a
# task failure (it applies to nothing, and the unimplemented stub still throws on grade), so
# the task fails WITHOUT the model ever being invoked.
_BLOCKED_RESULT = AgentResult(patch="", input_tokens=0, output_tokens=0)


class VertexAgentDriver:
    """Real AgentDriver: drives a Gemini coding agent and returns its diff (record/replay).

    Contract matches `AgentDriver` exactly. `model` is the Vertex model id; `cache` is the
    record-replay store (record=True allows a real call on a miss; replay-only raises). Pass
    `generate` to inject a fake reply (offline tests / a shared client from the factory); when
    omitted, a real google.genai Vertex client is built lazily on the first paid call.
    """

    def __init__(
        self, *, model: str, cache: Cache, generate: GenerateFn | None = None
    ) -> None:
        self._model = model
        self._cache = cache
        self._generate = generate

    def run(self, repo_dir: Path, context_file_text: str, task: Task) -> AgentResult:
        src_files = _read_src(repo_dir)
        system_instruction = context_file_text
        user_content = _build_user_content(task, src_files)

        # SECURITY CHECKPOINT (non-negotiable #2): scan both payloads BEFORE any API call.
        # BLOCKED -> no call, security event, sentinel failure. The driver talks to Gemini
        # directly, so it does not inherit ADK's before_model_callback — it must scan itself.
        safe_system = self._scan(system_instruction, task, "system instructions (context file)")
        if safe_system is None:
            return _BLOCKED_RESULT
        safe_user = self._scan(user_content, task, "task prompt + source files")
        if safe_user is None:
            return _BLOCKED_RESULT

        key = patch_key(self._model, safe_system, safe_user)
        cached = self._cache.get_patch(task.id, key)
        if cached is not None:
            return AgentResult(
                patch=cached["patch"],
                input_tokens=int(cached["input_tokens"]),
                output_tokens=int(cached["output_tokens"]),
            )
        if not self._cache.record:
            raise ReplayMiss(
                f"no recorded patch for task {task.id} (key {key[:12]}…); run in vertex "
                "(record) mode to capture it before replaying offline"
            )

        reply = self._generate_fn()(safe_system, safe_user)  # the paid call
        patch = _patch_from_reply(reply.text, src_files)
        if patch:
            self._cache.put_patch(
                task.id,
                key,
                {
                    "patch": patch,
                    "input_tokens": reply.input_tokens,
                    "output_tokens": reply.output_tokens,
                    "model": self._model,
                },
            )
        else:
            # Bad JSON, wrong/foreign path, or a no-op edit. Don't cache a non-answer; the
            # empty patch scores the task as a failure rather than crashing the harness.
            _log.warning(
                "eval-driver: model reply for task %s yielded no usable {path,content} "
                "patch; scoring the task as a failure",
                task.id,
            )
        return AgentResult(
            patch=patch,
            input_tokens=reply.input_tokens,
            output_tokens=reply.output_tokens,
        )

    def _scan(self, text: str, task: Task, label: str) -> str | None:
        """Run the security checkpoint; return safe text, or None if BLOCKED (no call)."""
        verdict = checkpoint.scan(text)
        if verdict.status is SecurityStatus.BLOCKED:
            _log.warning(
                "%s eval-driver blocked a Gemini call for task %s: prompt-injection "
                "intent=%s in %s. Content was treated as untrusted data and routed to "
                "human review; the model was NOT invoked.",
                checkpoint.SECURITY_EVENT_PREFIX,
                task.id,
                verdict.reason,
                label,
            )
            return None
        # CLEAN -> sanitized_content is the original; REDACTED -> PII-stripped text.
        return verdict.sanitized_content

    def _generate_fn(self) -> GenerateFn:
        if self._generate is None:
            self._generate = _default_generate(self._model)
        return self._generate


def _read_src(repo_dir: Path) -> dict[str, str]:
    """Read every `src/*.ts` file, keyed by repo-relative posix path, in sorted order."""
    repo_dir = Path(repo_dir)
    files: dict[str, str] = {}
    for path in sorted((repo_dir / "src").glob("*.ts")):
        files[path.relative_to(repo_dir).as_posix()] = path.read_text()
    return files


def _build_user_content(task: Task, src_files: dict[str, str]) -> str:
    """Assemble the user message: the task, the output contract, then the source files."""
    blocks = [f"===== {rel} =====\n{text}" for rel, text in src_files.items()]
    return f"TASK\n{task.prompt}\n\n{_INSTRUCTIONS}\n\nFILES\n" + "\n\n".join(blocks) + "\n"


def _patch_from_reply(text: str, src_files: dict[str, str]) -> str:
    """Turn the model's `{path, content}` JSON into a local unified diff, or "" if unusable.

    Returns "" (-> task failure, never a crash) for malformed JSON, a missing/non-string
    field, a `path` that is not one of the real files we showed the model, or a no-op edit.
    The diff is computed LOCALLY (difflib, `a/`/`b/` prefixes) so the harness's `git apply
    -p1` always applies the agent's chosen file.
    """
    try:
        data = json.loads(text)
        path = data["path"]
        content = data["content"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return ""
    if not isinstance(path, str) or not isinstance(content, str):
        return ""
    if path not in src_files:  # must be a real file under src/ that we actually sent
        return ""
    old = src_files[path]
    if content == old:
        return ""  # no change -> nothing to apply -> the task fails honestly
    diff = difflib.unified_diff(
        old.splitlines(keepends=True),
        content.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
    )
    return "".join(diff)


def gemini_generate(
    client, model: str, system_instruction: str, user_content: str
) -> _ModelReply:
    """One real Gemini call: temp 0, bounded output, JSON mode, real usage from metadata.

    `client` is a built `google.genai` client (injected by the factory so driver and counter
    share one). Kept module-level so the selection factory can reuse it with a shared client.
    """
    from google.genai import types

    response = client.models.generate_content(
        model=model,
        contents=user_content,
        config=types.GenerateContentConfig(
            temperature=0,                        # cost + determinism guard
            max_output_tokens=MAX_OUTPUT_TOKENS,  # bounded-output cost guard
            system_instruction=system_instruction,
            response_mime_type="application/json",
        ),
    )
    usage = response.usage_metadata
    return _ModelReply(
        text=response.text or "",
        input_tokens=int(getattr(usage, "prompt_token_count", 0) or 0),
        output_tokens=int(getattr(usage, "candidates_token_count", 0) or 0),
    )


def build_vertex_client():
    """Lazily construct a google.genai Vertex client from the ambient credentials.

    Imported here (not at module top) so this file loads with no SDK/creds. Credential
    presence is validated up-front in `selection.py`; this is just the construction site.
    """
    import os

    from google import genai

    return genai.Client(
        vertexai=True,
        project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        location=os.environ.get("GOOGLE_CLOUD_LOCATION"),
    )


def _default_generate(model: str) -> GenerateFn:
    """A `generate` callable that builds a Vertex client lazily on first use, then reuses it."""
    holder: dict[str, object] = {}

    def generate(system_instruction: str, user_content: str) -> _ModelReply:
        client = holder.get("client")
        if client is None:
            client = holder["client"] = build_vertex_client()
        return gemini_generate(client, model, system_instruction, user_content)

    return generate
