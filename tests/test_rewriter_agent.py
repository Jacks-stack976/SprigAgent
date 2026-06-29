"""Tests for the Rewriter agent module's reactive entry points.

``propose()`` / ``gentler()`` are the thin wrappers that expose the deterministic engine
(``sprigagent.rewrite``) — turning a Detector suspect into provable rungs, strongest→gentlest.
The existing stub ``create_rewriter()`` LlmAgent must remain untouched (its security checkpoint
still fires at the model boundary), so this round is purely additive — the same shape as the
Detector round's ``discover()``.
"""

from sprigagent import rewrite
from sprigagent.agents import rewriter
from sprigagent.agents.rewriter import REWRITER_OUTPUT_KEY, create_rewriter
from sprigagent.security.checkpoint import security_before_model_callback


def test_agent_module_delegates_to_engine():
    # The agent entry points are the engine functions — one seam, no reimplementation.
    assert rewriter.propose is rewrite.propose
    assert rewriter.gentler is rewrite.gentler


def test_create_rewriter_unchanged_still_guards_model_boundary():
    agent = create_rewriter()
    # The stub Track-1 agent is left intact: the security checkpoint still fires before its model.
    assert agent.name == "rewriter"
    assert agent.before_model_callback is security_before_model_callback
    assert agent.output_key == REWRITER_OUTPUT_KEY
