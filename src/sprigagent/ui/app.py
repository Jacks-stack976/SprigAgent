"""The Approval UI's Starlette app — render the dashboard, capture Approve/Decline decisions.

Offline and localhost-only. The app holds an already-produced ``OrchestrationResult`` (built from
already-scanned content) and renders it; ``POST /decision`` records a per-card approve/decline and
writes the approved-set artifact (``approved.json``). It is **decision capture only** — it touches
no git/GitHub and applies nothing (the branch-only apply is a separate, later round).
"""

from __future__ import annotations

import json
from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Route

from sprigagent.ui.render import APPROVED, DECLINED, _card_id, _heading, render_page

# ---------------------------------------------------------------------------
# Faithful source attribution — derived from the ACTUAL driver/counter objects used, so the UI
# never relabels: a stub run shows the stub estimate, a replay run shows the real Gemini model.
# ---------------------------------------------------------------------------
def attribution(driver, counter) -> str:
    """A human source label for the run's numbers, read off the real driver + counter objects.

    ``driver`` may be ``None`` — that is exactly the orchestrator's default offline StubDriver.
    The counter decides the headline label: ``CharEstimator`` → chars/4 estimate; ``GeminiTokenCounter``
    → the real Gemini model, ``replay cache`` (offline, ``cache.record`` False) or ``live Vertex``.
    """
    driver_name = type(driver).__name__ if driver is not None else "StubDriver"
    counter_name = type(counter).__name__

    if counter_name == "GeminiTokenCounter":
        model = getattr(counter, "_model", "gemini")
        cache = getattr(counter, "_cache", None)
        live = bool(getattr(cache, "record", False))
        counter_label = f"Gemini {model} · {'live Vertex' if live else 'replay cache'}"
    elif counter_name == "CharEstimator":
        counter_label = "char-estimate (~chars/4)"
    else:
        counter_label = counter_name

    return f"{driver_name} · {counter_label}"


# ---------------------------------------------------------------------------
# Approved-set artifact
# ---------------------------------------------------------------------------
def build_approved(result, source: str, decisions: dict) -> dict:
    """The approved-set payload: the approved cards (with their proven numbers), declined ids, total."""
    approved, declined, total = [], [], 0
    for outcome in result.accepted:
        cid = _card_id(outcome)
        choice = decisions.get(cid)
        if choice == APPROVED and outcome.eval is not None:
            ev = outcome.eval
            approved.append({
                "id": cid,
                "heading": _heading(outcome),
                "verdict": ev.verdict.value,
                "success_before": ev.success_before,
                "success_after": ev.success_after,
                "token_before": ev.token_before,
                "token_after": ev.token_after,
                "token_delta_pct": ev.token_delta_pct,
                "removed": list(outcome.edit.removed),
            })
            total += ev.token_before - ev.token_after
        elif choice == DECLINED:
            declined.append(cid)
    return {
        "repo": result.repo,
        "file": result.file,
        "source": source,
        "approved": approved,
        "declined": declined,
        "total_token_reduction": total,
    }


def write_approved(result, source: str, decisions: dict, approved_path) -> None:
    """Serialize the approved set to ``approved_path`` (decision capture — no git, no apply)."""
    path = Path(approved_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_approved(result, source, decisions), indent=2) + "\n")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
async def _home(request):
    app = request.app
    page = render_page(app.state.result, app.state.source, app.state.decisions)
    return HTMLResponse(page)


async def _decision(request):
    form = await request.form()
    card_id = form.get("card_id")
    choice = form.get("decision")
    app = request.app
    if card_id and choice in (APPROVED, DECLINED):
        app.state.decisions[card_id] = choice
        if app.state.approved_path is not None:
            write_approved(app.state.result, app.state.source, app.state.decisions, app.state.approved_path)
    return RedirectResponse("/", status_code=303)


def create_app(result, *, source: str, approved_path=None) -> Starlette:
    """Build the Approval dashboard app over an already-produced ``OrchestrationResult``."""
    app = Starlette(routes=[
        Route("/", _home, methods=["GET"]),
        Route("/decision", _decision, methods=["POST"]),
    ])
    app.state.result = result
    app.state.source = source
    app.state.approved_path = approved_path
    app.state.decisions = {}
    return app
