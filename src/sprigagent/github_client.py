"""The GitHub side-effect seam — an MCP-shaped client with a fake and a live ``gh`` adapter.

The branch-only apply round needs exactly three remote writes: create a branch, put a file on it,
open a PR. Those are isolated behind ``GitHubClient`` so the pure apply logic (``apply.py``) never
imports a network library, the tests run with a recording ``FakeClient``, and the ``--dry-run`` CLI
never constructs anything that touches GitHub.

The interface is deliberately shaped like the official **GitHub MCP** tool surface, so a real
``GithubMcpClient`` drops in behind it later with no change to ``apply.py``:

    create_branch  ↔  GitHub MCP ``create_branch``
    put_file       ↔  GitHub MCP ``create_or_update_file``
    open_pr        ↔  GitHub MCP ``create_pull_request``

Auth never lives here. ``GhCliClient`` shells out to ``gh``, which reads the operator's own
credentials from their environment / keychain. This module never reads, logs, or stores a token —
there is intentionally no reference to a token env var anywhere below.
"""

from __future__ import annotations

import json
import subprocess
from typing import Protocol, runtime_checkable


@runtime_checkable
class GitHubClient(Protocol):
    """The three remote writes branch-only apply needs. Each mirrors a GitHub MCP tool."""

    def create_branch(self, base: str, name: str) -> None:
        """Create branch ``name`` off ``base`` (mirrors MCP ``create_branch``)."""

    def put_file(self, branch: str, path: str, content: str, message: str) -> None:
        """Create/update ``path`` on ``branch`` (mirrors MCP ``create_or_update_file``)."""

    def open_pr(self, base: str, head: str, title: str, body: str) -> str:
        """Open a PR from ``head`` into ``base``; return its URL (mirrors ``create_pull_request``)."""


class FakeClient:
    """Records calls instead of performing them — for tests and any offline rehearsal.

    Does no I/O and needs no token. Tests assert ``.calls`` (an ordered ``(method, kwargs)`` log)
    to prove the branch-only sequence and that writes target the head branch, never the base.
    """

    open_pr_url = "https://github.com/example/repo/pull/1"  # the canned URL open_pr returns

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def create_branch(self, base: str, name: str) -> None:
        self.calls.append(("create_branch", {"base": base, "name": name}))

    def put_file(self, branch: str, path: str, content: str, message: str) -> None:
        self.calls.append(
            ("put_file", {"branch": branch, "path": path, "content": content, "message": message})
        )

    def open_pr(self, base: str, head: str, title: str, body: str) -> str:
        self.calls.append(("open_pr", {"base": base, "head": head, "title": title, "body": body}))
        return self.open_pr_url


class GhCliClient:
    """Live adapter: performs the three writes via the ``gh`` CLI (operator's own auth).

    Live-only — exercised by the manual ``--execute`` path against a throwaway repo, not by the
    offline test suite. Auth is entirely ``gh``'s: this class never sees, reads, or logs a token.
    ``repo`` is ``owner/name`` (or ``None`` to use the current checkout's remote).
    """

    def __init__(self, repo: str | None = None) -> None:
        self._repo = repo

    # -- small gh helpers ---------------------------------------------------
    def _gh(self, *args: str, capture: bool = True) -> str:
        """Run ``gh <args>`` and return stdout. Auth is gh's; we never pass a token."""
        proc = subprocess.run(
            ["gh", *args], check=True, text=True,
            capture_output=capture,
        )
        return (proc.stdout or "").strip()

    def _api(self, *args: str) -> str:
        base = ["api"]
        if self._repo:
            # gh api templating: {owner}/{repo} resolve from -R when provided.
            base += ["-H", "Accept: application/vnd.github+json"]
        return self._gh(*base, *args)

    def _repo_path(self, suffix: str) -> str:
        return f"repos/{self._repo}/{suffix}" if self._repo else f"repos/{{owner}}/{{repo}}/{suffix}"

    # -- the seam -----------------------------------------------------------
    def create_branch(self, base: str, name: str) -> None:
        sha = self._api(self._repo_path(f"git/ref/heads/{base}"), "--jq", ".object.sha")
        self._api(
            "--method", "POST", self._repo_path("git/refs"),
            "-f", f"ref=refs/heads/{name}", "-f", f"sha={sha}",
        )

    def put_file(self, branch: str, path: str, content: str, message: str) -> None:
        import base64

        b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
        fields = [
            "--method", "PUT", self._repo_path(f"contents/{path}"),
            "-f", f"message={message}", "-f", f"content={b64}", "-f", f"branch={branch}",
        ]
        # The Contents API needs the current blob sha to UPDATE an existing file; omit it to create.
        sha = self._existing_sha(path, branch)
        if sha:
            fields += ["-f", f"sha={sha}"]
        self._api(*fields)

    def _existing_sha(self, path: str, branch: str) -> str | None:
        try:
            return self._api(self._repo_path(f"contents/{path}"), "-f", f"ref={branch}", "--jq", ".sha") or None
        except subprocess.CalledProcessError:
            return None  # 404 -> the file does not exist yet on this branch

    def open_pr(self, base: str, head: str, title: str, body: str) -> str:
        args = ["pr", "create", "--base", base, "--head", head, "--title", title, "--body", body]
        if self._repo:
            args += ["-R", self._repo]
        return self._gh(*args)


__all__ = ["GitHubClient", "FakeClient", "GhCliClient"]
