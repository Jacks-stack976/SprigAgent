"""SprigAgent's autonomous Orchestrator — the accept / retry / give-up loop.

This is the round where the pieces become one autonomous flow. It wires the committed
Detector and Rewriter into a single end-to-end pass over a coding-agent context file:

  1. ``discover`` the prune suspects (the *what*). A BLOCKED file is a security event with no
     candidates; redactions are recorded.
  2. For each suspect, ``propose`` the strongest→gentlest ladder (the *how*) and walk it:
     prove the strongest rung; on ACCEPT, surface it and stop (rung 0 is the biggest saving, so
     the first ACCEPT is the best edit); on REJECT, try the next, gentler rung; when the ladder is
     exhausted with no ACCEPT, GAVE_UP — the load-bearing rule is kept (the "won't rubber-stamp"
     outcome). A conflict / blocked suspect has no provable ladder → NO_CANDIDATE.
  3. Aggregate per-suspect ``Outcome``s + file-level ``SecurityEvent``s into an
     ``OrchestrationResult`` — the stable contract the Approval UI renders.

Everything reused behind clean seams: ``agents.detector.discover``, ``rewrite.propose`` /
``rewrite.prove_edit`` (which scan once and never re-read context raw), and the frozen
``eval`` pipeline via the injected driver. Fully deterministic and offline under the StubDriver;
the replay driver reproduces the recorded real Gemini numbers on the section-level candidates.
No model / Vertex / credential calls here.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sprigagent.agents.detector import discover
from sprigagent.eval import StubDriver
from sprigagent.eval.cache import ReplayMiss
from sprigagent.eval.tokens import DEFAULT_COUNTER, TokenCounter
from sprigagent.rewrite import Edit, propose, prove_edit
from sprigagent.types import EvalResult, PruneSuspect, SecurityStatus, Verdict

# Per-suspect outcome status values the Approval UI keys off.
ACCEPTED = "ACCEPTED"          # a prune proved net-positive -> surface a card for human approval
GAVE_UP = "GAVE_UP"            # tried every rung, none held -> the rule is load-bearing, kept
NO_CANDIDATE = "NO_CANDIDATE"  # nothing provable to propose (e.g. conflict — deferred to the LLM flip)

# The bundled fixtures the default offline StubDriver replays (mirrors eval.harness's default).
DEFAULT_FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "eval" / "fixtures"


@dataclass(frozen=True)
class RungResult:
    """One proven (or unprovable) rung in a suspect's ladder — the audit trail."""

    edit: Edit                    # the rung that was proven
    eval: EvalResult | None       # the measured result, or None if unprovable (e.g. ReplayMiss)
    note: str = ""                # why it is unprovable, when eval is None


@dataclass(frozen=True)
class Outcome:
    """What the loop decided for one suspect (the Approval UI's per-card contract)."""

    suspect: PruneSuspect             # the suspect this outcome addresses
    status: str                       # ACCEPTED | GAVE_UP | NO_CANDIDATE
    edit: Edit | None                 # the accepted prune (diff + quarantined removed lines) or None
    eval: EvalResult | None           # the accepted EvalResult (verdict/success/tokens/evidence) or None
    rungs: tuple[RungResult, ...] = ()  # every rung tried, strongest→gentlest


@dataclass(frozen=True)
class SecurityEvent:
    """A context file the checkpoint BLOCKED on ingest — routed to human review, never pruned."""

    file: str
    reason: str | None
    categories: tuple[str, ...] = ()


@dataclass(frozen=True)
class OrchestrationResult:
    """The autonomous run's aggregate — what the Approval UI renders next round."""

    repo: str
    file: str
    outcomes: tuple[Outcome, ...] = ()
    security_events: tuple[SecurityEvent, ...] = ()
    redactions: tuple[str, ...] = ()

    @property
    def accepted(self) -> tuple[Outcome, ...]:
        """The proven, net-positive prunes — the cards the human approves/declines."""
        return tuple(o for o in self.outcomes if o.status == ACCEPTED)


def _run_suspect(repo: Path, suspect: PruneSuspect, driver, counter: TokenCounter) -> Outcome:
    """Walk one suspect's ladder strongest→gentlest until a rung ACCEPTs or it is exhausted.

    propose() returns the rungs largest→smallest saving, so the first ACCEPT is the best edit:
    record it and stop. Every REJECT/GAVE_UP rung is kept in the audit trail and the loop drops to
    the next, gentler rung. An exhausted ladder with no ACCEPT is GAVE_UP — the load-bearing rule
    is kept (SprigAgent won't rubber-stamp a harmful prune).
    """
    rungs = propose(suspect, repo)
    if not rungs:
        # Nothing provable (conflict — deferred — or a blocked section): keep the rule, no card.
        return Outcome(suspect=suspect, status=NO_CANDIDATE, edit=None, eval=None, rungs=())

    tried: list[RungResult] = []
    for rung in rungs:
        try:
            ev = prove_edit(repo, rung, driver=driver, counter=counter)
        except ReplayMiss as miss:
            # An uncached rung under replay means "can't prove this offline" — never an unhandled
            # exception. Record it and stop laddering: the gentler line-trims are also uncached.
            tried.append(RungResult(edit=rung, eval=None, note=f"ReplayMiss: not provable offline ({miss})"))
            break
        tried.append(RungResult(edit=rung, eval=ev))
        if ev.verdict is Verdict.ACCEPT:
            return Outcome(suspect=suspect, status=ACCEPTED, edit=rung, eval=ev, rungs=tuple(tried))

    return Outcome(suspect=suspect, status=GAVE_UP, edit=None, eval=None, rungs=tuple(tried))


def orchestrate(
    repo,
    *,
    file: str = "CLAUDE.md",
    driver=None,
    counter: TokenCounter = DEFAULT_COUNTER,
    fixtures_dir=None,
) -> OrchestrationResult:
    """Run the autonomous loop over ``repo``'s context ``file`` and aggregate the outcomes.

    ``driver`` defaults to an offline ``StubDriver`` over the bundled fixtures (or ``fixtures_dir``);
    pass a replay driver to reproduce the recorded real numbers. Single security scan per suspect
    (via ``propose``); a BLOCKED file short-circuits to a security event with no candidates.
    """
    repo = Path(repo)
    if driver is None:
        driver = StubDriver(fixtures_dir or DEFAULT_FIXTURES, counter)

    res = discover(repo, file)
    if res.status is SecurityStatus.BLOCKED:
        return OrchestrationResult(
            repo=str(repo),
            file=file,
            outcomes=(),
            security_events=(
                SecurityEvent(file=file, reason=res.security_reason, categories=tuple(res.redactions)),
            ),
            redactions=tuple(res.redactions),
        )

    outcomes = tuple(_run_suspect(repo, s, driver, counter) for s in res.suspects)
    return OrchestrationResult(
        repo=str(repo),
        file=file,
        outcomes=outcomes,
        security_events=(),
        redactions=tuple(res.redactions),
    )
