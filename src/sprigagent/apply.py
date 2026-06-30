"""Branch-only apply — turn an approved ``approved.json`` into a safe, branch-scoped PR.

This is the round that *acts on* the human gate. The Approval UI already wrote ``approved.json``
(``ui/app.py``); this component reads that approved set and, through the MCP-shaped
``github_client`` seam, opens a **branch-only** pull request that applies the approved prunes while
**quarantining** every removed line. It never re-discovers and never re-proves — ``approved.json``
is the gate and the only input.

Four safety rules are load-bearing here:

  * **Branch-only, never main.** A new ``sprigagent/prune-<ts>`` branch is created off the default
    branch; the PR targets the default branch for a human to merge. Nothing is pushed to or merged
    into the default branch; nothing auto-merges.
  * **Quarantine, never delete.** Removed lines are written verbatim to a recoverable artifact on
    the same branch (``.sprigagent/quarantine/<file>.<ts>.md``) and listed in the PR body.
  * **Auth stays the operator's.** The live path shells out to ``gh`` (see ``github_client``); this
    module never reads, logs, or commits a token.
  * **Acts only on the approved set.** Declined / gave-up items are not in ``approved.json``'s
    approved list, so they are never touched.

The plan-building logic (``build_plan``) is a **pure** function of ``(approved, file_text,
timestamp)`` — no clock, no network, no token — so it is trivially testable. The CLI defaults to
``--dry-run`` (prints the would-be branch, never touches GitHub); the live PR requires an explicit
``--execute``.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sprigagent import github_client

# Where quarantined lines land on the branch (per-file, per-run, recoverable).
QUARANTINE_DIR = ".sprigagent/quarantine"
BRANCH_PREFIX = "sprigagent/prune-"
DEFAULT_BASE = "main"


class ApplyMismatch(Exception):
    """An approved ``removed`` block could not be located in the context file.

    Raised instead of producing a partially-applied or garbled file — the never-delete /
    never-corrupt posture. The operator re-runs the approval flow against the current file.
    """


@dataclass(frozen=True)
class BranchPlan:
    """Everything needed to open the branch-only PR — fully computed, side-effect free.

    Produced by ``build_plan`` and consumed by ``apply_plan`` (which feeds it to the client seam)
    or printed verbatim by ``--dry-run``. Holds no token and no network handle.
    """

    branch: str            # the new branch (sprigagent/prune-<ts>) — the PR head
    base: str              # the default branch the PR targets — never written to
    file_path: str         # the pruned context file (repo-relative), e.g. "CLAUDE.md"
    new_file_text: str     # the context file with exactly the approved lines removed
    quarantine_path: str   # repo-relative path of the quarantine artifact on the branch
    quarantine_text: str   # the recoverable record of every removed block + its proven numbers
    pr_title: str          # the PR title (file + measured savings)
    pr_body: str           # the PR body (approved prunes table + savings + safety story)
    commit_message: str    # the commit message used for both file writes


# ---------------------------------------------------------------------------
# Removal: locate each approved block in the file and drop exactly those lines.
# ---------------------------------------------------------------------------
def _match_block(stripped: list[str], removed: list[str], claimed: set[int]) -> list[int] | None:
    """Indices in ``stripped`` matching ``removed``, skipping already-``claimed`` lines.

    Tries a **contiguous block** first (the common case — a whole-section strip or a contiguous
    trim), then an **ordered subsequence** (scattered line-trims). Returns ``None`` when the block
    cannot be fully located, so the caller can fail loud rather than corrupt the file.
    """
    n, m = len(stripped), len(removed)
    if m == 0:
        return []

    # Contiguous run: stripped[start : start+m] == removed, with no claimed line inside.
    for start in range(0, n - m + 1):
        window = range(start, start + m)
        if any(i in claimed for i in window):
            continue
        if all(stripped[start + k] == removed[k] for k in range(m)):
            return list(window)

    # Ordered subsequence: match each removed line at or after the previous match.
    idxs: list[int] = []
    cursor = 0
    for line in removed:
        hit = next((i for i in range(cursor, n) if i not in claimed and stripped[i] == line), None)
        if hit is None:
            return None
        idxs.append(hit)
        cursor = hit + 1
    return idxs


def _apply_removals(file_text: str, items: list[dict]) -> str:
    """Return ``file_text`` with every approved item's ``removed`` lines dropped (survivors intact).

    Lines are compared on their newline-stripped form (mirroring how ``rewrite`` quarantines them).
    Any block that cannot be located — or that would overlap another — raises ``ApplyMismatch``.
    """
    lines = file_text.splitlines(keepends=True)
    stripped = [ln.rstrip("\n") for ln in lines]
    claimed: set[int] = set()
    for item in items:
        removed = [r.rstrip("\n") for r in item.get("removed", [])]
        if not removed:
            continue
        idxs = _match_block(stripped, removed, claimed)
        if idxs is None:
            raise ApplyMismatch(
                f"could not locate the approved removed block for {item.get('heading', item.get('id'))!r} "
                f"in the current file — refusing to apply a partial/garbled edit."
            )
        claimed.update(idxs)
    return "".join(ln for i, ln in enumerate(lines) if i not in claimed)


# ---------------------------------------------------------------------------
# Quarantine + PR text (pure formatting).
# ---------------------------------------------------------------------------
def _fence_for(content: str) -> str:
    """A backtick fence longer than any backtick run in ``content`` (≥3) — so fenced content that
    itself contains ``` stays recoverable."""
    longest = max((len(m) for m in re.findall(r"`+", content)), default=0)
    return "`" * max(3, longest + 1)


def _pct(value: float) -> str:
    return f"{value:.0%}"


def _block_numbers(item: dict) -> str:
    return (
        f"- id: {item['id']}\n"
        f"- verdict: {item['verdict']}\n"
        f"- success: {_pct(item['success_before'])} → {_pct(item['success_after'])}\n"
        f"- tokens: {item['token_before']} → {item['token_after']} ({item['token_delta_pct']:+.1f}%)\n"
    )


def _build_quarantine(approved: dict, timestamp: str) -> str:
    """The recoverable record: every removed block, verbatim, with its proven numbers."""
    file = approved["file"]
    parts = [
        f"# SprigAgent quarantine — {file} @ {timestamp}\n",
        "",
        "These lines were removed by **approved** prunes and are preserved here verbatim.",
        "Nothing is destroyed — every block below is fully recoverable.",
        "",
    ]
    for item in approved["approved"]:
        body = "\n".join(item.get("removed", []))
        fence = _fence_for(body)
        # The heading may already be a markdown heading ("## Code style") or a locator ("L12");
        # only add a level when it is not already one, so the artifact never shows "## ## …".
        heading = item["heading"]
        block_header = heading if heading.lstrip().startswith("#") else f"## {heading}"
        parts += [
            block_header,
            "",
            _block_numbers(item).rstrip("\n"),
            "",
            f"Removed lines ({len(item.get('removed', []))}):",
            fence,
            body,
            fence,
            "",
        ]
    return "\n".join(parts).rstrip("\n") + "\n"


def _build_pr_title(approved: dict) -> str:
    n = approved["total_token_reduction"]
    m = len(approved["approved"])
    return f"SprigAgent: prune {approved['file']} (-{n} tokens, {m} approved prune(s))"


def _build_pr_body(approved: dict, quarantine_path: str, base: str) -> str:
    file = approved["file"]
    m = len(approved["approved"])
    n = approved["total_token_reduction"]
    rows = "\n".join(
        f"| `{it['heading']}` | {it['verdict']} | {_pct(it['success_before'])} → {_pct(it['success_after'])} "
        f"| {it['token_before']} → {it['token_after']} | {it['token_delta_pct']:+.1f}% |"
        for it in approved["approved"]
    )
    return (
        f"SprigAgent applied **{m}** human-approved prune(s) to `{file}` on this branch.\n\n"
        "A human reviewed and **approved** each of these in the SprigAgent Approval UI; this PR "
        "applies exactly that approved set, on a branch, for you to merge.\n\n"
        "## Approved prunes\n\n"
        "| Section | Verdict | Success (before → after) | Tokens (before → after) | Δ |\n"
        "|---|---|---|---|---|\n"
        f"{rows}\n\n"
        f"**Total token reduction: {n}** across {m} approved prune(s).\n\n"
        "## Quarantine (never-delete)\n\n"
        f"Every removed line is preserved verbatim in `{quarantine_path}` on this branch — "
        "recoverable, not destroyed.\n\n"
        "## Safety\n\n"
        f"- **Branch-only:** this PR targets `{base}`; it never pushes to or merges the default "
        "branch, and never auto-merges.\n"
        "- **Prune-only / never-delete:** removed lines are quarantined, not deleted.\n"
        "- **Acts only on the approved set:** declined and gave-up items are not included.\n"
        "- **Auth stays yours:** opened with your own GitHub credentials; no token is stored in "
        "this repo or PR.\n"
    )


# ---------------------------------------------------------------------------
# build_plan — the pure entry point.
# ---------------------------------------------------------------------------
def build_plan(approved: dict, file_text: str, *, timestamp: str, base: str = DEFAULT_BASE) -> BranchPlan:
    """Compute the full branch-only plan from the approved set + the current file text.

    Pure and deterministic: ``timestamp`` is injected (no clock), no network, no token. Raises
    ``ApplyMismatch`` if any approved block cannot be located in ``file_text`` (fail loud rather
    than corrupt). Declined / gave-up items are not in ``approved['approved']`` and are untouched.
    """
    file = approved["file"]
    new_file_text = _apply_removals(file_text, approved["approved"])
    quarantine_path = f"{QUARANTINE_DIR}/{file}.{timestamp}.md"
    quarantine_text = _build_quarantine(approved, timestamp)
    return BranchPlan(
        branch=f"{BRANCH_PREFIX}{timestamp}",
        base=base,
        file_path=file,
        new_file_text=new_file_text,
        quarantine_path=quarantine_path,
        quarantine_text=quarantine_text,
        pr_title=_build_pr_title(approved),
        pr_body=_build_pr_body(approved, quarantine_path, base),
        commit_message=_build_pr_title(approved),
    )


def apply_plan(plan: BranchPlan, client) -> str:
    """Drive the three writes through the MCP-shaped seam, branch-only, and return the PR URL.

    Order is load-bearing for the safety story: branch is cut from ``base``; both the pruned file
    and the quarantine artifact are written to the **head branch** (never ``base``); the PR points
    head→base for a human to merge. ``client`` is any ``GitHubClient`` (the ``FakeClient`` in tests,
    ``GhCliClient`` live).
    """
    client.create_branch(plan.base, plan.branch)
    client.put_file(plan.branch, plan.file_path, plan.new_file_text, plan.commit_message)
    client.put_file(plan.branch, plan.quarantine_path, plan.quarantine_text, plan.commit_message)
    return client.open_pr(plan.base, plan.branch, plan.pr_title, plan.pr_body)


# ---------------------------------------------------------------------------
# CLI — python -m sprigagent.apply <approved.json> [--dry-run] [--execute] ...
# ---------------------------------------------------------------------------
def _timestamp() -> str:
    """A short, filesystem/branch-safe run stamp. CLI-side (the pure logic takes it injected)."""
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _print_dry_run(plan: BranchPlan, file_text: str) -> None:
    diff = "".join(
        difflib.unified_diff(
            file_text.splitlines(keepends=True),
            plan.new_file_text.splitlines(keepends=True),
            fromfile=f"a/{plan.file_path}", tofile=f"b/{plan.file_path}",
        )
    )
    print("=== DRY RUN — no GitHub call will be made ===\n")
    print(f"branch: {plan.branch}   (head)")
    print(f"base:   {plan.base}   (target — never written to)\n")
    print(f"--- file edit: {plan.file_path} ---")
    print(diff if diff else "(no textual change)")
    print(f"\n--- quarantine artifact: {plan.quarantine_path} ---")
    print(plan.quarantine_text)
    print(f"--- PR title ---\n{plan.pr_title}\n")
    print(f"--- PR body ---\n{plan.pr_body}")
    print("=== end dry run — re-run with --execute to open the PR via gh ===")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m sprigagent.apply", description=__doc__)
    parser.add_argument("approved_json", help="path to approved.json written by the Approval UI")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the would-be branch/quarantine/PR and make no GitHub call (default)")
    parser.add_argument("--execute", action="store_true",
                        help="actually open the branch-only PR via gh (opt-in; uses your gh auth)")
    parser.add_argument("--base", default=DEFAULT_BASE, help=f"default branch to target (default {DEFAULT_BASE})")
    parser.add_argument("--repo", default=None, help="owner/name for gh (uses the cwd remote if omitted)")
    args = parser.parse_args(argv)

    approved = json.loads(Path(args.approved_json).read_text())
    items = approved.get("approved", [])
    if not items:
        print("Nothing to apply: the approved set is empty. No branch or PR was created.")
        return 1

    file_text = (Path(approved["repo"]) / approved["file"]).read_text()
    plan = build_plan(approved, file_text, timestamp=_timestamp(), base=args.base)

    # Safety-first: only an explicit --execute reaches GitHub. Everything else is a dry run.
    if not args.execute:
        _print_dry_run(plan, file_text)
        return 0

    client = github_client.GhCliClient(repo=args.repo)
    url = apply_plan(plan, client)
    print(f"Opened branch-only PR: {url}")
    print(f"  branch:     {plan.branch} → {plan.base}")
    print(f"  quarantine: {plan.quarantine_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
