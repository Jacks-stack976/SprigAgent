"""Tests for the real GitHub MCP client — pure, offline, no live server, no token.

``GithubMcpClient`` is a pure mapping from the ``GitHubClient`` Protocol onto GitHub MCP tool calls,
driven through an injected session. These tests use a ``FakeMcpSession`` (records calls, returns
canned tool results) so the three-tool branch-only flow, the CLI ``--client`` selection, and token
hygiene are all verified with no ``mcp`` install, no network, and no token. The live MCP PR is Jack's
manual step (needs the running server + his token), exactly like the gh live PR.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sprigagent.apply import apply_plan, build_plan, main
from sprigagent.github_client import FakeMcpSession, GitHubClient, GithubMcpClient

# ---------------------------------------------------------------------------
# Fixtures — a small context file + a one-item approved set (reuses build_plan)
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
    "\n"
    "## Also keep\n"
    "- another rule\n"
)
STYLE_REMOVED = ["## Code style", "- Use 2-space indentation", "- Max line length 100"]


def _approved(repo="/tmp/demo"):
    return {
        "repo": str(repo),
        "file": "CLAUDE.md",
        "source": "StubDriver · char-estimate (~chars/4)",
        "approved": [{
            "id": "## Code style", "heading": "## Code style", "verdict": "ACCEPT",
            "success_before": 1.0, "success_after": 1.0,
            "token_before": 631, "token_after": 411, "token_delta_pct": -34.9,
            "removed": list(STYLE_REMOVED),
        }],
        "declined": [], "total_token_reduction": 220,
    }


def _plan(repo="/tmp/demo"):
    return build_plan(_approved(repo), SAMPLE_FILE, timestamp="20260630-220000", base="main")


class _StubClient:
    """A minimal GitHubClient the CLI-selection tests get back from the patched constructors."""

    def __init__(self):
        self.calls = []

    def create_branch(self, base, name):
        self.calls.append(("create_branch", base, name))

    def put_file(self, branch, path, content, message):
        self.calls.append(("put_file", branch, path))

    def open_pr(self, base, head, title, body):
        self.calls.append(("open_pr", base, head))
        return "https://github.com/octo/demo/pull/99"

    def close(self):
        self.calls.append(("close",))


# ---------------------------------------------------------------------------
# 1. End-to-end over a fake MCP session: the three tools, in order, right args, URL parsed
# ---------------------------------------------------------------------------
def test_mcp_client_drives_tools_in_order_and_parses_url():
    plan = _plan()
    sess = FakeMcpSession(existing={plan.file_path: "shaCLAUDE"})  # CLAUDE.md already exists -> sha
    client = GithubMcpClient(sess, repo="octo/demo")

    url = apply_plan(plan, client)

    names = [n for n, _ in sess.calls]
    core = [n for n in names if n in ("create_branch", "create_or_update_file", "create_pull_request")]
    assert core == ["create_branch", "create_or_update_file", "create_or_update_file", "create_pull_request"]

    by: dict[str, list[dict]] = {}
    for n, a in sess.calls:
        by.setdefault(n, []).append(a)

    # create_branch is cut FROM base, naming the head branch.
    assert by["create_branch"][0] == {
        "owner": "octo", "repo": "demo", "branch": plan.branch, "from_branch": "main",
    }

    writes = by["create_or_update_file"]
    assert {w["path"] for w in writes} == {plan.file_path, plan.quarantine_path}
    for w in writes:
        assert w["owner"] == "octo" and w["repo"] == "demo"
        assert w["branch"] == plan.branch and w["branch"] != "main"   # head branch, never base
        assert w["content"] and w["message"]
    ctx = next(w for w in writes if w["path"] == plan.file_path)
    quar = next(w for w in writes if w["path"] == plan.quarantine_path)
    assert ctx.get("sha") == "shaCLAUDE"               # existing file updated WITH its sha
    assert not quar.get("sha")                          # brand-new file created, no sha

    pr = by["create_pull_request"][0]
    assert pr["owner"] == "octo" and pr["repo"] == "demo"
    assert pr["head"] == plan.branch and pr["base"] == "main"   # head -> base, never reversed
    assert pr["title"] and pr["body"]
    assert url == "https://github.com/octo/demo/pull/42"        # parsed from the tool result


def test_mcp_client_satisfies_the_protocol():
    client = GithubMcpClient(FakeMcpSession(), repo="octo/demo")
    assert isinstance(client, GitHubClient)


def test_mcp_client_requires_owner_slash_name():
    with pytest.raises(ValueError):
        GithubMcpClient(FakeMcpSession(), repo="just-a-name")


# ---------------------------------------------------------------------------
# 2. CLI --client selection (default gh) — asserted with no live call
# ---------------------------------------------------------------------------
def _write_inputs(tmp_path):
    (tmp_path / "CLAUDE.md").write_text(SAMPLE_FILE)
    aj = tmp_path / "approved.json"
    aj.write_text(json.dumps(_approved(tmp_path)))
    return aj


def test_cli_client_selection(tmp_path, monkeypatch):
    import sprigagent.github_client as gc

    aj = _write_inputs(tmp_path)
    chosen: list[str] = []

    def fake_gh(**kw):
        chosen.append("gh")
        return _StubClient()

    def fake_connect(repo, **kw):
        chosen.append("mcp")
        return _StubClient()

    monkeypatch.setattr(gc, "GhCliClient", fake_gh)
    monkeypatch.setattr(gc.GithubMcpClient, "connect", staticmethod(fake_connect))

    assert main([str(aj), "--execute", "--repo", "octo/demo"]) == 0          # default -> gh
    assert chosen == ["gh"]
    chosen.clear()

    assert main([str(aj), "--execute", "--client", "mcp", "--repo", "octo/demo"]) == 0
    assert chosen == ["mcp"]
    chosen.clear()

    assert main([str(aj), "--execute", "--client", "gh", "--repo", "octo/demo"]) == 0
    assert chosen == ["gh"]


def test_cli_client_mcp_requires_repo(tmp_path, monkeypatch, capsys):
    import sprigagent.github_client as gc

    monkeypatch.setattr(gc.GithubMcpClient, "connect",
                        staticmethod(lambda *a, **k: pytest.fail("must not connect without --repo")))
    aj = _write_inputs(tmp_path)
    rc = main([str(aj), "--execute", "--client", "mcp"])   # no --repo
    assert rc != 0
    assert "repo" in capsys.readouterr().out.lower()


# ---------------------------------------------------------------------------
# 3. Token hygiene — the module names no token env var
# ---------------------------------------------------------------------------
def test_module_references_no_token_env_var():
    import sprigagent.github_client as gc

    src = Path(gc.__file__).read_text()
    for tok in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PERSONAL_ACCESS_TOKEN"):
        assert tok not in src


# ---------------------------------------------------------------------------
# 4. Dry-run with --client mcp still constructs no client / makes no call
# ---------------------------------------------------------------------------
def test_dry_run_with_client_mcp_makes_no_call(tmp_path, monkeypatch, capsys):
    import sprigagent.github_client as gc

    monkeypatch.setattr(gc.GithubMcpClient, "connect",
                        staticmethod(lambda *a, **k: pytest.fail("dry-run must not open a live MCP session")))
    monkeypatch.setattr(gc, "GhCliClient",
                        lambda **k: pytest.fail("dry-run must construct no client"))
    aj = _write_inputs(tmp_path)
    rc = main([str(aj), "--dry-run", "--client", "mcp", "--repo", "octo/demo"])
    assert rc == 0
    assert "sprigagent/prune-" in capsys.readouterr().out
