"""Integration: the autonomous Detector feeds the existing proof loop on the real testbed.

Runs the deterministic Detector over ``sprig-demo``'s context files and asserts:
  1. it surfaces BOTH demo sections — ``## Code style`` (ACCEPT) and the load-bearing
     ``## Money convention (load-bearing)`` (REJECT) — proving high-recall discovery still
     feeds the demo, plus the planted stale ref and the cross-file indentation conflict;
  2. its discovered candidates are a true drop-in for ``DEMO_CANDIDATES``: feeding them to
     ``evaluate()`` reproduces ACCEPT (4/4, tokens drop) and REJECT (2/4) end-to-end;
  3. a context file carrying a prompt injection (AGENTS.md) is BLOCKED on ingest — a security
     event with no candidates, never sent to a model.

Inherits ``sprig_demo`` / ``fixtures_dir`` from conftest.py and skips cleanly if the testbed
(or its node_modules) is absent. Fully offline: the StubDriver replays cached fixtures.
"""

from sprigagent.agents.detector import discover
from sprigagent.detect import suspect_to_candidate
from sprigagent.eval import DEMO_CANDIDATES, evaluate
from sprigagent.types import SecurityStatus, Verdict

_STYLE = "## Code style"
_MONEY = "## Money convention (load-bearing)"


def test_detector_surfaces_both_demo_sections(sprig_demo):
    res = discover(sprig_demo, "CLAUDE.md")
    assert res.status is SecurityStatus.CLEAN

    headings = {s.locator for s in res.suspects if s.kind == "bloat"}
    assert _STYLE in headings, f"ACCEPT candidate not discovered; got {sorted(headings)}"
    assert _MONEY in headings, f"REJECT candidate not discovered; got {sorted(headings)}"

    kinds = {s.kind for s in res.suspects}
    assert "stale-ref" in kinds  # src/legacy/payments.ts (planted issue #2)
    assert "conflict" in kinds   # CLAUDE 2-space vs GEMINI 4-space (planted issue #3)

    # The discovered candidate is a true drop-in: same heading as the hardcoded DEMO_CANDIDATES.
    by_head = {s.locator: s for s in res.suspects if s.kind == "bloat"}
    assert suspect_to_candidate(by_head[_STYLE]).heading == DEMO_CANDIDATES["accept"].heading
    assert suspect_to_candidate(by_head[_MONEY]).heading == DEMO_CANDIDATES["reject"].heading


def test_discovered_candidates_reproduce_accept_and_reject(sprig_demo, fixtures_dir):
    res = discover(sprig_demo, "CLAUDE.md")
    by_head = {s.locator: s for s in res.suspects if s.kind == "bloat"}

    accept = evaluate(sprig_demo, suspect_to_candidate(by_head[_STYLE]), fixtures_dir=fixtures_dir)
    assert accept.verdict is Verdict.ACCEPT
    assert accept.success_before == 1.0          # baseline 4/4
    assert accept.success_after == 1.0           # pruning linter-covered style breaks nothing
    assert accept.token_after < accept.token_before

    reject = evaluate(sprig_demo, suspect_to_candidate(by_head[_MONEY]), fixtures_dir=fixtures_dir)
    assert reject.verdict is Verdict.REJECT
    assert reject.success_before == 1.0          # baseline 4/4
    assert reject.success_after == 0.5           # 001 + 002 fail without the cents rule: 2/4


def test_injection_bearing_context_file_is_blocked_on_ingest(sprig_demo):
    res = discover(sprig_demo, "AGENTS.md")  # carries a fake SSN + an auto-approve injection
    assert res.status is SecurityStatus.BLOCKED
    assert res.suspects == ()
    assert res.security_reason                    # the injection intent label is recorded
    assert "SSN" in res.redactions                # PII was redacted into the event payload
