"""Tests for the Detector agent module's autonomous-discovery entry point.

``discover()`` is the thin wrapper that runs the deterministic engine over a target repo and
returns a ``DetectionResult`` — the autonomous-discovery source that supersedes the hardcoded
``DEMO_CANDIDATES``. The existing stub ``create_detector()`` LlmAgent must remain untouched
(its security checkpoint still fires at the model boundary), so this round is purely additive.
"""

from pathlib import Path

from sprigagent.agents.detector import create_detector, discover
from sprigagent.detect import DetectionResult
from sprigagent.security.checkpoint import security_before_model_callback
from sprigagent.types import SecurityStatus


def test_discover_returns_detection_result_for_a_repo(tmp_path: Path):
    (tmp_path / "CLAUDE.md").write_text(
        "## Code style\n- Use 2-space indentation.\n- Use double quotes.\n- End with a semicolon.\n"
    )
    (tmp_path / ".prettierrc").write_text("{}\n")
    res = discover(tmp_path)
    assert isinstance(res, DetectionResult)
    assert res.status is SecurityStatus.CLEAN
    assert any(s.kind == "bloat" and s.locator == "## Code style" for s in res.suspects)


def test_create_detector_unchanged_still_guards_model_boundary():
    agent = create_detector()
    # The stub Track-1 agent is left intact: the security checkpoint still fires before its model.
    assert agent.name == "detector"
    assert agent.before_model_callback is security_before_model_callback
