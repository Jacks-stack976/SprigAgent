"""CLI: prove a prune end-to-end and print the verdict.

    python -m sprigagent.eval <target-repo> <accept|reject>

Runs the offline harness against a target repo with one of the demo prune candidates and
prints baseline vs pruned pass-rates, the context-token delta, and the verdict. This is the
artifact that demonstrates the harness end-to-end with no model and no cost.
"""

from __future__ import annotations

import sys
from pathlib import Path

from sprigagent.eval.candidates import DEMO_CANDIDATES
from sprigagent.eval.harness import evaluate


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2 or args[1] not in DEMO_CANDIDATES:
        choices = "|".join(DEMO_CANDIDATES)
        print(
            f"usage: python -m sprigagent.eval <target-repo> <{choices}>",
            file=sys.stderr,
        )
        return 2

    target_repo = Path(args[0]).expanduser()
    candidate = DEMO_CANDIDATES[args[1]]
    result = evaluate(target_repo, candidate)

    print(f"target:    {target_repo}")
    print(f"candidate: {candidate.name}  (strip {candidate.heading!r})")
    print(f"baseline pass-rate: {result.success_before:.0%}")
    print(f"pruned   pass-rate: {result.success_after:.0%}")
    print(
        f"context tokens:     {result.token_before} -> {result.token_after} "
        f"({result.token_delta_pct:+.1f}%)"
    )
    print(f"VERDICT:   {result.verdict.value}")
    print(f"evidence:  {result.evidence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
