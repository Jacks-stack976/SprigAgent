"""Regression: the proof step proves against the file it was told to — not a hardcoded CLAUDE.md.

Closes the silent-mismatch bug where pointing at GEMINI.md (or any non-CLAUDE instruction file)
detected suspects in that file but proved them against CLAUDE.md. Two guards:

  * ``test_evaluate_proves_the_file_it_was_told`` — the bug-closer. It exercises the harness
    primitive ``evaluate(..., file="GEMINI.md")`` directly and fails LOUDLY under the old hardcode.
  * ``test_detect_and_prove_honor_the_target_file`` — the end-to-end detect+prove path the UI uses
    (``orchestrate`` -> ``propose`` -> ``prove_edit``), guarding that it stays file-faithful.

Offline & Node-free: an empty task suite (``tasks.json`` with no tasks) means ``load_tasks``
returns ``[]``, so ``evaluate``/``prove_edit`` run ZERO vitest iterations and the StubDriver is
constructed but never invoked. ``CharEstimator`` makes token counts deterministic and file-specific.
"""

import json
from pathlib import Path

from sprigagent.eval import evaluate
from sprigagent.eval.candidates import Candidate
from sprigagent.eval.tokens import CharEstimator
from sprigagent.orchestrate import ACCEPTED, orchestrate

# GEMINI.md is deliberately much longer than CLAUDE.md so their token counts cannot coincide.
_CLAUDE_MD = "# CLAUDE.md\n\n## Alpha\n- claude one\n- claude two\n"
_GEMINI_MD = "# GEMINI.md\n\n## Beta\n" + "".join(f"- gemini rule {i}\n" for i in range(40))


def _repo_with_two_context_files(root: Path) -> None:
    (root / "CLAUDE.md").write_text(_CLAUDE_MD)
    (root / "GEMINI.md").write_text(_GEMINI_MD)
    tasks = root / ".sprigagent" / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "tasks.json").write_text(json.dumps({"tasks": []}))  # no tasks -> no vitest


def test_evaluate_proves_the_file_it_was_told(tmp_path):
    _repo_with_two_context_files(tmp_path)
    est = CharEstimator()

    res = evaluate(
        tmp_path,
        Candidate(name="remove-beta", heading="## Beta"),
        file="GEMINI.md",
        counter=est,
    )

    # token_before is counted from the file evaluate READ. Under the old CLAUDE.md hardcode this
    # would be CLAUDE.md's count -> the first assertion fails loudly.
    assert res.token_before == est.count(_GEMINI_MD)
    assert res.token_before != est.count(_CLAUDE_MD)
    # The '## Beta' strip actually happened on GEMINI.md.
    assert res.token_after < res.token_before


def test_detect_and_prove_honor_the_target_file(tmp_path):
    _repo_with_two_context_files(tmp_path)
    est = CharEstimator()

    res = orchestrate(tmp_path, file="GEMINI.md", counter=est)

    assert res.file == "GEMINI.md"
    assert res.outcomes, "expected the 40-line '## Beta' section to surface a bloat suspect"
    assert all(o.suspect.file == "GEMINI.md" for o in res.outcomes)

    # The proven rung measured GEMINI.md's content, not CLAUDE.md's.
    proven = [o for o in res.outcomes if o.status == ACCEPTED and o.eval is not None]
    assert proven, "expected the '## Beta' strip to prove ACCEPT (tokens drop, empty suite)"
    assert proven[0].eval.token_before == est.count(_GEMINI_MD)
    assert proven[0].eval.token_before != est.count(_CLAUDE_MD)
