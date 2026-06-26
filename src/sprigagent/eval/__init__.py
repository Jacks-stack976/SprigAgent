"""SprigAgent's Eval-Runner harness — proves a context-file prune is net-positive.

Stub-driven and fully offline in this phase: a deterministic StubDriver replays cached
patch fixtures and an offline TokenCounter measures context-file savings, so the whole
verification loop runs with no model, no credentials, and no cost. The driver and the token
counter are the two seams the Vertex flip swings behind, leaving the harness unchanged.

The harness emits the project's existing `EvalResult` (see ``sprigagent.types``) so wiring
it into the ADK eval_runner agent later is a one-liner.
"""

from sprigagent.eval.candidates import DEMO_CANDIDATES, Candidate, prune
from sprigagent.eval.driver import AgentDriver, AgentResult, StubDriver
from sprigagent.eval.harness import evaluate
from sprigagent.eval.tasks import Task, load_tasks
from sprigagent.eval.tokens import CharEstimator, TokenCounter
from sprigagent.types import EvalResult, Verdict

__all__ = [
    "evaluate",
    "EvalResult",
    "Verdict",
    "AgentDriver",
    "AgentResult",
    "StubDriver",
    "Candidate",
    "prune",
    "DEMO_CANDIDATES",
    "Task",
    "load_tasks",
    "TokenCounter",
    "CharEstimator",
]
