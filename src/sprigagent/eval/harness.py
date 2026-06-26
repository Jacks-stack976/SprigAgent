"""The Eval-Runner harness: prove a prune by measuring baseline vs pruned, offline.

`evaluate()` runs every task twice — once with the full context file (baseline), once with
the candidate's pruned context file — through the driver -> sandbox -> apply -> grade
pipeline, measures the context-file token delta, and returns the project's EXISTING
`EvalResult` (no new return type) with a verdict. No model, no network: the StubDriver
replays fixtures and the TokenCounter is offline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sprigagent.eval.candidates import Candidate, prune
from sprigagent.eval.driver import AgentDriver, StubDriver
from sprigagent.eval.grader import grade
from sprigagent.eval.sandbox import apply_patch, make_sandbox, teardown
from sprigagent.eval.tasks import Task, load_tasks
from sprigagent.eval.tokens import DEFAULT_COUNTER, TokenCounter
from sprigagent.types import EvalResult, Verdict


@dataclass(frozen=True)
class _SuiteRun:
    rate: float                                # pass-rate, 0.0-1.0
    per_task: tuple[tuple[str, bool], ...]     # (task_id, passed) in suite order
    agent_tokens: int                          # summed driver-side usage (secondary)


def _run_suite(
    target_repo: Path, tasks: list[Task], context_text: str, driver: AgentDriver
) -> _SuiteRun:
    """Run every task once under one context file; fresh sandbox per task."""
    passed = 0
    per_task: list[tuple[str, bool]] = []
    agent_tokens = 0
    for task in tasks:
        sandbox = make_sandbox(target_repo)
        try:
            result = driver.run(sandbox, context_text, task)
            agent_tokens += result.input_tokens + result.output_tokens
            ok = apply_patch(sandbox, result.patch) and grade(task, sandbox)
        finally:
            teardown(sandbox)
        per_task.append((task.id, ok))
        passed += int(ok)
    rate = passed / len(tasks) if tasks else 0.0
    return _SuiteRun(rate=rate, per_task=tuple(per_task), agent_tokens=agent_tokens)


def _decide(
    before_rate: float, after_rate: float, token_before: int, token_after: int
) -> Verdict:
    """ACCEPT only if quality held AND tokens dropped; REJECT if quality regressed."""
    if after_rate < before_rate:
        return Verdict.REJECT
    if after_rate >= before_rate and token_after < token_before:
        return Verdict.ACCEPT
    return Verdict.GAVE_UP


def evaluate(
    target_repo: Path,
    candidate: Candidate,
    *,
    driver: AgentDriver | None = None,
    counter: TokenCounter = DEFAULT_COUNTER,
    fixtures_dir: Path | None = None,
) -> EvalResult:
    """Measure `candidate` against `target_repo` and return an `EvalResult` verdict.

    `driver` defaults to a StubDriver over `fixtures_dir` (or the repo's bundled fixtures).
    `counter` measures the headline context-file tokens.
    """
    target_repo = Path(target_repo)
    if driver is None:
        driver = StubDriver(fixtures_dir or _default_fixtures_dir(), counter=counter)

    tasks = load_tasks(target_repo)
    full_text = (target_repo / "CLAUDE.md").read_text()
    pruned_text = prune(full_text, candidate)

    before = _run_suite(target_repo, tasks, full_text, driver)
    after = _run_suite(target_repo, tasks, pruned_text, driver)

    token_before = counter.count(full_text)
    token_after = counter.count(pruned_text)
    verdict = _decide(before.rate, after.rate, token_before, token_after)
    evidence = _evidence(candidate, before, after, token_before, token_after, verdict)

    return EvalResult(
        success_before=before.rate,
        success_after=after.rate,
        token_before=token_before,
        token_after=token_after,
        verdict=verdict,
        evidence=evidence,
    )


def _evidence(
    candidate: Candidate,
    before: _SuiteRun,
    after: _SuiteRun,
    token_before: int,
    token_after: int,
    verdict: Verdict,
) -> str:
    def fmt(run: _SuiteRun) -> str:
        return ", ".join(
            f"{tid}:{'pass' if ok else 'FAIL'}" for tid, ok in run.per_task
        )

    pct = (
        round((token_after - token_before) / token_before * 100, 1)
        if token_before
        else 0.0
    )
    return (
        f"candidate={candidate.name} verdict={verdict.value}; "
        f"baseline {before.rate:.0%} [{fmt(before)}]; "
        f"pruned {after.rate:.0%} [{fmt(after)}]; "
        f"context tokens {token_before}->{token_after} ({pct:+.1f}%); "
        f"agent usage ~{before.agent_tokens}->{after.agent_tokens} tok (secondary)"
    )


def _default_fixtures_dir() -> Path:
    # Demo default: the captured fixtures live in this repo's tests tree. The CLI relies on
    # this repo-relative path; tests pass `fixtures_dir` explicitly.
    return Path(__file__).resolve().parents[3] / "tests" / "eval" / "fixtures"
