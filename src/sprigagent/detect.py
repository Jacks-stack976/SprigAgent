"""SprigAgent's deterministic Detector engine — autonomous prune-suspect discovery.

This is the real, offline, non-LLM linter that replaces the hardcoded ``DEMO_CANDIDATES``
(``sprigagent.eval.candidates``) as the *source* of prune candidates. It reads a coding-agent
context file (CLAUDE.md / GEMINI.md / AGENTS.md), runs it through the project's existing
security checkpoint, and flags prune suspects across four smell categories:

  * **bloat**      — long sections, or formatting/style rules a linter already enforces;
  * **stale-ref**  — referenced file paths / npm scripts that do not exist in the repo;
  * **duplicate**  — near-identical directives (intra-file or across sibling context files);
  * **conflict**   — best-effort, cheap lexical contradictions only (see ``_flag_conflicts``).

Design philosophy — **high recall, not precision.** The Detector proposes anything that
*could* be dead weight and lets the Eval-Runner prove each one. It deliberately surfaces even
load-bearing sections (e.g. a money convention) as candidates; proving load-bearing-ness is the
verification loop's job, not the Detector's.

Untrusted-input rule: context-file content reaches the heuristics ONLY through
``security.checkpoint.scan`` (the same deterministic gate the eval driver uses). BLOCKED ->
no candidates + a security event; REDACTED -> operate on the sanitized text and record the PII
categories; CLEAN -> proceed. Each file is scanned exactly once.

Output is the project's existing ``types.PruneSuspect`` (the documented Detector contract,
carrying category + rationale). ``suspect_to_candidate`` adapts a section-level suspect into an
``eval.candidates.Candidate`` so the offline proof loop (``evaluate``) consumes Detector output
with zero changes — a true drop-in for ``DEMO_CANDIDATES``.

Fully deterministic and offline: no model, no Vertex, no credentials. (The LLM flip for the
Detector — e.g. robust semantic conflict detection — is a separate, later step.)
"""

from __future__ import annotations

import difflib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from sprigagent.eval.candidates import Candidate
from sprigagent.security import checkpoint
from sprigagent.types import PruneSuspect, SecurityStatus

# The context files the Detector understands; the non-target ones form the cross-file pool.
CONTEXT_FILES = ("CLAUDE.md", "GEMINI.md", "AGENTS.md")

# Tunables (named so they read as policy, not magic numbers).
BLOAT_MIN_LINES = 6      # a context-file section longer than this is "long" -> bloat suspect
DUPE_THRESHOLD = 0.85    # normalized similarity at/above which two lines are near-duplicates
_MIN_LINE_LEN = 12       # ignore trivially short normalized lines in dupe/conflict comparisons

# Directories never walked when resolving file references (keeps stale-ref checks fast/honest).
_PRUNE_DIRS = {"node_modules", ".git", "dist", "build", ".venv", "venv", "__pycache__", ".next"}


@dataclass(frozen=True)
class Section:
    """One ``## `` section of a Markdown context file."""

    heading: str                    # the heading line, stripped, e.g. "## Code style"
    start: int                      # 1-based line number of the heading
    end: int                        # 1-based line number of the last non-blank content line
    content_lines: tuple[str, ...]  # non-blank lines in the section body (heading excluded)


@dataclass(frozen=True)
class DetectionResult:
    """What the Detector emits for one context file (mirrors the security checkpoint's verdict)."""

    status: SecurityStatus              # CLEAN | REDACTED | BLOCKED (of the *target* file)
    suspects: tuple[PruneSuspect, ...]  # () when the target file is BLOCKED
    redactions: tuple[str, ...] = ()    # PII categories redacted from the target before detection
    security_reason: str | None = None  # injection-intent label when BLOCKED


# ---------------------------------------------------------------------------
# Markdown structure
# ---------------------------------------------------------------------------
def _sections(text: str) -> list[Section]:
    """Split ``text`` into its ``## `` sections.

    A section runs from its heading to the next top-level ``## `` heading or EOF — the SAME
    boundary rule as ``eval.candidates.prune()``, so every heading this Detector emits is
    exactly strippable by ``prune()`` downstream.
    """
    lines = text.splitlines()
    heads = [i for i, ln in enumerate(lines) if ln.startswith("## ")]
    out: list[Section] = []
    for n, h in enumerate(heads):
        stop = heads[n + 1] if n + 1 < len(heads) else len(lines)
        body = lines[h + 1 : stop]
        content = tuple(ln for ln in body if ln.strip())
        last = h + 1
        for j in range(h + 1, stop):
            if lines[j].strip():
                last = j
        out.append(
            Section(heading=lines[h].strip(), start=h + 1, end=last + 1, content_lines=content)
        )
    return out


def _content_lines(text: str) -> list[tuple[int, str]]:
    """Return ``(1-based line number, raw line)`` for every non-blank, non-heading line."""
    return [
        (i, ln)
        for i, ln in enumerate(text.splitlines(), 1)
        if ln.strip() and not ln.startswith("#")
    ]


# ---------------------------------------------------------------------------
# Bloat
# ---------------------------------------------------------------------------
# Keywords that signal formatter/linter-enforced style (indentation, quoting, casing, …).
_STYLE_KW = (
    "indent", "space", "quote", "semicolon", "trailing", "comma", "whitespace",
    "newline", "camelcase", "pascalcase", "char", "arrow", "abbrev", "import",
    " var", " const", "line length",
)


def _has_linter_config(repo: Path) -> bool:
    """True if the repo ships a formatter/linter config (so style rules are tool-enforced)."""
    for pat in (".eslintrc*", ".prettierrc*", "biome.json", ".flake8", "ruff.toml", ".ruff.toml"):
        if any(repo.glob(pat)):
            return True
    pp = repo / "pyproject.toml"
    if pp.exists():
        blob = pp.read_text(errors="ignore")
        if "[tool.ruff" in blob or "[tool.black]" in blob or "[tool.flake8]" in blob:
            return True
    return False


def _is_linter_style(content_lines: tuple[str, ...]) -> bool:
    """Heuristic: the section is dense with formatter/linter-owned style keywords."""
    blob = " ".join(content_lines).lower()
    return sum(1 for kw in _STYLE_KW if kw in blob) >= 3


def _flag_bloat(file: str, text: str, repo: Path) -> list[PruneSuspect]:
    """Flag sections that are long, or that restate linter/formatter-enforced style. High-recall."""
    repo = Path(repo)
    linter = _has_linter_config(repo)
    out: list[PruneSuspect] = []
    for sec in _sections(text):
        n = len(sec.content_lines)
        style = linter and _is_linter_style(sec.content_lines)
        if n < BLOAT_MIN_LINES and not style:
            continue
        span = f"L{sec.start}–L{sec.end}"
        if style:
            reason = (
                f"{n}-line section ({span}) of formatting/style rules already enforced by the "
                f"repo's linter/formatter config — redundant tokens with no behavioral effect."
            )
        else:
            reason = (
                f"verbose {n}-line section ({span}); context files favor terse rules — flag for "
                f"review (whether it is load-bearing is the Eval-Runner's call)."
            )
        out.append(PruneSuspect(file=file, locator=sec.heading, kind="bloat", reason=reason))
    return out


# ---------------------------------------------------------------------------
# Stale references
# ---------------------------------------------------------------------------
_KNOWN_EXTS = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".json", ".md", ".txt",
    ".css", ".scss", ".html", ".yml", ".yaml", ".toml", ".cfg", ".ini", ".sh",
    ".rs", ".go", ".java", ".rb", ".sql",
}
# A path-like token: starts alnum/underscore, then path chars, ending in `.<letters>`.
_PATH_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./\-]*\.[A-Za-z]{1,5}")
_NPM_RE = re.compile(r"npm run ([A-Za-z][\w:-]*)")


def _repo_basenames(repo: Path) -> set[str]:
    """All file basenames under ``repo``, excluding heavy/irrelevant dirs (e.g. node_modules)."""
    names: set[str] = set()
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in _PRUNE_DIRS]
        names.update(files)
    return names


def _flag_stale_refs(file: str, text: str, repo: Path) -> list[PruneSuspect]:
    """Flag referenced file paths / npm scripts that do not exist in ``repo``."""
    repo = Path(repo)
    names = _repo_basenames(repo)
    scripts: set[str] = set()
    pkg = repo / "package.json"
    if pkg.exists():
        try:
            scripts = set(json.loads(pkg.read_text()).get("scripts", {}))
        except (json.JSONDecodeError, OSError):
            scripts = set()
    out: list[PruneSuspect] = []
    seen: set[tuple[str, str]] = set()
    for i, ln in _content_lines(text):
        for m in _PATH_RE.finditer(ln):
            ref = m.group(0)
            ext = os.path.splitext(ref)[1].lower()
            if "/" not in ref and ext not in _KNOWN_EXTS:
                continue  # not a file reference (e.g. "e.g", a version, prose)
            if (repo / ref).exists() or ref.rsplit("/", 1)[-1] in names:
                continue  # resolves by exact path or by basename anywhere in the repo
            key = ("path", ref)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                PruneSuspect(
                    file=file,
                    locator=f"L{i} {ref}",
                    kind="stale-ref",
                    reason=f"referenced path `{ref}` does not exist in the repo — stale reference.",
                )
            )
        if scripts:
            for m in _NPM_RE.finditer(ln):
                script = m.group(1)
                if script in scripts:
                    continue
                key = ("npm", script)
                if key in seen:
                    continue
                seen.add(key)
                out.append(
                    PruneSuspect(
                        file=file,
                        locator=f"L{i} npm run {script}",
                        kind="stale-ref",
                        reason=f"`npm run {script}` is not a script in package.json — stale command.",
                    )
                )
    return out


# ---------------------------------------------------------------------------
# Line normalization + shared cross-file pool (used by dupes and conflicts)
# ---------------------------------------------------------------------------
_BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")


def _norm(line: str) -> str:
    """Normalize a directive line for fuzzy comparison (drop bullets/markdown/punctuation)."""
    s = _BULLET_RE.sub("", line.strip())
    s = re.sub(r"[`*_#>]", "", s).lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _pool(file: str, text: str, siblings: dict[str, str]) -> list[tuple[str, int, str, str]]:
    """Build a comparison pool of ``(source_file, line_no, raw, normalized)`` across files."""
    pool = [(file, i, ln, _norm(ln)) for i, ln in _content_lines(text)]
    for sf, st in siblings.items():
        pool += [(sf, i, ln, _norm(ln)) for i, ln in _content_lines(st)]
    return pool


# ---------------------------------------------------------------------------
# Duplicates
# ---------------------------------------------------------------------------
def _flag_dupes(file: str, text: str, siblings: dict[str, str] | None = None) -> list[PruneSuspect]:
    """Flag near-duplicate directives within the file or against sibling context files."""
    pool = _pool(file, text, siblings or {})
    out: list[PruneSuspect] = []
    seen: set[tuple] = set()
    for a in range(len(pool)):
        fa, ia, ra, na = pool[a]
        if len(na) < _MIN_LINE_LEN:
            continue
        for b in range(a + 1, len(pool)):
            fb, ib, rb, nb = pool[b]
            if len(nb) < _MIN_LINE_LEN or (fa == fb and ia == ib):
                continue
            if difflib.SequenceMatcher(None, na, nb).ratio() < DUPE_THRESHOLD:
                continue
            # Anchor the suspect on the target file's occurrence; skip pairs wholly in siblings.
            if fa == file:
                loc, other = f"L{ia} (dup of {fb}:L{ib})", (fb, ib)
                anchor = (file, ia)
            elif fb == file:
                loc, other = f"L{ib} (dup of {fa}:L{ia})", (fa, ia)
                anchor = (file, ib)
            else:
                continue
            key = (anchor, other)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                PruneSuspect(
                    file=file,
                    locator=loc,
                    kind="duplicate",
                    reason=f'near-duplicate directive: "{ra.strip()}" ≈ "{rb.strip()}".',
                )
            )
    return out


# ---------------------------------------------------------------------------
# Conflicts (best-effort, cheap lexical contradictions ONLY)
# ---------------------------------------------------------------------------
# TODO(llm-flip): robust/semantic conflict detection — recognizing that two differently-worded
# rules contradict — is the job of the later LLM flip. This deterministic pass intentionally
# catches only two cheap, obvious cases (indentation-width mismatch and direct polarity
# negation). Do NOT grow this into a brittle hand-rolled NLP layer.
_NEG = {"never", "no", "not", "dont", "avoid", "without", "cannot"}
_POLARITY_STRIP = _NEG | {"always", "do", "please", "must", "should"}


def _indent_width(norm: str) -> int | None:
    """If a normalized line is about indentation and names a width, return it (else None)."""
    if "indent" not in norm:
        return None
    m = re.search(r"(\d+)", norm)
    return int(m.group(1)) if m else None


def _polarity(norm: str) -> str:
    return "neg" if set(norm.split()) & _NEG else "pos"


def _subject(norm: str) -> str:
    return " ".join(t for t in norm.split() if t not in _POLARITY_STRIP)


def _flag_conflicts(file: str, text: str, siblings: dict[str, str] | None = None) -> list[PruneSuspect]:
    """Best-effort: flag obviously contradictory directives (cheap lexical rules only)."""
    pool = _pool(file, text, siblings or {})
    out: list[PruneSuspect] = []

    # (a) indentation-width mismatch across directives.
    widths = [(f, i, w) for f, i, _r, n in pool if (w := _indent_width(n)) is not None]
    distinct = {w for _f, _i, w in widths}
    if len(distinct) > 1:
        where = ", ".join(f"{f}:L{i}→{w}" for f, i, w in widths)
        out.append(
            PruneSuspect(
                file=file,
                locator=f"indentation-width conflict ({where})",
                kind="conflict",
                reason=f"contradictory indentation widths across directives: {sorted(distinct)}.",
            )
        )

    # (b) direct polarity negation on the same subject ("always X" vs "never X").
    seen: set[tuple] = set()
    for a in range(len(pool)):
        fa, ia, ra, na = pool[a]
        if len(na) < _MIN_LINE_LEN:
            continue
        for b in range(a + 1, len(pool)):
            fb, ib, rb, nb = pool[b]
            if len(nb) < _MIN_LINE_LEN or _polarity(na) == _polarity(nb):
                continue
            if difflib.SequenceMatcher(None, _subject(na), _subject(nb)).ratio() < 0.9:
                continue
            key = tuple(sorted([(fa, ia), (fb, ib)]))
            if key in seen:
                continue
            seen.add(key)
            out.append(
                PruneSuspect(
                    file=file,
                    locator=f"{fa}:L{ia} vs {fb}:L{ib}",
                    kind="conflict",
                    reason=f'contradictory directives: "{ra.strip()}" vs "{rb.strip()}".',
                )
            )
    return out


# ---------------------------------------------------------------------------
# Orchestration + security ingest
# ---------------------------------------------------------------------------
def detect_text(
    content: str,
    *,
    target_repo: Path,
    file: str = "CLAUDE.md",
    siblings: dict[str, str] | None = None,
) -> DetectionResult:
    """Run the full deterministic detector over already-loaded context-file ``content``.

    ``content`` is UNTRUSTED: it is passed through ``checkpoint.scan`` before any heuristic sees
    it. ``siblings`` maps other context-file names to their (already checkpoint-cleared) text for
    cross-file dupe/conflict detection.
    """
    target_repo = Path(target_repo)
    siblings = siblings or {}

    verdict = checkpoint.scan(content)
    if verdict.status is SecurityStatus.BLOCKED:
        # Untrusted content never reaches the heuristics; route to human review as an event.
        return DetectionResult(
            status=SecurityStatus.BLOCKED,
            suspects=(),
            redactions=tuple(verdict.categories),
            security_reason=verdict.reason,
        )

    text = verdict.sanitized_content or ""  # REDACTED -> sanitized text; CLEAN -> unchanged
    suspects: list[PruneSuspect] = []
    suspects += _flag_bloat(file, text, target_repo)
    suspects += _flag_stale_refs(file, text, target_repo)
    suspects += _flag_dupes(file, text, siblings)
    suspects += _flag_conflicts(file, text, siblings)

    # Deduplicate identical findings (file, locator, kind) while preserving discovery order.
    seen: set[tuple[str, str, str]] = set()
    uniq: list[PruneSuspect] = []
    for s in suspects:
        key = (s.file, s.locator, s.kind)
        if key not in seen:
            seen.add(key)
            uniq.append(s)

    return DetectionResult(
        status=verdict.status, suspects=tuple(uniq), redactions=tuple(verdict.categories)
    )


def detect_file(target_repo: Path, file: str = "CLAUDE.md") -> DetectionResult:
    """Read ``target_repo/file`` (and its sibling context files) and detect prune suspects.

    The target file and every sibling are each scanned exactly once via ``checkpoint.scan``; a
    BLOCKED sibling is excluded from the cross-file comparison pool (its untrusted content is
    never compared against), and a BLOCKED *target* yields a security event with no candidates.
    """
    target_repo = Path(target_repo)
    content = (target_repo / file).read_text()

    siblings: dict[str, str] = {}
    for other in CONTEXT_FILES:
        if other == file:
            continue
        p = target_repo / other
        if not p.exists():
            continue
        v = checkpoint.scan(p.read_text())
        if v.status is SecurityStatus.BLOCKED:
            continue  # untrusted sibling — never compared against
        siblings[other] = v.sanitized_content or ""

    return detect_text(content, target_repo=target_repo, file=file, siblings=siblings)


# ---------------------------------------------------------------------------
# Adapter: PruneSuspect -> eval.candidates.Candidate (the DEMO_CANDIDATES drop-in)
# ---------------------------------------------------------------------------
def _slug(heading: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", heading.lstrip("#").strip().lower()).strip("-")
    return f"remove-{s}" if s else "remove-section"


def suspect_to_candidate(suspect: PruneSuspect) -> Candidate:
    """Adapt a section-level suspect into the ``Candidate`` shape ``evaluate()`` consumes.

    Section-strip suspects (bloat) carry their verbatim heading in ``locator``; the resulting
    ``Candidate`` is a true drop-in for a ``DEMO_CANDIDATES`` entry. Non-section suspects
    (stale-ref / duplicate / conflict) are not section strips and raise ``ValueError`` — those
    go to the Rewriter / human, not straight to a section-strip eval.
    """
    if not suspect.locator.startswith("## "):
        raise ValueError(
            f"suspect is not section-level (locator={suspect.locator!r}); "
            "only section-strip (bloat) suspects map to a Candidate"
        )
    heading = suspect.locator
    return Candidate(name=_slug(heading), heading=heading)
