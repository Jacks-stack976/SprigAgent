"""Deterministic, offline replay of the committed real cache (no credentials, no network).

Skips cleanly until the cache holds recordings (captured at the smoke / full-run step). Once
populated, it proves the recorded real run reproduces — same EvalResult twice — with the
credential variables stripped, so a replay can never silently fall through to a paid call.
"""

import json

import pytest

from sprigagent.eval import DEMO_CANDIDATES, evaluate, make_driver_and_counter
from sprigagent.eval.cache import Cache, ReplayMiss

_CRED_VARS = ["GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION", "GOOGLE_APPLICATION_CREDENTIALS"]


def _recorded_model(cache: Cache) -> str:
    """The model id a recording was made under — replay keys must match it exactly."""
    for path in sorted((cache.dir / "patches").glob("**/*.json")):
        return json.loads(path.read_text())["model"]
    pytest.skip("no recorded patches to read a model id from")


def test_replay_is_offline_and_deterministic(sprig_demo, monkeypatch):
    cache = Cache(record=False)
    if not cache.has_any():
        pytest.skip("no recorded Vertex cache yet (captured at the smoke/full-run step)")

    # Replay must not depend on credentials; strip them so a miss raises instead of calling.
    for var in _CRED_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("VERTEX_MODEL", _recorded_model(cache))

    # A full evaluate() replay needs the COMPLETE recording set (every task under both the
    # baseline and pruned contexts, plus both token counts). A partial cache — e.g. just the
    # single smoke recording — can't satisfy that, so skip until the full sweep has recorded.
    try:
        driver, counter = make_driver_and_counter("replay")
        first = evaluate(sprig_demo, DEMO_CANDIDATES["accept"], driver=driver, counter=counter)
        driver, counter = make_driver_and_counter("replay")
        second = evaluate(sprig_demo, DEMO_CANDIDATES["accept"], driver=driver, counter=counter)
    except ReplayMiss as miss:
        pytest.skip(f"partial cache — full recordings not captured yet ({miss})")

    assert first == second
