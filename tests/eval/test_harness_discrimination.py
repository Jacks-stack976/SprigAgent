"""The headline: the harness re-derives Phase 2's discrimination through the real pipeline.

These pass-rates (4/4 vs 4/4 -> ACCEPT, 4/4 vs 2/4 -> REJECT) come OUT of the real
sandbox -> git apply -> vitest -> token-count pipeline; they are not constants wired into a
stub. The StubDriver only chooses WHICH cached patch to replay, based on whether the
load-bearing cents rule survives the prune.
"""

from sprigagent.eval import DEMO_CANDIDATES, evaluate
from sprigagent.types import Verdict


def test_accept_candidate_holds_quality_and_cuts_tokens(sprig_demo, fixtures_dir):
    result = evaluate(sprig_demo, DEMO_CANDIDATES["accept"], fixtures_dir=fixtures_dir)
    assert result.success_before == 1.0          # baseline: 4/4
    assert result.success_after == 1.0           # pruning style bloat breaks nothing: 4/4
    assert result.token_after < result.token_before
    assert result.verdict is Verdict.ACCEPT


def test_reject_candidate_regresses_dependent_tasks(sprig_demo, fixtures_dir):
    result = evaluate(sprig_demo, DEMO_CANDIDATES["reject"], fixtures_dir=fixtures_dir)
    assert result.success_before == 1.0          # baseline: 4/4
    assert result.success_after == 0.5           # 001 + 002 fail without the cents rule: 2/4
    assert result.verdict is Verdict.REJECT
