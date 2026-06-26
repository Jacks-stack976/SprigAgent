"""Shared fixtures for the Eval-Runner harness tests.

The harness tests drive the REAL pipeline against the `sprig-demo` target repo (copy ->
git apply -> vitest -> measure). They locate that repo via `$SPRIG_DEMO_REPO` (default
`~/sprig-demo`) and skip cleanly if it — or its installed `node_modules` — is absent, so
the suite stays green on machines that don't have the testbed checked out.
"""

import os
from pathlib import Path

import pytest

SPRIG_DEMO = Path(os.environ.get("SPRIG_DEMO_REPO", Path.home() / "sprig-demo"))
FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="session")
def sprig_demo() -> Path:
    if not (SPRIG_DEMO / ".sprigagent" / "tasks" / "tasks.json").exists():
        pytest.skip(f"sprig-demo target not found at {SPRIG_DEMO}")
    if not (SPRIG_DEMO / "node_modules" / ".bin" / "vitest").exists():
        pytest.skip(f"sprig-demo node_modules not installed at {SPRIG_DEMO}")
    return SPRIG_DEMO


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES
