"""Integration: the autonomous Orchestrator over the real sprig-demo testbed.

Inherits ``sprig_demo`` / ``fixtures_dir`` from conftest.py and clean-skips if the testbed (or its
node_modules) is absent. Three groups:

  * **ADK wiring** — the Track-1 ``eval_runner`` agent calls real ``harness.evaluate()`` when a
    ``target_repo`` is in session state, returning the harness's real numbers (canned fallback
    otherwise keeps the in-process demo fast/green).
  * **autonomous run (stub)** — ``orchestrate()`` over sprig-demo: the stale-ref minimal diff
    ACCEPTs and preserves the valid refs; ``## Code style`` ACCEPTs at the full strip; the
    ``## Money convention`` ladder is driven and each rung's verdict reported (no predetermined
    ACCEPT); the aggregate has the Approval-UI shape.
  * **replay close-out (offline)** — under ``SPRIG_DRIVER=replay`` the recorded section-level
    candidates reproduce the real Gemini numbers: ACCEPT 631→411 (−34.9%, 4/4) and the money full
    strip REJECT at 3/4. Gentler line-trims ReplayMiss and are handled, not asserted.
"""

import asyncio
import json

import pytest

from sprigagent.agents.eval_runner import EVAL_OUTPUT_KEY, create_eval_runner
from sprigagent.agents.rewriter import REWRITER_OUTPUT_KEY
from sprigagent.eval import DEMO_CANDIDATES, StubDriver, evaluate
from sprigagent.orchestrate import ACCEPTED, NO_CANDIDATE, orchestrate

_STYLE = "## Code style"
_MONEY = "## Money convention (load-bearing)"


def _by(outcomes, predicate):
    matches = [o for o in outcomes if predicate(o)]
    assert matches, "expected outcome not found"
    return matches[0]


def _drive_eval_runner(seed_state: dict) -> dict:
    """Run ONLY the eval_runner agent with seeded session state; return its emitted eval_out dict."""
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types as genai_types

    async def run():
        svc = InMemorySessionService()
        await svc.create_session(app_name="t", user_id="u", session_id="s", state=seed_state)
        runner = Runner(agent=create_eval_runner(), app_name="t", session_service=svc)
        msg = genai_types.Content(role="user", parts=[genai_types.Part(text="go")])
        async for _ in runner.run_async(user_id="u", session_id="s", new_message=msg):
            pass
        sess = await svc.get_session(app_name="t", user_id="u", session_id="s")
        return sess.state[EVAL_OUTPUT_KEY]

    return json.loads(asyncio.run(run()))


def test_eval_runner_agent_calls_real_evaluate(sprig_demo, fixtures_dir):
    ref = evaluate(sprig_demo, DEMO_CANDIDATES["accept"], fixtures_dir=fixtures_dir)
    payload = _drive_eval_runner({
        "target_repo": str(sprig_demo),
        REWRITER_OUTPUT_KEY: json.dumps({"scenario": "accept"}),
    })
    # The agent emitted the harness's REAL result, not the canned placeholder.
    assert payload["verdict"] == "ACCEPT"
    assert payload["token_before"] == ref.token_before
    assert payload["token_after"] == ref.token_after
    assert payload["success_before"] == ref.success_before
    assert payload["success_after"] == ref.success_after


def test_full_autonomous_run_has_approval_ui_shape(sprig_demo, fixtures_dir):
    result = orchestrate(sprig_demo, driver=StubDriver(fixtures_dir))
    outcomes = result.outcomes

    # stale-ref -> minimal diff ACCEPTs and preserves the valid references (NOT a whole strip).
    stale = _by(outcomes, lambda o: o.suspect.kind == "stale-ref")
    assert stale.status == ACCEPTED
    assert "src/legacy/payments.ts" not in stale.edit.after_text
    assert "currency.ts" in stale.edit.after_text
    assert "tax.ts" in stale.edit.after_text

    # ## Code style -> ACCEPTs at the full strip (rung 0), so the loop stops immediately.
    style = _by(outcomes, lambda o: o.suspect.locator == _STYLE)
    assert style.status == ACCEPTED
    assert len(style.rungs) == 1
    assert style.rungs[0].edit.kind == "section-strip"

    # ## Money convention -> the full strip REJECTs and the ladder is driven. Assert only the
    # ROBUST invariants (rung-0 section-strip REJECT; it laddered) — NOT a predetermined ACCEPT.
    money = _by(outcomes, lambda o: o.suspect.locator == _MONEY)
    assert money.rungs[0].edit.kind == "section-strip"
    assert money.rungs[0].eval.verdict.value == "REJECT"
    assert len(money.rungs) >= 2

    # conflict -> NO_CANDIDATE (deferred); aggregate has the Approval-UI shape.
    conflict = _by(outcomes, lambda o: o.suspect.kind == "conflict")
    assert conflict.status == NO_CANDIDATE
    assert len(result.accepted) >= 2          # stale-ref + Code style are real, proven cards
    assert result.security_events == ()

    # Report the actual per-suspect outcome (run with -s) — incl. the money ladder verdicts.
    print("\n=== Autonomous run over sprig-demo (StubDriver, offline) ===")
    for o in outcomes:
        head = f"  [{o.suspect.kind:9}] {o.suspect.locator[:42]:42} -> {o.status}"
        if o.eval is not None:
            head += f"  ({o.eval.token_before}->{o.eval.token_after}, {o.eval.token_delta_pct:+.1f}%)"
        print(head)
        for i, r in enumerate(o.rungs):
            v = r.eval.verdict.value if r.eval else f"UNPROVABLE ({r.note})"
            print(f"        rung {i} [{r.edit.kind:>13}] -> {v}")
    print("  note: the money ladder's gentler ACCEPT is a StubDriver artifact (it keys only on the")
    print("  'integer cents' substring). The honest money result is the replay 3/4 REJECT below.")


# ---------------------------------------------------------------------------
# Task 7: replay close-out — the recorded REAL Gemini numbers reproduce offline.
# ---------------------------------------------------------------------------
_CRED_VARS = ["GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION", "GOOGLE_APPLICATION_CREDENTIALS"]


def _recorded_model(cache):
    for path in sorted((cache.dir / "patches").glob("**/*.json")):
        return json.loads(path.read_text())["model"]
    return None


def test_replay_reproduces_real_gemini_numbers_on_recorded_candidates(sprig_demo, monkeypatch):
    from sprigagent.eval import make_driver_and_counter
    from sprigagent.eval.cache import Cache

    cache = Cache(record=False)
    if not cache.has_any():
        pytest.skip("no recorded Vertex cache yet (captured at the smoke/full-run step)")

    # Replay must be credential-free: strip creds so a miss raises instead of reaching the network.
    for var in _CRED_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("VERTEX_MODEL", _recorded_model(cache))

    driver, counter = make_driver_and_counter("replay")
    result = orchestrate(sprig_demo, driver=driver, counter=counter)

    style = _by(result.outcomes, lambda o: o.suspect.locator == _STYLE)
    money = _by(result.outcomes, lambda o: o.suspect.locator == _MONEY)

    # Section-level rung-0 is what the cache recorded; a partial cache -> clean skip.
    if style.rungs[0].eval is None or money.rungs[0].eval is None:
        pytest.skip("partial replay cache — section-level candidates not fully recorded")

    # ACCEPT ## Code style: the REAL Gemini headline reproduces, offline, credential-free.
    s0 = style.rungs[0].eval
    assert style.status == ACCEPTED
    assert (s0.token_before, s0.token_after) == (631, 411)
    assert s0.token_delta_pct == -34.9
    assert s0.success_before == 1.0 and s0.success_after == 1.0   # 4/4 held

    # REJECT ## Money full strip: the REAL 3/4 (stronger than the stub's 2/4). Gentler line-trims
    # ReplayMiss and are handled (recorded unprovable, not laddered) -> the suspect is GAVE_UP.
    m0 = money.rungs[0].eval
    assert m0.verdict.value == "REJECT"
    assert m0.success_before == 1.0
    assert m0.success_after == 0.75                               # 3/4 — NOT the stub's 0.5
    assert any(r.eval is None and "ReplayMiss" in r.note for r in money.rungs[1:])

    print("\n=== Replay close-out (offline, credential-free, recorded gemini-2.5-pro) ===")
    print(f"  ## Code style   -> ACCEPT  {s0.token_before}->{s0.token_after} ({s0.token_delta_pct:+.1f}%), "
          f"{s0.success_before:.0%}->{s0.success_after:.0%}")
    print(f"  ## Money (strip)-> REJECT  {m0.success_before:.0%}->{m0.success_after:.0%} (real 3/4); "
          f"gentler rungs ReplayMiss -> GAVE_UP")
