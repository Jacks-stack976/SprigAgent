"""The single seam between the harness and whatever produces task patches.

Phase 3 ships `StubDriver` (deterministic fixture replay — no model, no network, no cost).
The next phase adds a `VertexAgentDriver` behind this same Protocol — running the real
Gemini coding agent against the task and capturing its diff — and the harness does not
change. This mirrors Phase A's `get_model()` / `# PHASE-7 SWAP POINT` discipline: one swap
site, stable callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from sprigagent.eval.tasks import Task
from sprigagent.eval.tokens import DEFAULT_COUNTER, TokenCounter


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
