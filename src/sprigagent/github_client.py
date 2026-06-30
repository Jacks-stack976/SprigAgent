"""The GitHub side-effect seam — an MCP-shaped client with a fake and a live ``gh`` adapter.

The branch-only apply round needs exactly three remote writes: create a branch, put a file on it,
open a PR. Those are isolated behind ``GitHubClient`` so the pure apply logic (``apply.py``) never
imports a network library, the tests run with a recording ``FakeClient``, and the ``--dry-run`` CLI
never constructs anything that touches GitHub.

Three implementations share the interface:

    FakeClient       — records calls, no I/O (tests / dry-run rehearsal)
    GhCliClient      — live, shells out to ``gh`` (the default fallback)
    GithubMcpClient  — live, calls GitHub tools **through the Model Context Protocol** (interop)

The interface is deliberately shaped like the official **GitHub MCP** tool surface, so each method
maps 1:1 onto a tool ``GithubMcpClient`` calls over MCP:

    create_branch  ↔  GitHub MCP ``create_branch``
    put_file       ↔  GitHub MCP ``create_or_update_file``  (+ ``get_file_contents`` for the sha)
    open_pr        ↔  GitHub MCP ``create_pull_request``

Auth never lives here. ``GhCliClient`` shells out to ``gh``; ``GithubMcpClient`` forwards the parent
environment to the MCP server, which reads its *own* credentials. This module never reads, logs, or
stores a token — there is intentionally no reference to a token env var anywhere below.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shlex
import subprocess
from types import SimpleNamespace
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


# ---------------------------------------------------------------------------
# GithubMcpClient — open the PR by calling GitHub tools through the Model Context Protocol.
# ---------------------------------------------------------------------------
def _result_text(result) -> str:
    """Concatenate the text of every content block in an MCP ``CallToolResult`` (or fake)."""
    return "".join(getattr(b, "text", "") or "" for b in (getattr(result, "content", None) or []))


def _result_json(result) -> dict:
    try:
        data = json.loads(_result_text(result))
    except (ValueError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def _parse_pr_url(result) -> str:
    """Pull the PR URL out of a ``create_pull_request`` result (html_url, then a tolerant fallback)."""
    data = _result_json(result)
    url = data.get("html_url") or data.get("url")
    if url:
        return url
    m = re.search(r"https://github\.com/[^\s\"']+/pull/\d+", _result_text(result))
    return m.group(0) if m else _result_text(result).strip()


class GithubMcpClient:
    """Implements ``GitHubClient`` by calling GitHub tools over MCP — the interoperability path.

    A **pure mapping** over an injected ``session`` (anything with ``call_tool(name, arguments) ->
    result``): the unit tests inject a ``FakeMcpSession``; the live ``connect`` wires a real MCP
    ``ClientSession`` over stdio. Tool/arg names follow the ``@modelcontextprotocol/server-github``
    schema and are class constants, so pointing at a different server is a one-line change.
    """

    CREATE_BRANCH = "create_branch"
    PUT_FILE = "create_or_update_file"
    OPEN_PR = "create_pull_request"
    GET_CONTENTS = "get_file_contents"

    def __init__(self, session, repo: str) -> None:
        if "/" not in repo:
            raise ValueError(f"GithubMcpClient needs repo as 'owner/name', got {repo!r}")
        self._session = session
        self._owner, self._repo = repo.split("/", 1)

    def create_branch(self, base: str, name: str) -> None:
        self._session.call_tool(self.CREATE_BRANCH, {
            "owner": self._owner, "repo": self._repo, "branch": name, "from_branch": base,
        })

    def put_file(self, branch: str, path: str, content: str, message: str) -> None:
        args = {
            "owner": self._owner, "repo": self._repo, "path": path,
            "content": content, "message": message, "branch": branch,
        }
        sha = self._existing_sha(path, branch)  # required to UPDATE an existing file; omit to create
        if sha:
            args["sha"] = sha
        self._session.call_tool(self.PUT_FILE, args)

    def open_pr(self, base: str, head: str, title: str, body: str) -> str:
        result = self._session.call_tool(self.OPEN_PR, {
            "owner": self._owner, "repo": self._repo,
            "title": title, "body": body, "head": head, "base": base,
        })
        return _parse_pr_url(result)

    def _existing_sha(self, path: str, branch: str) -> str | None:
        try:
            result = self._session.call_tool(self.GET_CONTENTS, {
                "owner": self._owner, "repo": self._repo, "path": path, "branch": branch,
            })
        except Exception:
            return None  # tool unavailable / transport error -> treat as a new file
        if getattr(result, "isError", False):
            return None  # 404 -> the file does not exist on this branch yet
        return _result_json(result).get("sha") or None

    def close(self) -> None:
        close = getattr(self._session, "close", None)
        if close is not None:
            close()

    @classmethod
    def connect(cls, repo: str, *, server_command, env=None) -> "GithubMcpClient":
        """Wire a live client to a GitHub MCP server launched via ``server_command`` (str or argv)."""
        return cls(_OneShotStdioSession(server_command, env=env), repo)


class _OneShotStdioSession:
    """Live MCP session over stdio. Each ``call_tool`` is a one-shot: launch the server, handshake,
    call one tool, tear down. GitHub state persists server-side between calls, so independent
    sessions compose correctly — and there is no background loop / long-lived session to leak.

    ``mcp`` is imported **lazily** inside the call so this module loads with no ``mcp`` installed
    (the offline suite never touches this path). The parent environment is forwarded wholesale so
    the server reads its own credentials; this class never names or inspects a token.
    """

    def __init__(self, server_command, *, env=None) -> None:
        self._argv = list(server_command) if isinstance(server_command, (list, tuple)) else shlex.split(server_command)
        self._env = dict(env) if env is not None else dict(os.environ)

    def call_tool(self, name: str, arguments: dict):
        return asyncio.run(self._call(name, arguments))

    async def _call(self, name: str, arguments: dict):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(command=self._argv[0], args=self._argv[1:], env=self._env)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await session.call_tool(name, arguments)

    def close(self) -> None:
        pass  # one-shot: nothing persistent to close


class FakeMcpSession:
    """Offline stand-in for an MCP ``ClientSession`` — records calls, returns canned results.

    No ``mcp`` import, no I/O, no token. ``existing`` maps already-present file paths to a sha (so
    ``get_file_contents`` returns one for them and a not-found error otherwise); ``create_pull_request``
    returns a result carrying ``pr_url``.
    """

    def __init__(self, *, existing=None, pr_url="https://github.com/octo/demo/pull/42") -> None:
        self.calls: list[tuple[str, dict]] = []
        self._existing = dict(existing or {})
        self._pr_url = pr_url

    def call_tool(self, name: str, arguments: dict):
        self.calls.append((name, dict(arguments)))
        if name == GithubMcpClient.GET_CONTENTS:
            path = arguments.get("path")
            if path in self._existing:
                return _fake_result(json.dumps({"sha": self._existing[path], "path": path}))
            return _fake_result(json.dumps({"message": "Not Found"}), is_error=True)
        if name == GithubMcpClient.OPEN_PR:
            return _fake_result(json.dumps({"html_url": self._pr_url, "number": 42}))
        return _fake_result(json.dumps({"ok": True}))

    def close(self) -> None:
        pass


def _fake_result(text: str, *, is_error: bool = False):
    return SimpleNamespace(content=[SimpleNamespace(text=text)], isError=is_error)


__all__ = ["GitHubClient", "FakeClient", "GhCliClient", "GithubMcpClient", "FakeMcpSession"]
