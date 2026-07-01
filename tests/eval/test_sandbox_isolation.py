"""Isolation, determinism, and offline guarantees for the Eval-Runner harness."""

import hashlib
import subprocess
from pathlib import Path

from sprigagent.eval import DEMO_CANDIDATES, evaluate

_CRED_VARS = [
    "GOOGLE_API_KEY",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_GENAI_USE_VERTEXAI",
    "VERTEX_MODEL",
]


def _tree_hash(repo: Path) -> str:
    """Digest every git-tracked file's path + bytes; any mutation changes the result.

    Scoped to ``-- .`` so it inspects only the target subtree: when the target is a vendored
    copy nested inside another git repo (``testbed/sprig-demo``), this ignores the outer repo's
    files. For a standalone repo root the pathspec is the whole repo, so behaviour is unchanged.
    """
    files = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "--", "."],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    h = hashlib.sha256()
    for rel in sorted(files):
        h.update(rel.encode())
        h.update((repo / rel).read_bytes())
    return h.hexdigest()


def test_harness_never_mutates_target_tree(sprig_demo, fixtures_dir):
    before = _tree_hash(sprig_demo)
    for name in ("accept", "reject"):
        evaluate(sprig_demo, DEMO_CANDIDATES[name], fixtures_dir=fixtures_dir)
    assert _tree_hash(sprig_demo) == before, "harness mutated the target tree"
    porcelain = subprocess.run(
        ["git", "-C", str(sprig_demo), "status", "--porcelain", "--", "."],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert porcelain == "", f"target working tree not clean:\n{porcelain}"


def test_results_are_deterministic(sprig_demo, fixtures_dir):
    first = evaluate(sprig_demo, DEMO_CANDIDATES["reject"], fixtures_dir=fixtures_dir)
    second = evaluate(sprig_demo, DEMO_CANDIDATES["reject"], fixtures_dir=fixtures_dir)
    assert first == second


def test_runs_offline_without_credentials(sprig_demo, fixtures_dir, monkeypatch):
    for var in _CRED_VARS:
        monkeypatch.delenv(var, raising=False)
    result = evaluate(sprig_demo, DEMO_CANDIDATES["accept"], fixtures_dir=fixtures_dir)
    assert result.verdict.value == "ACCEPT"
