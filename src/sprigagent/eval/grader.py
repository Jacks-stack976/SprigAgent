"""Grading a single task: run its hidden test in the sandbox; exit 0 = pass.

Tests-primary. Because each `task.json`'s `test_cmd` is its own vitest process, one task's
failure (or a thrown stub) is a clean non-zero exit, never a crash that takes down the
others — the RED-not-ERROR property proved in Phase 2, preserved here.
"""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

from sprigagent.eval.tasks import Task


def grade(task: Task, sandbox: Path) -> bool:
    """Run the task's hidden test inside `sandbox`; return True iff it passes."""
    if task.grading == "judge":
        return _grade_judge(task, sandbox)
    if task.grading != "tests":
        raise ValueError(f"unknown grading mode: {task.grading!r}")

    env = dict(os.environ)
    bin_dir = Path(sandbox) / "node_modules" / ".bin"
    # Prefer the sandbox's local toolchain (vitest/tsx) so the run stays offline.
    env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
    proc = subprocess.run(
        shlex.split(task.test_cmd),
        cwd=str(sandbox),
        env=env,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0


def _grade_judge(task: Task, sandbox: Path) -> bool:
    # PHASE-FLIP SWAP POINT: LLM-as-judge grading for tasks whose success is not a clean
    # pass/fail test. Unused today — all demo tasks are grading="tests". Left as a seam so
    # the dispatch above is ready; intentionally not implemented (YAGNI).
    raise NotImplementedError(
        "judge grading is not implemented in Phase 3 (all demo tasks use tests)"
    )
