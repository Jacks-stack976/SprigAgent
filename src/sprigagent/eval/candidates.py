"""Prune candidates for the harness: a named removal of one section from a context file.

This phase represents a candidate as a section-strip keyed on its Markdown heading. That
is enough to model the two demo prunes — ACCEPT (drop the linter-covered style block) and
REJECT (drop the load-bearing money convention) — and to compute the pruned context text
deterministically. At real integration, a Rewriter-produced `types.PruneCandidate.diff`
would be applied to the full text instead; `prune()` is the only thing that changes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    name: str     # human label, e.g. "remove-style-block"
    heading: str  # the section heading to strip, e.g. "## Code style"


def prune(full_text: str, candidate: Candidate) -> str:
    """Return `full_text` with the candidate's section removed.

    A "section" runs from its heading line up to (but not including) the next top-level
    `## ` heading, or end-of-file. Raises if the heading is absent so a stale candidate
    fails loudly instead of silently pruning nothing.
    """
    lines = full_text.splitlines(keepends=True)
    start = next(
        (i for i, ln in enumerate(lines) if ln.strip() == candidate.heading), None
    )
    if start is None:
        raise ValueError(f"candidate heading not found: {candidate.heading!r}")
    end = start + 1
    while end < len(lines) and not lines[end].startswith("## "):
        end += 1
    return "".join(lines[:start] + lines[end:])


# The two demo candidates, matching sprig-demo/CLAUDE.md section headings exactly.
#   accept -> removes the linter/formatter-covered style block (zero behavioral effect)
#   reject -> removes the load-bearing integer-cents money convention (breaks 001/002)
DEMO_CANDIDATES: dict[str, Candidate] = {
    "accept": Candidate(name="remove-style-block", heading="## Code style"),
    "reject": Candidate(
        name="remove-money-convention", heading="## Money convention (load-bearing)"
    ),
}
