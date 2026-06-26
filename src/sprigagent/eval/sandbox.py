"""Throwaway sandboxes so a harness run never touches the real target tree.

Each task in each run gets a fresh copy of the target repo (minus `node_modules`/`.git`),
with `node_modules` symlinked back to the original so tests run fast and fully offline.
The driver's patch is applied INTO the sandbox; the sandbox is graded and then destroyed.
The real repo is only ever read — verified by the sandbox-isolation test.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

# node_modules is symlinked (not copied) for speed; .git is irrelevant to grading.
_IGNORE = shutil.ignore_patterns("node_modules", ".git")


def make_sandbox(target_repo: Path) -> Path:
    """Copy `target_repo` into a fresh temp dir; symlink its node_modules in (read-only use).

    Returns the path to the copied repo root (the cwd that test commands expect).
    """
    target_repo = Path(target_repo)
    holder = Path(tempfile.mkdtemp(prefix="sprigagent-eval-"))
    root = holder / "repo"
    shutil.copytree(target_repo, root, ignore=_IGNORE, symlinks=True)
    node_modules = target_repo / "node_modules"
    if node_modules.exists():
        (root / "node_modules").symlink_to(node_modules.resolve())
    return root


def apply_patch(sandbox: Path, patch: str) -> bool:
    """Apply a unified diff inside the sandbox.

    Returns False (never raises) if the patch does not apply, so a bad patch is scored as a
    task failure rather than crashing the run. `git apply` works on a plain working tree —
    the sandbox is not a git repo — and `-p1` strips the diff's `a/` `b/` prefixes.
    """
    proc = subprocess.run(
        ["git", "apply", "--whitespace=nowarn", "-p1", "-"],
        cwd=str(sandbox),
        input=patch,
        text=True,
        capture_output=True,
    )
    return proc.returncode == 0


def teardown(sandbox: Path) -> None:
    """Remove the sandbox (the temp holder dir that contains the repo copy)."""
    shutil.rmtree(Path(sandbox).parent, ignore_errors=True)
