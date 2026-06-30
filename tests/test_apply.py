"""Tests for the branch-only apply round — pure, offline, no GitHub, no token.

The apply logic is a pure function of (approved.json, context-file text, injected timestamp): it
computes the pruned file content, the quarantine artifact, and the PR title/body. The GitHub side
effects live behind an MCP-shaped client seam so tests use a ``FakeClient`` and the ``--dry-run``
CLI never constructs the live ``gh`` adapter. Every test here runs with no network and no token.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from sprigagent.apply import ApplyMismatch, apply_plan, build_plan, main
from sprigagent.github_client import FakeClient

# ---------------------------------------------------------------------------
# Fixtures: a CLAUDE.md-like file + a constructed approved.json (no orchestrate, no testbed)
# ---------------------------------------------------------------------------
SAMPLE_FILE = (
    "# Project\n"
    "\n"
    "## Keep me\n"
    "- important rule\n"
    "\n"
    "## Code style\n"
    "- Use 2-space indentation\n"
    "- Max line length 100\n"
    "- Prefer single quotes\n"
    "\n"
    "## Also keep\n"
    "- another rule\n"
)

STYLE_REMOVED = [
    "## Code style",
    "- Use 2-space indentation",
    "- Max line length 100",
    "- Prefer single quotes",
]


def _item(**over):
    item = {
        "id": "## Code style",
        "heading": "## Code style",
        "verdict": "ACCEPT",
        "success_before": 1.0,
        "success_after": 1.0,
        "token_before": 631,
        "token_after": 411,
        "token_delta_pct": -34.9,
        "removed": list(STYLE_REMOVED),
    }
    item.update(over)
    return item


def _approved(repo, *, approved=None, declined=None, total=220):
    return {
        "repo": str(repo),
        "file": "CLAUDE.md",
        "source": "StubDriver · char-estimate (~chars/4)",
        "approved": [_item()] if approved is None else approved,
        "declined": declined or [],
        "total_token_reduction": total,
    }


def _plan(repo="/tmp/sprig-demo", **kw):
    return build_plan(_approved(repo, **kw), SAMPLE_FILE, timestamp="20260630-212345", base="main")


# ---------------------------------------------------------------------------
# 1. build_plan removes exactly the approved (contiguous) lines; survivors byte-for-byte
# ---------------------------------------------------------------------------
def test_build_plan_removes_exactly_the_approved_block():
    plan = _plan()
    assert "## Code style" not in plan.new_file_text
    for bullet in STYLE_REMOVED[1:]:
        assert bullet not in plan.new_file_text
    # Everything outside the approved block survives, byte-for-byte.
    assert "# Project\n" in plan.new_file_text
    assert "## Keep me\n- important rule\n" in plan.new_file_text
    assert "## Also keep\n- another rule\n" in plan.new_file_text
    # No other lines were touched: the survivors are exactly the original minus the 4 removed.
    original = SAMPLE_FILE.splitlines(keepends=True)
    expected = "".join(ln for ln in original if ln.rstrip("\n") not in STYLE_REMOVED)
    assert plan.new_file_text == expected


def test_declined_lines_are_untouched():
    # "## Also keep" is declined (only "## Code style" is in approved) -> it must remain.
    plan = _plan(declined=["## Also keep"])
    assert "## Also keep" in plan.new_file_text
    assert "- another rule" in plan.new_file_text


# ---------------------------------------------------------------------------
# 2. Scattered / multi-line removed -> ordered-subsequence match
# ---------------------------------------------------------------------------
def test_build_plan_handles_scattered_removed_lines():
    scattered = ["- Use 2-space indentation", "- Prefer single quotes"]  # non-adjacent
    plan = _plan(approved=[_item(removed=scattered)])
    assert "- Use 2-space indentation" not in plan.new_file_text
    assert "- Prefer single quotes" not in plan.new_file_text
    # The line between them is NOT in the removed set -> it survives.
    assert "- Max line length 100" in plan.new_file_text
    assert "## Code style" in plan.new_file_text  # heading not in removed -> stays


# ---------------------------------------------------------------------------
# 3. Quarantine artifact: every removed line verbatim + heading + proven numbers
# ---------------------------------------------------------------------------
def test_quarantine_contains_every_removed_line_and_numbers():
    plan = _plan()
    q = plan.quarantine_text
    for line in STYLE_REMOVED:
        assert line in q                       # every removed line, verbatim
    assert "## Code style" in q                # the heading
    assert "ACCEPT" in q                       # the verdict
    assert "631" in q and "411" in q           # tokens before/after
    assert "-34.9" in q                        # the delta
    assert plan.quarantine_path == ".sprigagent/quarantine/CLAUDE.md.20260630-212345.md"


def test_quarantine_fence_survives_backticks_in_content():
    # A removed line containing a ``` fence must still be recoverable (longer outer fence).
    fenced = _item(removed=["## Code style", "- run ```npm test``` first"])
    plan = build_plan(
        _approved("/tmp/x", approved=[fenced]),
        "## Code style\n- run ```npm test``` first\n",
        timestamp="20260630-212345",
    )
    assert "- run ```npm test``` first" in plan.quarantine_text
    assert "````" in plan.quarantine_text       # outer fence is longer than the inner ```


# ---------------------------------------------------------------------------
# 4. PR body lists the approved prunes + total savings + the quarantine path
# ---------------------------------------------------------------------------
def test_pr_body_lists_prunes_total_and_quarantine_path():
    plan = _plan()
    body = plan.pr_body
    assert "## Code style" in body             # the pruned section
    assert "ACCEPT" in body                     # its verdict
    assert "631" in body and "411" in body      # before/after tokens
    assert "220" in body                        # total_token_reduction
    assert plan.quarantine_path in body         # points at the quarantine artifact
    # The safety story is in the PR body.
    assert "branch" in body.lower() and "never" in body.lower()
    assert "quarantine" in body.lower()
    # The title carries the file + the savings.
    assert "CLAUDE.md" in plan.pr_title and "220" in plan.pr_title


# ---------------------------------------------------------------------------
# 5. Mismatch safety — an absent removed block fails loud, never garbles the file
# ---------------------------------------------------------------------------
def test_absent_removed_block_raises_apply_mismatch():
    ghost = _item(removed=["- this line is not anywhere in the file"])
    with pytest.raises(ApplyMismatch):
        build_plan(_approved("/tmp/x", approved=[ghost]), SAMPLE_FILE, timestamp="t")


# ---------------------------------------------------------------------------
# 6. Empty approved set -> clean message, no client, no PR
# ---------------------------------------------------------------------------
def test_empty_approved_set_attempts_no_pr(tmp_path, monkeypatch, capsys):
    import sprigagent.github_client as gc

    def _boom(*a, **k):  # constructing the live client in this path is a bug
        raise AssertionError("GhCliClient must not be constructed for an empty approved set")

    monkeypatch.setattr(gc, "GhCliClient", _boom)
    (tmp_path / "CLAUDE.md").write_text(SAMPLE_FILE)
    aj = tmp_path / "approved.json"
    aj.write_text(json.dumps(_approved(tmp_path, approved=[], total=0)))

    rc = main([str(aj), "--execute"])  # even with --execute, an empty set does nothing
    assert rc != 0
    assert "nothing to apply" in capsys.readouterr().out.lower()


# ---------------------------------------------------------------------------
# 7. apply_plan drives the seam in order; branch-only (head=branch, base=default)
# ---------------------------------------------------------------------------
def test_apply_plan_calls_the_seam_in_order_branch_only():
    plan = _plan()
    client = FakeClient()
    url = apply_plan(plan, client)

    methods = [name for name, _ in client.calls]
    assert methods == ["create_branch", "put_file", "put_file", "open_pr"]

    branch = plan.branch
    assert branch.startswith("sprigagent/prune-")
    # create_branch is cut FROM the default base.
    assert client.calls[0][1] == {"base": "main", "name": branch}
    # both file writes target the new branch, never the base.
    for name, kw in client.calls[1:3]:
        assert kw["branch"] == branch and kw["branch"] != "main"
    paths = {kw["path"] for _, kw in client.calls[1:3]}
    assert plan.file_path in paths and plan.quarantine_path in paths
    # the PR points head=branch at base=default; never the other way, never auto-merge.
    _, pr = client.calls[3]
    assert pr["base"] == "main" and pr["head"] == branch
    assert url == client.open_pr_url


# ---------------------------------------------------------------------------
# 8. Dry-run prints the full plan and constructs NO live client
# ---------------------------------------------------------------------------
def test_dry_run_prints_plan_and_makes_no_live_call(tmp_path, monkeypatch, capsys):
    import sprigagent.github_client as gc

    def _boom(*a, **k):
        raise AssertionError("dry-run must not construct the live GhCliClient")

    monkeypatch.setattr(gc, "GhCliClient", _boom)
    (tmp_path / "CLAUDE.md").write_text(SAMPLE_FILE)
    aj = tmp_path / "approved.json"
    aj.write_text(json.dumps(_approved(tmp_path)))

    rc = main([str(aj), "--dry-run"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "sprigagent/prune-" in out          # the branch name
    assert ".sprigagent/quarantine/CLAUDE.md" in out  # the quarantine artifact path
    assert "## Code style" in out              # the pruned section appears in the plan
    assert "220" in out                        # the total savings in the PR body


def test_default_is_dry_run(tmp_path, monkeypatch):
    import sprigagent.github_client as gc

    monkeypatch.setattr(gc, "GhCliClient", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("no --execute -> must default to dry-run, no live client")))
    (tmp_path / "CLAUDE.md").write_text(SAMPLE_FILE)
    aj = tmp_path / "approved.json"
    aj.write_text(json.dumps(_approved(tmp_path)))
    assert main([str(aj)]) == 0  # no flags == dry-run


# ---------------------------------------------------------------------------
# 9. Token hygiene — nothing the apply produces, and no code path, handles a raw token
# ---------------------------------------------------------------------------
def test_generated_artifacts_carry_no_secret():
    plan = _plan()
    blob = "\n".join([plan.pr_title, plan.pr_body, plan.quarantine_text, plan.new_file_text])
    assert not re.search(r"gh[pousr]_[A-Za-z0-9]{20,}", blob)  # no GitHub token literal
    assert "GITHUB_TOKEN" not in blob and "GH_TOKEN" not in blob


def test_apply_code_never_reads_a_token_env_var():
    # Auth is gh's job (Jack's env); our code must never read/echo a raw token.
    src = Path(__file__).resolve().parents[1] / "src" / "sprigagent"
    for mod in ("apply.py", "github_client.py"):
        text = (src / mod).read_text()
        assert "GITHUB_TOKEN" not in text
        assert "GH_TOKEN" not in text
