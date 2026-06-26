"""Shared data contracts that flow between SprigAgent's four agents.

These plain dataclasses are the *seams* the whole project hangs on: every later phase
swaps a stub implementation behind these types without changing them. They are kept
dependency-free (no ADK, no Vertex) so they are trivially testable and stable. Each
field is commented because these names are the project's load-bearing interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Verdict(str, Enum):
    """The Eval-Runner's ruling on a candidate prune."""

    ACCEPT = "ACCEPT"    # quality held and tokens dropped -> surface for human approval
    REJECT = "REJECT"    # quality regressed -> the line was load-bearing, keep it
    GAVE_UP = "GAVE_UP"  # no net-positive edit found after retries -> drop the suspect


class SecurityStatus(str, Enum):
    """Outcome of the deterministic pre-LLM security checkpoint."""

    CLEAN = "CLEAN"        # nothing found; content may reach the model unchanged
    REDACTED = "REDACTED"  # PII removed; the sanitized content may reach the model
    BLOCKED = "BLOCKED"    # injection detected; content must NOT reach the model


@dataclass
class PruneSuspect:
    """What the Detector emits: a line/region it judges to be dead weight (the *what*)."""

    file: str      # context file the suspect lives in (e.g. "CLAUDE.md")
    locator: str   # where in the file — a line range or a text anchor
    kind: str      # smell category: bloat | stale-ref | duplicate | conflict
    reason: str    # human-readable justification for suspecting it

    @classmethod
    def from_dict(cls, d: dict) -> "PruneSuspect":
        return cls(file=d["file"], locator=d["locator"], kind=d["kind"], reason=d["reason"])


@dataclass
class PruneCandidate:
    """What the Rewriter emits: the specific minimal edit for one suspect (the *how*)."""

    suspect: PruneSuspect      # the suspect this edit addresses
    diff: str                  # the minimal unified diff that removes the dead weight
    removed_lines: list[str]   # quarantined verbatim — never destroyed (never-delete rule)
    rationale: str             # why this edit is safe and why it is leaner
    # Stub-mode scenario marker threaded from the input through to the Eval-Runner, so
    # the demo path (accept vs reject) is selected by input, not hardcoded position.
    scenario: str = "accept"

    @classmethod
    def from_dict(cls, d: dict) -> "PruneCandidate":
        return cls(
            suspect=PruneSuspect.from_dict(d["suspect"]),
            diff=d["diff"],
            removed_lines=list(d.get("removed_lines", [])),
            rationale=d["rationale"],
            scenario=d.get("scenario", "accept"),
        )


@dataclass
class EvalResult:
    """What the Eval-Runner emits: measured proof, baseline vs candidate."""

    success_before: float  # task pass-rate with the original config, 0.0–1.0
    success_after: float   # task pass-rate with the candidate config, 0.0–1.0
    token_before: int      # tokens the coding agent used on the baseline config
    token_after: int       # tokens the coding agent used on the candidate config
    verdict: Verdict       # ACCEPT / REJECT / GAVE_UP
    evidence: str          # short human-readable summary of the measurement

    @property
    def token_delta_pct(self) -> float:
        """Token change as a percentage; negative = savings (e.g. 4000 -> 1080 == -73.0)."""
        if self.token_before == 0:
            return 0.0
        return round((self.token_after - self.token_before) / self.token_before * 100, 1)

    @classmethod
    def from_dict(cls, d: dict) -> "EvalResult":
        return cls(
            success_before=float(d["success_before"]),
            success_after=float(d["success_after"]),
            token_before=int(d["token_before"]),
            token_after=int(d["token_after"]),
            verdict=Verdict(d["verdict"]),
            evidence=d["evidence"],
        )


@dataclass
class SecurityVerdict:
    """Output of the security checkpoint (see security/checkpoint.py)."""

    status: SecurityStatus            # CLEAN | REDACTED | BLOCKED
    sanitized_content: str | None     # PII-free content to forward (None if dropped)
    categories: tuple[str, ...] = ()  # PII categories redacted, e.g. ("SSN", "CC")
    reason: str | None = None         # for BLOCKED: which injection intent tripped the gate

    @classmethod
    def clean(cls, content: str) -> "SecurityVerdict":
        return cls(status=SecurityStatus.CLEAN, sanitized_content=content)

    @classmethod
    def redacted(cls, content: str, categories: tuple[str, ...]) -> "SecurityVerdict":
        return cls(
            status=SecurityStatus.REDACTED,
            sanitized_content=content,
            categories=tuple(categories),
        )

    @classmethod
    def blocked(
        cls, reason: str, sanitized: str | None = None, categories: tuple[str, ...] = ()
    ) -> "SecurityVerdict":
        # `sanitized` carries the PII-redacted content into the human-review payload, so
        # even a blocked item never leaks raw PII into logs or approval surfaces.
        # `categories` records any PII that was redacted from that payload.
        return cls(
            status=SecurityStatus.BLOCKED,
            sanitized_content=sanitized,
            reason=reason,
            categories=tuple(categories),
        )

    @property
    def is_event(self) -> bool:
        """True when this must be routed to human review as a security event."""
        return self.status is SecurityStatus.BLOCKED


@dataclass
class PipelineResult:
    """The Orchestrator's end-of-run summary — what main.py and the tests consume."""

    decision: str                          # SURFACED | DECLINED | SECURITY_EVENT
    security: SecurityVerdict              # what the checkpoint did to this input
    suspect: PruneSuspect | None = None    # None if blocked before detection completed
    candidate: PruneCandidate | None = None
    eval_result: EvalResult | None = None
    redactions: tuple[str, ...] = ()       # PII categories redacted en route to the model
    notes: str = ""                        # free-text trace for the dashboard/demo
