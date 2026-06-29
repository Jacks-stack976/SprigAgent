"""SprigAgent's deterministic Rewriter engine — minimal diffs + a gentler-on-reject ladder.

The Detector (``sprigagent.detect``) emits coarse ``PruneSuspect``s ("this whole section / this
line looks prunable"). The Rewriter is the *how*: it turns a suspect into the **minimal** edit
that still removes the dead weight, and — when a full strip would REJECT — emits a strongest→
gentlest **ladder** of provable rungs so the Orchestrator (a later round) can re-prove each until
one ACCEPTs or the ladder is exhausted. This module is the capability; the Orchestrator wires the
reject→retry loop.

Why a Rewriter-owned prover (``prove_edit``)? The frozen proof loop (``eval.harness.evaluate``)
applies a candidate **strictly whole-section-by-heading** (``eval.candidates.Candidate`` carries
only a heading; ``prune`` strips heading→next ``## ``/EOF). Sub-section "gentler" edits therefore
cannot be proven by ``evaluate()`` as-is, and ``eval/`` is frozen. So the Rewriter owns a thin
prover that runs the **exact same** offline pipeline on two explicit context texts (true-original
``before`` vs partial-prune ``after``), reusing ONLY ``eval/``'s public building blocks
(``load_tasks`` / ``make_sandbox`` / ``apply_patch`` / ``grade`` / ``teardown`` / token counters).
A parity test pins ``prove_edit`` to ``evaluate()`` on the whole-section-strip case both express,
so it cannot silently drift. Measurements are the literal original vs the literal partial-prune —
honest, uninflated (the project's whole thesis is *trustworthy measured proof*).

Untrusted-input rule: the single file-reading entry (``propose``) routes content through
``security.checkpoint.scan`` exactly once; BLOCKED → no edits. The pure engine functions
(``minimal_diff`` / ``ladder``) operate on already-scanned text.

Fully deterministic and offline: no model, no Vertex, no credentials. (The LLM flip for the
Rewriter — robust semantic gentler-rewriting and conflict resolution — is a separate, later step.)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sprigagent.eval.candidates import Candidate, prune
from sprigagent.eval.sandbox import apply_patch, make_sandbox, teardown
from sprigagent.eval.grader import grade
from sprigagent.eval.tasks import load_tasks
from sprigagent.eval.tokens import DEFAULT_COUNTER, TokenCounter
from sprigagent.security import checkpoint
from sprigagent.types import EvalResult, PruneSuspect, SecurityStatus, Verdict

# Tunables, named so they read as policy rather than magic numbers.
_CORE_GROUPS = 2  # bloat-by-length minimal diff keeps this many leading bullet groups as a core

# A bullet line starts with -, *, + or "N." (mirrors detect._BULLET_RE so the two engines agree
# on what a directive line looks like). Continuation lines do NOT match and extend the group.
_BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")


@dataclass(frozen=True)
class Edit:
    """One Rewriter-proposed prune: the minimal removal, plus the texts that prove it.

    A rung in the gentler ladder. ``before_text``/``after_text`` are full context-file texts (the
    baseline config vs the candidate config) so the Rewriter-owned ``prove_edit`` can measure the
    literal original vs the literal partial-prune through the frozen pipeline.
    """

    suspect: PruneSuspect       # the suspect this edit addresses
    kind: str                   # "section-strip" | "line-trim"
    heading: str | None         # the section it operates within (None for non-section edits)
    removed: tuple[str, ...]    # quarantined verbatim lines — never destroyed (never-delete rule)
    before_text: str            # the scanned original context text (== raw for a CLEAN file)
    after_text: str             # the context text after this edit (the candidate config)
    rationale: str              # why this edit is safe and why it is leaner

    @property
    def removed_chars(self) -> int:
        """Size of the removal — the offline, counter-free key the ladder orders rungs by."""
        return len("".join(self.removed))


# ---------------------------------------------------------------------------
# Markdown structure (same boundary rule as eval.candidates.prune)
# ---------------------------------------------------------------------------
def _section_bounds(lines: list[str], heading: str) -> tuple[int, int] | None:
    """Return ``(start, end)`` line indices for ``heading``'s section, or None if absent.

    ``lines`` are ``splitlines(keepends=True)`` output. The section runs from its heading line
    (``start``) to the next top-level ``## `` heading or EOF (``end``, exclusive) — exactly the
    boundary ``eval.candidates.prune`` uses, so a section-strip Edit matches ``prune`` byte-for-byte.
    """
    start = next((i for i, ln in enumerate(lines) if ln.strip() == heading), None)
    if start is None:
        return None
    end = start + 1
    while end < len(lines) and not lines[end].startswith("## "):
        end += 1
    return start, end


def _bullet_groups(body_lines: list[str]) -> list[tuple[int, int]]:
    """Group section-body lines into bullet groups: ``[start, end)`` ranges into ``body_lines``.

    A line matching ``_BULLET_RE`` starts a group; the following lines (continuations, until the
    next bullet) belong to it. Returns ``[]`` when the body has no bullets (prose section).
    """
    starts = [i for i, ln in enumerate(body_lines) if _BULLET_RE.match(ln)]
    if not starts:
        return []
    bounds: list[tuple[int, int]] = []
    for n, s in enumerate(starts):
        e = starts[n + 1] if n + 1 < len(starts) else len(body_lines)
        bounds.append((s, e))
    return bounds


def _trim_units(body_lines: list[str]) -> list[tuple[int, int]]:
    """The granularity the ladder trims at: bullet groups, or — for a prose section with no
    bullets — one unit per non-blank line. Each is a ``[start, end)`` range into ``body_lines``."""
    groups = _bullet_groups(body_lines)
    if groups:
        return groups
    return [(i, i + 1) for i, ln in enumerate(body_lines) if ln.strip()]


def _remove_body_ranges(
    lines: list[str], body_start: int, ranges: list[tuple[int, int]]
) -> tuple[str, tuple[str, ...]]:
    """Remove the given body-relative line ranges from ``lines`` (keepends); return
    ``(after_text, removed)``. ``removed`` holds the verbatim removed lines (newline stripped,
    quarantine-friendly); ``after_text`` preserves the surviving lines byte-for-byte."""
    remove_idx: set[int] = set()
    for s, e in ranges:
        remove_idx.update(range(body_start + s, body_start + e))
    removed = tuple(lines[i].rstrip("\n") for i in sorted(remove_idx))
    after_text = "".join(ln for i, ln in enumerate(lines) if i not in remove_idx)
    return after_text, removed


# ---------------------------------------------------------------------------
# Style-keyword heuristic (formatter/linter-enforced directives) — minimal-diff helper.
# Deliberately focused on clearly formatter-owned rules so a "cosmetic core" (import order,
# boolean naming, camelCase, …) survives the linter-covered minimal diff. Robust semantic
# judgement is the later LLM flip's job, not this lexical pass.
# ---------------------------------------------------------------------------
_STYLE_KW = (
    "indent", "space", "quote", "semicolon", "trailing", "comma",
    "whitespace", "newline", "line length", "brace",
)


def _is_style_line(text: str) -> bool:
    blob = text.lower()
    return any(kw in blob for kw in _STYLE_KW)


# ---------------------------------------------------------------------------
# Minimal diff: turn a coarse suspect into the smallest edit that removes the dead weight.
# ---------------------------------------------------------------------------
def _stale_ref_token(locator: str) -> str | None:
    """The referenced token a stale-ref/duplicate locator points at (everything after ``L{i} ``)."""
    parts = locator.split(" ", 1)
    return parts[1] if len(parts) > 1 else None


def _locate_line(locator: str, lines: list[str], verify_token: str | None) -> int | None:
    """Resolve the 0-based index of the line a ``L{i} …`` locator names.

    Trust the locator's line number first; if it has drifted (or ``verify_token`` is no longer on
    that line), fall back to searching for ``verify_token``. Returns None when nothing matches."""
    m = re.match(r"L(\d+)\b", locator)
    if m:
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(lines) and (verify_token is None or verify_token in lines[idx]):
            return idx
    if verify_token is not None:
        for i, ln in enumerate(lines):
            if verify_token in ln:
                return i
    return None


def _line_removal_edit(
    suspect: PruneSuspect, full_text: str, *, verify_token: str | None, rationale: str
) -> Edit | None:
    lines = full_text.splitlines(keepends=True)
    idx = _locate_line(suspect.locator, lines, verify_token)
    if idx is None:
        return None
    removed = (lines[idx].rstrip("\n"),)
    after_text = "".join(lines[:idx] + lines[idx + 1:])
    return Edit(
        suspect=suspect, kind="line-trim", heading=None, removed=removed,
        before_text=full_text, after_text=after_text, rationale=rationale,
    )


def _bloat_minimal(suspect: PruneSuspect, full_text: str) -> Edit | None:
    """For a bloat suspect: drop only the linter-enforced bullets if the section mixes them with
    a cosmetic core; otherwise trim a verbose section to its first ``_CORE_GROUPS`` units."""
    heading = suspect.locator  # a bloat suspect's locator IS the verbatim "## heading"
    lines = full_text.splitlines(keepends=True)
    bounds = _section_bounds(lines, heading)
    if bounds is None:
        return None
    body_start, body_end = bounds[0] + 1, bounds[1]
    body = lines[body_start:body_end]
    units = _trim_units(body)
    if not units:
        return None

    style = [k for k, (s, e) in enumerate(units) if _is_style_line("".join(body[s:e]))]
    if 0 < len(style) < len(units):
        ranges = [units[k] for k in style]
        rationale = "drop only the linter/formatter-enforced bullets; keep the cosmetic core."
    else:
        if len(units) <= _CORE_GROUPS:
            return None  # already terse — no meaningful minimal trim
        ranges = [(units[_CORE_GROUPS][0], len(body))]
        rationale = f"trim the verbose section to its first {_CORE_GROUPS} directives (a kept core)."

    after_text, removed = _remove_body_ranges(lines, body_start, ranges)
    return Edit(
        suspect=suspect, kind="line-trim", heading=heading, removed=removed,
        before_text=full_text, after_text=after_text, rationale=rationale,
    )


def minimal_diff(suspect: PruneSuspect, full_text: str) -> Edit | None:
    """Turn a coarse suspect into the *smallest* edit that removes its dead weight (or None).

    ``full_text`` must be already-scanned context-file text (see ``propose`` for the single-scan
    entry). Per kind: ``stale-ref`` drops only the dead-ref line (valid refs survive); ``bloat``
    drops the linter bullets / trims to a core; ``duplicate`` drops the redundant copy; ``conflict``
    is deferred to the LLM flip.
    """
    if suspect.kind == "stale-ref":
        return _line_removal_edit(
            suspect, full_text, verify_token=_stale_ref_token(suspect.locator),
            rationale="remove only the stale reference; the rest of the section is untouched.",
        )
    if suspect.kind == "duplicate":
        return _line_removal_edit(
            suspect, full_text, verify_token=None,
            rationale="remove the redundant copy; the canonical statement is kept.",
        )
    if suspect.kind == "bloat":
        return _bloat_minimal(suspect, full_text)
    # TODO(llm-flip): semantic conflict *resolution* (which of two contradictory rules to keep,
    # or how to reconcile them) needs the model — the same deferral as the Detector's conflict
    # detection. Don't hand-roll a brittle deterministic resolver here.
    return None


# ---------------------------------------------------------------------------
# Gentler ladder: strongest (full strip) -> gentlest (smallest trim), each a provable rung.
# ---------------------------------------------------------------------------
def ladder(suspect: PruneSuspect, full_text: str) -> tuple[Edit, ...]:
    """Provable rungs for a suspect, ordered strongest→gentlest (largest→smallest removal).

    For a ``bloat`` suspect: rung 0 is the full section strip (parity with ``prune``/``evaluate``),
    then progressively gentler "keep heading + first k directive groups" trims. For other kinds the
    ladder is just the single ``minimal_diff`` edit (or ``()`` for conflict / when no edit applies).
    Rungs are deduped by resulting text and filtered to a strictly decreasing removal size, so the
    Orchestrator can walk a monotone ladder until one rung ACCEPTs or it is exhausted (→ GAVE_UP).
    """
    if suspect.kind != "bloat":
        edit = minimal_diff(suspect, full_text)
        return (edit,) if edit is not None else ()

    heading = suspect.locator  # a bloat suspect's locator IS the verbatim "## heading"
    lines = full_text.splitlines(keepends=True)
    bounds = _section_bounds(lines, heading)
    if bounds is None:
        return ()
    body_start, body_end = bounds[0] + 1, bounds[1]
    body = lines[body_start:body_end]

    rungs: list[Edit] = []

    # Strongest rung: the whole-section strip (heading + body). Built via prune() so it is
    # byte-for-byte what evaluate() would apply — the parity anchor.
    strip_after = prune(full_text, Candidate(name="full-strip", heading=heading))
    strip_removed = tuple(lines[i].rstrip("\n") for i in range(bounds[0], bounds[1]))
    rungs.append(Edit(
        suspect=suspect, kind="section-strip", heading=heading, removed=strip_removed,
        before_text=full_text, after_text=strip_after,
        rationale="strip the whole section (strongest prune).",
    ))

    # Gentler rungs: keep the heading + the first k directive groups, remove the rest.
    units = _trim_units(body)
    for k in range(len(units)):
        after_text, removed = _remove_body_ranges(lines, body_start, [(units[k][0], len(body))])
        rungs.append(Edit(
            suspect=suspect, kind="line-trim", heading=heading, removed=removed,
            before_text=full_text, after_text=after_text,
            rationale=f"keep the heading and the first {k} directive group(s); trim the rest.",
        ))

    # Order strongest→gentlest, drop duplicate results, and enforce a strictly decreasing ladder.
    rungs.sort(key=lambda e: e.removed_chars, reverse=True)
    out: list[Edit] = []
    seen_text: set[str] = set()
    for r in rungs:
        if r.after_text in seen_text:
            continue
        if out and r.removed_chars >= out[-1].removed_chars:
            continue  # not strictly gentler than the last kept rung
        out.append(r)
        seen_text.add(r.after_text)
    return tuple(out)


# ---------------------------------------------------------------------------
# prove_edit: run the FROZEN pipeline on (true-original before) vs (partial-prune after).
#
# `eval/` applies a candidate strictly whole-section-by-heading, so sub-section "gentler" edits
# can't be proven through `evaluate()` directly. This Rewriter-owned prover reuses ONLY `eval/`'s
# PUBLIC building blocks (load_tasks / make_sandbox / apply_patch / grade / teardown / a token
# counter) on two explicit context texts. The suite loop and decide rule below are faithful copies
# of `harness._run_suite` / `harness._decide`; a parity test (see the integration suite) pins this
# to `evaluate()` on the whole-section-strip case both can express, so it cannot silently drift.
# ---------------------------------------------------------------------------
def _run_suite(repo: Path, tasks: list, context_text: str, driver) -> tuple[float, tuple]:
    """Run every task once under one context file; fresh sandbox per task (mirror harness)."""
    passed = 0
    per_task: list[tuple[str, bool]] = []
    for task in tasks:
        sandbox = make_sandbox(repo)
        try:
            result = driver.run(sandbox, context_text, task)
            ok = apply_patch(sandbox, result.patch) and grade(task, sandbox)
        finally:
            teardown(sandbox)
        per_task.append((task.id, ok))
        passed += int(ok)
    rate = passed / len(tasks) if tasks else 0.0
    return rate, tuple(per_task)


def _decide(before_rate: float, after_rate: float, token_before: int, token_after: int) -> Verdict:
    """ACCEPT only if quality held AND tokens dropped; REJECT if quality regressed (mirror harness)."""
    if after_rate < before_rate:
        return Verdict.REJECT
    if after_rate >= before_rate and token_after < token_before:
        return Verdict.ACCEPT
    return Verdict.GAVE_UP


def prove_edit(repo: Path, edit: Edit, *, driver, counter: TokenCounter = DEFAULT_COUNTER) -> EvalResult:
    """Prove one rung: measure ``edit.before_text`` vs ``edit.after_text`` through the frozen
    pipeline and return the project's existing ``EvalResult`` (no new return type).

    ``driver`` is an ``eval.AgentDriver`` (the offline ``StubDriver`` for the demo). ``before``/
    ``after`` are the literal original and the literal partial-prune, so the token numbers are
    honest and uninflated. Makes no model / Vertex call when given an offline driver + counter.
    """
    repo = Path(repo)
    tasks = load_tasks(repo)
    before_rate, before_pt = _run_suite(repo, tasks, edit.before_text, driver)
    after_rate, after_pt = _run_suite(repo, tasks, edit.after_text, driver)

    token_before = counter.count(edit.before_text)
    token_after = counter.count(edit.after_text)
    verdict = _decide(before_rate, after_rate, token_before, token_after)
    pct = round((token_after - token_before) / token_before * 100, 1) if token_before else 0.0
    locator = edit.heading or edit.suspect.locator
    evidence = (
        f"edit={edit.kind} on {edit.suspect.file}:{locator} verdict={verdict.value}; "
        f"baseline {before_rate:.0%}; trimmed {after_rate:.0%}; "
        f"context tokens {token_before}->{token_after} ({pct:+.1f}%); removed {len(edit.removed)} line(s)."
    )
    return EvalResult(
        success_before=before_rate,
        success_after=after_rate,
        token_before=token_before,
        token_after=token_after,
        verdict=verdict,
        evidence=evidence,
    )


# ---------------------------------------------------------------------------
# Reactive seams the Orchestrator calls. These are the ONLY entry points that read a context
# file, so they own the single security scan (untrusted-input rule). The pure engine above
# operates on the already-scanned text these produce.
# ---------------------------------------------------------------------------
def propose(suspect: PruneSuspect, repo: Path) -> tuple[Edit, ...]:
    """Provable rungs for ``suspect``, strongest→gentlest. Reads ``repo/suspect.file`` and routes
    it through the security checkpoint EXACTLY ONCE; BLOCKED → ``()`` (the content is never turned
    into an edit, and routing it to human review is the Detector/Orchestrator's job)."""
    repo = Path(repo)
    content = (repo / suspect.file).read_text()
    verdict = checkpoint.scan(content)  # the single scan for this flow
    if verdict.status is SecurityStatus.BLOCKED:
        return ()
    text = verdict.sanitized_content or ""  # REDACTED -> sanitized; CLEAN -> unchanged
    return ladder(suspect, text)


def gentler(suspect: PruneSuspect, repo: Path, *, after_chars: int) -> Edit | None:
    """The next rung strictly gentler than a rejected edit of size ``after_chars`` chars, or None
    when the ladder is exhausted (→ a clean GAVE_UP). This is the Orchestrator's reject→retry step:
    feed the rejected edit's ``removed_chars`` and re-prove what comes back."""
    for rung in propose(suspect, repo):
        if rung.removed_chars < after_chars:
            return rung
    return None
