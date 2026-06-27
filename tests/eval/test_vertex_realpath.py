"""Opt-in LIVE real-path test — the only test that can spend money, and only on request.

Skipped unless BOTH the Vertex credentials AND `SPRIG_REALPATH_LIVE=1` are set. Assertions
are DIRECTION-based, never exact constants: a real model's pass-rates and token counts will
not match the chars/4 estimates, and that is expected and honest. The ACCEPT prune must hold
quality and cut tokens; the REJECT prune must regress quality. Temperature is 0 (in the
driver), so a live run is as reproducible as the model allows.
"""

import os

import pytest

from sprigagent.eval import DEMO_CANDIDATES, evaluate, make_driver_and_counter
from sprigagent.types import Verdict

_LIVE = os.environ.get("SPRIG_REALPATH_LIVE") == "1"
_CREDS = all(
    os.environ.get(v)
    for v in ("GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION", "VERTEX_MODEL")
)

pytestmark = pytest.mark.skipif(
    not (_LIVE and _CREDS),
    reason="live real-path test: set SPRIG_REALPATH_LIVE=1 and Vertex creds to run",
)


def test_accept_direction_holds_quality_and_cuts_tokens(sprig_demo):
    driver, counter = make_driver_and_counter("vertex")
    result = evaluate(sprig_demo, DEMO_CANDIDATES["accept"], driver=driver, counter=counter)
    assert result.success_after >= result.success_before  # quality held
    assert result.token_after < result.token_before       # tokens down
    assert result.verdict is Verdict.ACCEPT


def test_reject_direction_regresses_quality(sprig_demo):
    driver, counter = make_driver_and_counter("vertex")
    result = evaluate(sprig_demo, DEMO_CANDIDATES["reject"], driver=driver, counter=counter)
    assert result.success_after < result.success_before   # quality regressed
    assert result.verdict is Verdict.REJECT
