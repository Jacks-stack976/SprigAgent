"""Loading the frozen task suite from a target repo's `.sprigagent/` tree.

A `Task` is the unit the AgentDriver implements and the grader scores. It mirrors the
on-disk `task.json` contract (id, prompt_file, test_cmd, targets_rule, grading) plus the
loaded agent-facing prompt text. The driver receives a whole `Task` — not a bare prompt —
so the stub can select a fixture by `id`/`targets_rule` and a future real driver gets the
task's metadata (prompt, test command, which rule it exercises) for free.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Task:
    id: str                   # e.g. "001-split-evenly"
    prompt: str               # agent-facing task.md text (no convention, no tests)
    test_cmd: str             # the hidden-test command, run from the repo root
    targets_rule: str | None  # the load-bearing rule the task exercises, or None
    grading: str              # "tests" (primary) | "judge" (seam, unimplemented)


def load_tasks(target_repo: Path) -> list[Task]:
    """Read `.sprigagent/tasks/tasks.json` and hydrate each listed task directory."""
    tasks_root = Path(target_repo) / ".sprigagent" / "tasks"
    index = json.loads((tasks_root / "tasks.json").read_text())
    tasks: list[Task] = []
    for task_id in index["tasks"]:
        tdir = tasks_root / task_id
        meta = json.loads((tdir / "task.json").read_text())
        prompt = (tdir / meta["prompt_file"]).read_text()
        tasks.append(
            Task(
                id=meta["id"],
                prompt=prompt,
                test_cmd=meta["test_cmd"],
                targets_rule=meta.get("targets_rule"),
                grading=meta.get("grading", "tests"),
            )
        )
    return tasks
