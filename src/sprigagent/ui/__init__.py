"""SprigAgent Approval UI — a local, offline dashboard for the human gate.

Renders an ``OrchestrationResult`` (the proven prune cards + their real numbers + on-screen source
attribution, the "won't rubber-stamp" GAVE_UP trail, the security events) and captures Approve /
Decline per card, writing an approved-set artifact. Offline and localhost-only; it consumes an
already-produced result and never re-reads/re-scans context, calls a model, or touches git/GitHub
(the branch-only apply is a separate, later step).
"""

from sprigagent.ui.app import attribution, build_approved, create_app, write_approved
from sprigagent.ui.render import render_page

__all__ = ["render_page", "create_app", "attribution", "build_approved", "write_approved"]
