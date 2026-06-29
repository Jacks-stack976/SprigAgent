"""Pure HTML rendering for the Approval UI — no server, no I/O, no templates.

``render_page(result, source, decisions)`` turns an ``OrchestrationResult`` into one self-contained
HTML page. It is a pure function (trivially testable) and obeys the integrity rule: every figure is
read from the result, the ``source`` attribution string is shown verbatim, and ALL interpolated
content is ``html.escape``d (context-file text can carry ``<``, ``>``, ``&``, backticks). The UI
never hardcodes a number, cherry-picks, or relabels a driver — feed it a stub run and it shows stub
numbers with stub attribution; feed it a replay run and it shows the real Gemini numbers with replay
attribution.
"""

from __future__ import annotations

import html

from sprigagent.orchestrate import (
    ACCEPTED,
    GAVE_UP,
    NO_CANDIDATE,
    OrchestrationResult,
    Outcome,
)

APPROVED = "approved"
DECLINED = "declined"


def _esc(value: object) -> str:
    """HTML-escape any value for safe interpolation (quotes too, for attribute contexts)."""
    return html.escape(str(value), quote=True)


def _card_id(outcome: Outcome) -> str:
    """The stable id for an accepted card — the suspect's locator is unique within a file."""
    return outcome.suspect.locator


def _heading(outcome: Outcome) -> str:
    """A human title for an outcome: the section heading, else the suspect locator."""
    edit = outcome.edit
    if edit is not None and edit.heading:
        return edit.heading
    return outcome.suspect.locator


# ---------------------------------------------------------------------------
# CSS — kept inline so the page is a single self-contained file (offline, no assets).
# ---------------------------------------------------------------------------
CSS = """
:root { --bg:#0f1419; --panel:#171c24; --line:#273039; --ink:#e6edf3; --mut:#9aa7b2;
        --accept:#2ea043; --reject:#d1413a; --warn:#d29922; --accent:#58a6ff; --rm:#3d1d1f; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--ink);
       font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
.wrap { max-width:920px; margin:0 auto; padding:28px 22px 64px; }
h1 { font-size:22px; margin:0 0 2px; letter-spacing:.2px; }
.sub { color:var(--mut); font-size:13px; }
.src { display:inline-block; margin-top:10px; padding:4px 10px; border:1px solid var(--line);
       border-radius:99px; color:var(--accent); font-size:12px; font-family:ui-monospace,Menlo,monospace; }
.counts { color:var(--mut); font-size:13px; margin-top:8px; }
.section-title { margin:30px 0 12px; font-size:13px; text-transform:uppercase; letter-spacing:.12em;
                 color:var(--mut); border-bottom:1px solid var(--line); padding-bottom:6px; }
.card { background:var(--panel); border:1px solid var(--line); border-radius:12px;
        padding:16px 18px; margin:12px 0; }
.card.approved { border-color:var(--accept); }
.card.declined { opacity:.6; }
.card h3 { margin:0 0 6px; font-size:17px; font-family:ui-monospace,Menlo,monospace; }
.badge { font-size:11px; font-weight:600; padding:2px 8px; border-radius:6px; vertical-align:middle; }
.badge.accept { background:rgba(46,160,67,.15); color:var(--accept); border:1px solid var(--accept); }
.badge.reject { background:rgba(209,65,58,.13); color:var(--reject); border:1px solid var(--reject); }
.badge.warn { background:rgba(210,153,34,.13); color:var(--warn); border:1px solid var(--warn); }
.metrics { display:flex; flex-wrap:wrap; gap:18px; margin:10px 0; font-family:ui-monospace,Menlo,monospace;
           font-size:14px; }
.metric .k { color:var(--mut); font-size:11px; text-transform:uppercase; letter-spacing:.08em; display:block; }
.delta-down { color:var(--accept); font-weight:600; }
.diff { background:#10151b; border:1px solid var(--line); border-radius:8px; margin:10px 0;
        font-family:ui-monospace,Menlo,monospace; font-size:12.5px; overflow:auto; }
.diff .lbl { color:var(--mut); padding:6px 12px; border-bottom:1px solid var(--line); font-size:11px;
             text-transform:uppercase; letter-spacing:.08em; }
.diff pre { margin:0; padding:8px 12px; }
.diff .rm { color:#ff9b95; background:var(--rm); display:block; padding:1px 4px; white-space:pre-wrap; }
.evidence { color:var(--mut); font-size:12.5px; margin:8px 0 2px; }
.rationale { font-size:13px; margin:6px 0 12px; }
.actions { display:flex; gap:10px; align-items:center; }
button { font:inherit; font-size:13px; padding:7px 16px; border-radius:8px; cursor:pointer;
         border:1px solid var(--line); background:#1f2630; color:var(--ink); }
button.approve { border-color:var(--accept); color:var(--accept); }
button.decline { border-color:var(--reject); color:var(--reject); }
.state { font-size:13px; font-weight:600; }
.state.approved { color:var(--accept); }
.state.declined { color:var(--reject); }
.total { background:var(--panel); border:1px solid var(--accept); border-radius:10px; padding:12px 16px;
         margin:10px 0 4px; font-family:ui-monospace,Menlo,monospace; }
.trail { list-style:none; padding:0; margin:8px 0; font-family:ui-monospace,Menlo,monospace; font-size:13px; }
.trail li { padding:4px 0; border-bottom:1px solid var(--line); }
.kept { color:var(--warn); font-size:13px; margin-top:8px; }
.sec { background:rgba(209,65,58,.06); border:1px solid var(--reject); border-radius:10px;
       padding:12px 16px; margin:10px 0; }
.muted-line { color:var(--mut); font-size:13px; padding:6px 0; }
"""


# ---------------------------------------------------------------------------
# Accepted cards (the headline)
# ---------------------------------------------------------------------------
def _diff_block(removed: tuple[str, ...]) -> str:
    lines = "".join(f'<span class="rm">{_esc(ln)}</span>' for ln in removed)
    return (
        '<div class="diff"><div class="lbl">diff — removed lines '
        '(quarantined verbatim · never deleted)</div><pre>' + lines + "</pre></div>"
    )


def _metrics(ev) -> str:
    pct = ev.token_delta_pct
    return (
        '<div class="metrics">'
        f'<div class="metric"><span class="k">verdict</span>'
        f'<span class="badge accept">{_esc(ev.verdict.value)}</span></div>'
        f'<div class="metric"><span class="k">pass-rate</span>'
        f'{_esc(f"{ev.success_before:.0%}")} → {_esc(f"{ev.success_after:.0%}")}</div>'
        f'<div class="metric"><span class="k">context tokens</span>'
        f'{_esc(f"{ev.token_before:,}")} → {_esc(f"{ev.token_after:,}")} '
        f'<span class="delta-down">{_esc(f"{pct:+.1f}%")}</span></div>'
        "</div>"
    )


def _accepted_card(outcome: Outcome, source: str, decision: str | None) -> str:
    ev, edit = outcome.eval, outcome.edit
    cid = _card_id(outcome)
    cls = " approved" if decision == APPROVED else " declined" if decision == DECLINED else ""

    if decision == APPROVED:
        state = '<span class="state approved">✓ Approved</span>'
    elif decision == DECLINED:
        state = '<span class="state declined">✗ Declined</span>'
    else:
        state = (
            f'<button class="approve" type="submit" name="decision" value="{APPROVED}">Approve</button>'
            f'<button class="decline" type="submit" name="decision" value="{DECLINED}">Decline</button>'
        )

    return (
        f'<div class="card{cls}">'
        f"<h3>{_esc(_heading(outcome))}</h3>"
        + _metrics(ev)
        + _diff_block(edit.removed)
        + f'<div class="evidence">evidence: {_esc(ev.evidence)}</div>'
        + f'<div class="rationale">{_esc(edit.rationale)}</div>'
        + f'<div class="src">source: {_esc(source)}</div>'
        + '<form method="post" action="/decision" class="actions" style="margin-top:12px;">'
        + f'<input type="hidden" name="card_id" value="{_esc(cid)}">'
        + state
        + "</form>"
        + "</div>"
    )


def _approved_total(result: OrchestrationResult, decisions: dict) -> int:
    """Σ proven token reduction over the approved accepted cards."""
    total = 0
    for o in result.accepted:
        if decisions.get(_card_id(o)) == APPROVED and o.eval is not None:
            total += o.eval.token_before - o.eval.token_after
    return total


def _accepted_section(result: OrchestrationResult, source: str, decisions: dict) -> str:
    cards = result.accepted
    if not cards:
        return ""
    total = _approved_total(result, decisions)
    body = "".join(_accepted_card(o, source, decisions.get(_card_id(o))) for o in cards)
    head = (
        '<div class="section-title">Proven prunes — approve or decline</div>'
        f'<div class="total">approved so far: <b class="delta-down">{_esc(f"{total:,}")}</b> '
        "context tokens removed (proven net-positive)</div>"
    )
    return head + body


# ---------------------------------------------------------------------------
# "Won't rubber-stamp" — GAVE_UP outcomes + their rung audit trail
# ---------------------------------------------------------------------------
def _rung_li(rung) -> str:
    ev = rung.eval
    if ev is None:
        # An unprovable rung (e.g. ReplayMiss under replay) — shown honestly, never hidden.
        detail = f'<span class="badge warn">unprovable</span> {_esc(rung.note)}'
    else:
        cls = "reject" if ev.verdict.value == "REJECT" else "accept" if ev.verdict.value == "ACCEPT" else "warn"
        detail = (
            f'<span class="badge {cls}">{_esc(ev.verdict.value)}</span> '
            f'pass {_esc(f"{ev.success_before:.0%}")}→{_esc(f"{ev.success_after:.0%}")}, '
            f'tokens {_esc(f"{ev.token_before:,}")}→{_esc(f"{ev.token_after:,}")}'
        )
    return f'<li>rung [{_esc(rung.edit.kind)}] → {detail}</li>'


def _gaveup_card(outcome: Outcome) -> str:
    trail = "".join(_rung_li(r) for r in outcome.rungs)
    return (
        '<div class="card">'
        f"<h3>{_esc(_heading(outcome))} "
        '<span class="badge warn">KEPT</span></h3>'
        '<div class="evidence">every prune was proven harmful or unprovable — the loop refused to '
        "rubber-stamp it:</div>"
        f'<ul class="trail">{trail}</ul>'
        '<div class="kept">↳ load-bearing rule — kept (no net-positive prune found).</div>'
        "</div>"
    )


def _gaveup_section(result: OrchestrationResult) -> str:
    cards = [o for o in result.outcomes if o.status == GAVE_UP]
    if not cards:
        return ""
    head = '<div class="section-title">Won\'t rubber-stamp — load-bearing rules kept</div>'
    return head + "".join(_gaveup_card(o) for o in cards)


# ---------------------------------------------------------------------------
# Security events (the pre-LLM checkpoint) + NO_CANDIDATE (deferred)
# ---------------------------------------------------------------------------
def _security_section(result: OrchestrationResult) -> str:
    events = result.security_events
    if not events:
        return ""
    rows = ""
    for e in events:
        cats = ", ".join(e.categories) if e.categories else "—"
        rows += (
            '<div class="sec">'
            f"<b>{_esc(e.file)}</b> — BLOCKED before the model "
            f'<span class="badge reject">{_esc(e.reason or "injection")}</span>'
            f'<div class="evidence">PII redacted from the human-review payload: {_esc(cats)}. '
            "Treated as untrusted data, routed to human review — the model was never invoked.</div>"
            "</div>"
        )
    return '<div class="section-title">Security events — blocked at the checkpoint</div>' + rows


def _nocandidate_section(result: OrchestrationResult) -> str:
    rows = [o for o in result.outcomes if o.status == NO_CANDIDATE]
    if not rows:
        return ""
    lines = "".join(
        f'<div class="muted-line">{_esc(o.suspect.kind)}: {_esc(o.suspect.locator)} '
        "— detected · deferred (robust resolution is the later LLM-flip's job)</div>"
        for o in rows
    )
    return '<div class="section-title">Detected · deferred</div>' + lines


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------
def _header(result: OrchestrationResult, source: str) -> str:
    n_acc = len(result.accepted)
    n_gave = sum(1 for o in result.outcomes if o.status != ACCEPTED)
    return (
        '<div class="head">'
        "<h1>SprigAgent — proven prunes, awaiting your call</h1>"
        f'<div class="sub">{_esc(result.repo)} · {_esc(result.file)}</div>'
        f'<div class="src">numbers measured by: {_esc(source)}</div>'
        f'<div class="counts">{n_acc} proven · {n_gave} other outcome(s) · '
        f"{len(result.security_events)} security event(s)</div>"
        "</div>"
    )


def render_page(result: OrchestrationResult, source: str, decisions: dict | None = None) -> str:
    """Render the whole Approval dashboard as one self-contained HTML string (pure)."""
    decisions = decisions or {}
    body = (
        _header(result, source)
        + _accepted_section(result, source, decisions)
        + _gaveup_section(result)
        + _security_section(result)
        + _nocandidate_section(result)
    )
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>SprigAgent — Approval</title>"
        f"<style>{CSS}</style></head><body><div class='wrap'>"
        + body
        + "</div></body></html>"
    )
