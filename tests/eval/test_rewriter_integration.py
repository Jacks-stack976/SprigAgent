"""Integration: the deterministic Rewriter turns real Detector suspects into provable edits.

Runs over the real ``sprig-demo`` testbed (inherits ``sprig_demo`` / ``fixtures_dir`` from
conftest.py; clean-skips if the testbed or its node_modules is absent). Fully offline — the
StubDriver replays cached fixtures; no model, no Vertex, no credentials.

Asserts:
  1. **parity** — for the ``## Code style`` whole-section strip (which both ``prove_edit`` and the
     frozen ``evaluate`` can express), the Rewriter's prover returns the SAME verdict / tokens /
     pass-rates as ``evaluate`` — pinning ``prove_edit`` to the real harness so it can't drift;
  2. **stale-ref minimal diff** — the dead ``src/legacy/payments.ts`` reference yields a one-line
     removal that ACCEPTs at a real saving and leaves the valid refs intact;
  3. **money-convention ladder** — the full strip REJECTs (cents anchor gone, 4/4→2/4); the gentler
     rungs are ordered and structurally valid, and each rung's ACTUAL verdict is reported (no
     predetermined ACCEPT — under the StubDriver's "integer cents" discrimination, a gentler rung
     that retains an integer-cents bullet flips to ACCEPT, but that is the stub's coarse model, not
     a proof the rung is truly safe — robust judgement is the later LLM flip's job).
"""

from sprigagent.agents.detector import discover
from sprigagent.eval import Candidate, StubDriver, evaluate
from sprigagent.rewrite import minimal_diff, propose, prove_edit
from sprigagent.types import Verdict

_STYLE = "## Code style"
_MONEY = "## Money convention (load-bearing)"


def _suspect(suspects, predicate):
    matches = [s for s in suspects if predicate(s)]
    assert matches, "expected suspect not discovered"
    return matches[0]


def test_prove_edit_parity_with_evaluate_on_section_strip(sprig_demo, fixtures_dir):
    res = discover(sprig_demo, "CLAUDE.md")
    style = _suspect(res.suspects, lambda s: s.kind == "bloat" and s.locator == _STYLE)

    strip = propose(style, sprig_demo)[0]  # rung 0 is the whole-section strip
    assert strip.kind == "section-strip"

    mine = prove_edit(sprig_demo, strip, driver=StubDriver(fixtures_dir))
    ref = evaluate(sprig_demo, Candidate(name="remove-style-block", heading=_STYLE), fixtures_dir=fixtures_dir)

    # prove_edit is pinned to the frozen harness on the case both express.
    assert mine.verdict is ref.verdict
    assert mine.token_before == ref.token_before
    assert mine.token_after == ref.token_after
    assert mine.success_before == ref.success_before
    assert mine.success_after == ref.success_after


def test_stale_ref_minimal_diff_accepts_and_preserves_valid_refs(sprig_demo, fixtures_dir):
    res = discover(sprig_demo, "CLAUDE.md")
    stale = _suspect(res.suspects, lambda s: s.kind == "stale-ref" and "payments.ts" in s.locator)

    edit = propose(stale, sprig_demo)[0]
    # Only the dead reference is gone; the valid references survive (NOT a whole-section strip).
    assert "src/legacy/payments.ts" not in edit.after_text
    assert "currency.ts" in edit.after_text
    assert "tax.ts" in edit.after_text

    result = prove_edit(sprig_demo, edit, driver=StubDriver(fixtures_dir))
    assert result.verdict is Verdict.ACCEPT
    assert result.success_before == 1.0
    assert result.success_after == 1.0       # removing a dead ref breaks nothing
    assert result.token_after < result.token_before


def test_money_convention_full_strip_rejects_and_ladder_is_reported(sprig_demo, fixtures_dir):
    res = discover(sprig_demo, "CLAUDE.md")
    money = _suspect(res.suspects, lambda s: s.kind == "bloat" and s.locator == _MONEY)

    rungs = propose(money, sprig_demo)
    assert len(rungs) >= 2

    # Robust structural invariants (NOT a predetermined ACCEPT).
    sizes = [r.removed_chars for r in rungs]
    assert all(a > b for a, b in zip(sizes, sizes[1:])), sizes      # strictly strongest -> gentlest
    assert rungs[0].kind == "section-strip"
    assert _MONEY not in rungs[0].after_text                        # the full strip removes the heading
    for r in rungs[1:]:
        assert r.kind == "line-trim"
        assert _MONEY in r.after_text                               # gentler rungs keep the heading

    driver = StubDriver(fixtures_dir)
    report = []
    for i, rung in enumerate(rungs):
        ev = prove_edit(sprig_demo, rung, driver=driver)
        report.append((i, rung.kind, ev.verdict.value, ev.token_before, ev.token_after, ev.token_delta_pct))

    # The full strip REJECTs: the cents anchor is gone, so 001/002 fail (4/4 -> 2/4).
    full_strip = next(r for r in report if r[1] == "section-strip")
    assert full_strip[2] == Verdict.REJECT.value

    # Report the ACTUAL verdict of every rung so the demo moment is visible (run with -s).
    print("\n=== Money-convention gentler ladder (StubDriver, offline) ===")
    for i, kind, verdict, tb, ta, pct in report:
        print(f"  rung {i} [{kind:>13}] -> {verdict:<7} tokens {tb}->{ta} ({pct:+.1f}%)")
    print("  note: stub discriminates only on the 'integer cents' substring; a gentler rung that")
    print("  retains an integer-cents bullet flips to ACCEPT here, but whether it is TRULY safe")
    print("  (it may drop the load-bearing remainder rule) needs the real driver / the LLM flip.")
