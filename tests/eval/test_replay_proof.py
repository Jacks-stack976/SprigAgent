"""Node-free, credential-free proof of the headline token reduction.

Reads the token counts **straight from the committed replay cache**
(``tests/eval/cache/tokens/``) — no Node/vitest, no ``$SPRIG_DEMO_REPO`` checkout, no Vertex
call. If the committed cache ever drifts from the claimed -34.9% ACCEPT headline, this test
breaks. That is the point: it is the can't-quietly-rot credibility artifact.

The complementary success-rate half (4/4 held on ACCEPT, 3/4 on the load-bearing REFUSE)
legitimately needs vitest and lives in ``test_orchestrator_integration.py``.
"""

import json
from pathlib import Path

CACHE_TOKENS = Path(__file__).resolve().parent / "cache" / "tokens"


def _committed_token_counts() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(CACHE_TOKENS.glob("*.json"))]


def test_replay_headline_is_pinned_by_the_committed_cache():
    records = _committed_token_counts()
    assert records, "no committed token cache to prove against"

    # Every recording is under one model — the replay keys hash it in, so a model swap would
    # invalidate them rather than silently replay stale numbers.
    assert {r["model"] for r in records} == {"gemini-2.5-pro"}

    values = {r["total_tokens"] for r in records}
    # 631 = full sprig-demo CLAUDE.md ; 411 = after the '## Code style' strip (the ACCEPT
    # headline). Both must be present in the committed cache.
    token_before, token_after = 631, 411
    assert token_before in values, f"expected full-file count 631 in cache, saw {sorted(values)}"
    assert token_after in values, f"expected pruned count 411 in cache, saw {sorted(values)}"

    token_delta_pct = round((token_after - token_before) / token_before * 100, 1)
    assert (token_before, token_after) == (631, 411)
    assert token_delta_pct == -34.9
