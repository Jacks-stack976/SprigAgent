"""Tests for the Approval UI — pure, offline, no browser, no testbed.

Everything is driven by a CONSTRUCTED ``OrchestrationResult`` fixture so the suite stays fast and
testbed-independent. The renderer is a pure function; the Starlette app is exercised via the
offline ``TestClient``. The integrity rule (every figure read from the result, source label shown
verbatim, all content escaped) is asserted directly.
"""

from __future__ import annotations

from sprigagent.orchestrate import (
    ACCEPTED,
    GAVE_UP,
    NO_CANDIDATE,
    OrchestrationResult,
    Outcome,
    RungResult,
    SecurityEvent,
)
from sprigagent.rewrite import Edit
from sprigagent.types import EvalResult, PruneSuspect, Verdict

_STUB_SOURCE = "StubDriver · char-estimate (~chars/4)"
_REPLAY_SOURCE = "VertexAgentDriver · Gemini gemini-2.5-pro · replay cache"


# ---------------------------------------------------------------------------
# Fixture builders (constructed dataclasses — no orchestrate(), no testbed)
# ---------------------------------------------------------------------------
def _suspect(kind="bloat", locator="## Code style"):
    return PruneSuspect(file="CLAUDE.md", locator=locator, kind=kind, reason="reason-text")


def _edit(heading="## Code style", removed=("- removed bullet one",), kind="section-strip"):
    return Edit(
        suspect=_suspect(locator=heading),
        kind=kind,
        heading=heading,
        removed=removed,
        before_text="before",
        after_text="after",
        rationale="rationale-text-ABC",
    )


def _eval(sb=1.0, sa=1.0, tb=999, ta=640, verdict=Verdict.ACCEPT, evidence="evidence-text-XYZ"):
    return EvalResult(
        success_before=sb, success_after=sa, token_before=tb, token_after=ta,
        verdict=verdict, evidence=evidence,
    )


def _accepted(heading="## Code style", removed=("- removed bullet one",), ev=None):
    e = _edit(heading=heading, removed=removed)
    ev = ev or _eval()
    return Outcome(suspect=e.suspect, status=ACCEPTED, edit=e, eval=ev, rungs=(RungResult(edit=e, eval=ev),))


def _gaveup(heading="## Money convention (load-bearing)"):
    strip = _edit(heading=heading, removed=("- All amounts are integer cents.",), kind="section-strip")
    trim = _edit(heading=heading, removed=("- Convert at the display edge.",), kind="line-trim")
    reject = _eval(sb=1.0, sa=0.75, verdict=Verdict.REJECT, evidence="money evidence")
    return Outcome(
        suspect=strip.suspect, status=GAVE_UP, edit=None, eval=None,
        rungs=(
            RungResult(edit=strip, eval=reject),
            RungResult(edit=trim, eval=None, note="ReplayMiss: not provable offline (no recorded patch)"),
        ),
    )


def _no_candidate(locator="indentation-width conflict (CLAUDE.md:L36 vs GEMINI.md:L4)"):
    s = _suspect(kind="conflict", locator=locator)
    return Outcome(suspect=s, status=NO_CANDIDATE, edit=None, eval=None, rungs=())


def _result(outcomes=(), security_events=(), redactions=()):
    return OrchestrationResult(
        repo="/home/jack/sprig-demo", file="CLAUDE.md",
        outcomes=tuple(outcomes), security_events=tuple(security_events), redactions=tuple(redactions),
    )


# ---------------------------------------------------------------------------
# Task 1: pure renderer — accepted cards + attribution + integrity
# ---------------------------------------------------------------------------
def _render(result, source=_STUB_SOURCE, decisions=None):
    from sprigagent.ui import render_page

    return render_page(result, source, decisions or {})


def test_accepted_card_renders_real_numbers_and_source():
    removed = ("- Use 2-space indentation.", "- <script>alert(1)</script> sneaky bullet")
    html = _render(_result([_accepted(removed=removed)]))

    assert "## Code style" in html               # the heading
    assert "999" in html and "640" in html       # the real token numbers, read from the result
    assert "35.9" in html                         # token_delta_pct = (640-999)/999 = -35.9%
    assert "evidence-text-XYZ" in html            # the evidence string
    assert "rationale-text-ABC" in html           # the rationale
    assert _STUB_SOURCE in html                   # on-screen source attribution, verbatim
    assert "Use 2-space indentation" in html      # the quarantined removed line is shown


def test_removed_lines_are_html_escaped():
    html = _render(_result([_accepted(removed=("- <script>alert(1)</script> sneaky bullet",))]))
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html   # escaped...
    assert "<script>alert(1)" not in html                    # ...never a live tag


def test_numbers_are_not_hardcoded():
    html = _render(_result([_accepted(ev=_eval(tb=111, ta=70))]))
    assert "111" in html and "70" in html
    assert "999" not in html                      # the previous fixture's number is absent


def test_source_attribution_is_shown_verbatim():
    result = _result([_accepted()])
    assert _STUB_SOURCE in _render(result, source=_STUB_SOURCE)
    assert _REPLAY_SOURCE in _render(result, source=_REPLAY_SOURCE)
    assert "gemini-2.5-pro" in _render(result, source=_REPLAY_SOURCE)


# ---------------------------------------------------------------------------
# Task 2: GAVE_UP rung trail + security events + NO_CANDIDATE
# ---------------------------------------------------------------------------
def test_gaveup_shows_the_rung_trail_and_rule_kept():
    html = _render(_result([_gaveup()]))
    assert "## Money convention (load-bearing)" in html
    assert "REJECT" in html                       # the full strip was refused
    assert "75%" in html                          # the real 3/4 pass-rate is visible
    assert "unprovable" in html and "ReplayMiss" in html  # the eval=None rung shown honestly
    assert "load-bearing" in html and "kept" in html      # the won't-rubber-stamp framing


def test_security_event_is_rendered():
    sec = SecurityEvent(file="AGENTS.md", reason="override-instructions", categories=("SSN",))
    html = _render(_result(security_events=[sec]))
    assert "AGENTS.md" in html
    assert "override-instructions" in html
    assert "SSN" in html


def test_no_candidate_is_a_deferred_line():
    html = _render(_result([_no_candidate()]))
    assert "indentation-width conflict (CLAUDE.md:L36 vs GEMINI.md:L4)" in html
    assert "deferred" in html


def test_full_result_renders_all_sections_together():
    html = _render(_result(
        outcomes=[_accepted(), _gaveup(), _no_candidate()],
        security_events=[SecurityEvent(file="AGENTS.md", reason="override-instructions", categories=("SSN",))],
    ))
    assert "## Code style" in html          # accepted
    assert "## Money convention" in html    # gave_up
    assert "AGENTS.md" in html              # security
    assert "deferred" in html               # no_candidate


# ---------------------------------------------------------------------------
# Task 3: the Starlette app + decision capture
# ---------------------------------------------------------------------------
import json  # noqa: E402

from starlette.testclient import TestClient  # noqa: E402


def _client(result, source=_STUB_SOURCE, approved_path=None):
    from sprigagent.ui import create_app

    app = create_app(result, source=source, approved_path=approved_path)
    return TestClient(app)


def test_get_renders_the_dashboard(tmp_path):
    client = _client(_result([_accepted()]), approved_path=tmp_path / "approved.json")
    resp = client.get("/")
    assert resp.status_code == 200
    assert "## Code style" in resp.text
    assert "999" in resp.text and "640" in resp.text
    assert _STUB_SOURCE in resp.text


def test_approve_writes_the_approved_set(tmp_path):
    path = tmp_path / "approved.json"
    client = _client(_result([_accepted()]), approved_path=path)
    resp = client.post("/decision", data={"card_id": "## Code style", "decision": "approved"})
    assert resp.status_code == 200  # TestClient follows the 303 redirect back to /

    data = json.loads(path.read_text())
    assert [c["id"] for c in data["approved"]] == ["## Code style"]
    assert data["approved"][0]["token_before"] == 999
    assert data["approved"][0]["token_after"] == 640
    assert data["total_token_reduction"] == 999 - 640
    assert data["declined"] == []
    assert data["source"] == _STUB_SOURCE
    # A re-GET reflects the recorded decision.
    assert "✓ Approved" in client.get("/").text


def test_decline_excludes_from_the_approved_set(tmp_path):
    path = tmp_path / "approved.json"
    client = _client(_result([_accepted()]), approved_path=path)
    client.post("/decision", data={"card_id": "## Code style", "decision": "declined"})
    data = json.loads(path.read_text())
    assert data["approved"] == []
    assert data["declined"] == ["## Code style"]
    assert data["total_token_reduction"] == 0


# ---------------------------------------------------------------------------
# Task 4: faithful source attribution — derived from the ACTUAL driver/counter objects
# ---------------------------------------------------------------------------
def test_attribution_stub_path():
    from sprigagent.eval import StubDriver
    from sprigagent.eval.tokens import CharEstimator
    from sprigagent.ui import attribution

    # A None driver IS the orchestrator's default offline StubDriver.
    assert "StubDriver" in attribution(None, CharEstimator())
    assert "char-estimate" in attribution(None, CharEstimator())
    assert "StubDriver" in attribution(StubDriver("/tmp/fixtures"), CharEstimator())


def test_attribution_replay_path_names_the_real_model():
    from sprigagent.eval.cache import Cache
    from sprigagent.eval.driver import VertexAgentDriver
    from sprigagent.eval.tokens import GeminiTokenCounter
    from sprigagent.ui import attribution

    # Constructed offline — these constructors make no call (the client is lazy).
    replay_cache = Cache(record=False)
    driver = VertexAgentDriver(model="gemini-2.5-pro", cache=replay_cache)
    counter = GeminiTokenCounter(model="gemini-2.5-pro", cache=replay_cache)
    label = attribution(driver, counter)
    assert "Gemini" in label and "gemini-2.5-pro" in label and "replay" in label

    # A record=True counter is the live Vertex path (no call made here).
    live = GeminiTokenCounter(model="gemini-2.5-pro", cache=Cache(record=True))
    assert "live" in attribution(driver, live)


def test_render_shows_whichever_attribution_it_is_given():
    # The renderer relabels nothing: stub fixture -> stub label; replay fixture -> replay label.
    result = _result([_accepted()])
    assert "char-estimate" in _render(result, source=_STUB_SOURCE)
    assert "char-estimate" not in _render(result, source=_REPLAY_SOURCE)
    assert "replay cache" in _render(result, source=_REPLAY_SOURCE)


# ---------------------------------------------------------------------------
# Task 5: launch entry honoring SPRIG_DRIVER (no socket bound in tests)
# ---------------------------------------------------------------------------
def test_build_returns_result_and_stub_source(monkeypatch):
    from sprigagent.ui import __main__ as entry

    monkeypatch.setenv("SPRIG_DRIVER", "stub")
    fixture = _result([_accepted()])
    # Stub the loop so build() exercises driver selection + attribution without running the suite.
    monkeypatch.setattr(entry, "orchestrate", lambda repo, **kw: fixture)

    result, source = entry.build("/any/repo")
    assert result is fixture
    assert "StubDriver" in source and "char-estimate" in source


def test_replay_without_model_defaults_from_cache(monkeypatch):
    from sprigagent.ui import __main__ as entry

    monkeypatch.setenv("SPRIG_DRIVER", "replay")
    monkeypatch.delenv("VERTEX_MODEL", raising=False)
    # Zero-config replay: no VERTEX_MODEL -> the model is defaulted from the committed cache,
    # so build() succeeds (NOT CredentialsMissing) and the label carries the recorded model.
    # Stub the loop so this exercises driver selection + attribution without running the suite.
    fixture = _result([_accepted()])
    monkeypatch.setattr(entry, "orchestrate", lambda repo, **kw: fixture)

    result, source = entry.build("/any/repo")
    assert result is fixture
    assert "gemini-2.5-pro" in source and "replay" in source
