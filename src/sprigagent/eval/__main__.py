"""CLI: prove a prune end-to-end, or take the single real smoke call.

    python -m sprigagent.eval <target-repo> <accept|reject>     # the harness sweep
    python -m sprigagent.eval <target-repo> --smoke <task-id>   # ONE real Gemini call

The sweep selects its driver from ``$SPRIG_DRIVER`` (default ``stub`` — offline, free,
deterministic; the Phase-3 demo path). ``--smoke`` forces the **real** Vertex path for
exactly one task and one ``driver.run``: it is the first paid call, a cost-guarded probe
that the real coding agent produces a patch which applies and passes that task's hidden
test. If credentials are absent it stops and prints what to set, making no call. It never
runs the sweep — that is a separate, deliberate step.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from sprigagent.eval.candidates import DEMO_CANDIDATES
from sprigagent.eval.grader import grade
from sprigagent.eval.harness import evaluate
from sprigagent.eval.sandbox import apply_patch, make_sandbox, teardown
from sprigagent.eval.selection import ENV_VAR, CredentialsMissing, make_driver_and_counter
from sprigagent.eval.tasks import load_tasks

_USAGE = (
    "usage:\n"
    "  python -m sprigagent.eval <target-repo> <{choices}>\n"
    "  python -m sprigagent.eval <target-repo> --smoke <task-id>"
)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv

    if len(args) == 3 and args[1] == "--smoke":
        return _smoke(Path(args[0]).expanduser(), args[2])

    if len(args) == 2 and args[1] in DEMO_CANDIDATES:
        return _sweep(Path(args[0]).expanduser(), args[1])

    print(_USAGE.format(choices="|".join(DEMO_CANDIDATES)), file=sys.stderr)
    return 2


def _sweep(target_repo: Path, candidate_key: str) -> int:
    """Run the full baseline-vs-pruned harness with the env-selected driver (stub default)."""
    mode = os.environ.get(ENV_VAR, "stub")
    try:
        driver, counter = make_driver_and_counter()
    except CredentialsMissing as exc:  # only reachable in vertex mode
        print(exc, file=sys.stderr)
        print("\nNo paid call was made.", file=sys.stderr)
        return 2

    candidate = DEMO_CANDIDATES[candidate_key]
    result = evaluate(target_repo, candidate, driver=driver, counter=counter)

    print(f"driver:    {mode}")
    print(f"target:    {target_repo}")
    print(f"candidate: {candidate.name}  (strip {candidate.heading!r})")
    print(f"baseline pass-rate: {result.success_before:.0%}")
    print(f"pruned   pass-rate: {result.success_after:.0%}")
    print(
        f"context tokens:     {result.token_before} -> {result.token_after} "
        f"({result.token_delta_pct:+.1f}%)"
    )
    print(f"VERDICT:   {result.verdict.value}")
    print(f"evidence:  {result.evidence}")
    return 0


def _smoke(target_repo: Path, task_id: str, file: str = "CLAUDE.md") -> int:
    """The single, cost-guarded paid call: one real ``driver.run`` on one task, then grade.

    ``file`` is the context file fed to the agent — defaults to "CLAUDE.md" so the demo probe is
    unchanged, but the read is no longer a bare literal (it honors the target file it is given).
    """
    try:
        # Force the real path regardless of $SPRIG_DRIVER; a missing env is a hard pre-call stop.
        driver, _counter = make_driver_and_counter(mode="vertex")
    except CredentialsMissing as exc:
        print(exc, file=sys.stderr)
        print("\nNo paid call was made.", file=sys.stderr)
        return 2

    tasks = {t.id: t for t in load_tasks(target_repo)}
    if task_id not in tasks:
        print(
            f"unknown task {task_id!r}; choices: {', '.join(tasks)}", file=sys.stderr
        )
        return 2
    task = tasks[task_id]
    full_text = (target_repo / file).read_text()

    sandbox = make_sandbox(target_repo)
    try:
        result = driver.run(sandbox, full_text, task)  # <-- the one paid call
        applied = apply_patch(sandbox, result.patch)
        passed = applied and grade(task, sandbox)
    finally:
        teardown(sandbox)

    print(f"SMOKE: one real Gemini call on task {task.id}")
    print(f"  patch applies:   {applied}")
    print(f"  hidden test:     {'PASS' if passed else 'FAIL'}")
    print(
        f"  agent tokens:    in={result.input_tokens} out={result.output_tokens} "
        "(real usage_metadata)"
    )
    print("  recorded to the replay cache for offline reproduction.")
    print("\nSTOP: single smoke call complete. The full sweep was NOT run.")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
