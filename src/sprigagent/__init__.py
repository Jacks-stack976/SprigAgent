"""SprigAgent — autonomous config-pruning agent.

Phase A scaffolds the four-agent ADK pipeline (Detector -> Rewriter -> Eval-Runner
-> Orchestrator) end-to-end in deterministic stub mode. Exactly one component is
real: the pre-LLM security checkpoint (`sprigagent.security.checkpoint`). Every other
agent is a stub behind a stable interface that a later phase replaces.
"""

__version__ = "0.0.1"
