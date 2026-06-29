"""Launch the Approval UI: ``python -m sprigagent.ui <repo> [--file CLAUDE.md] [--port 8765]``.

Runs the autonomous Orchestrator over the target context file with the ``SPRIG_DRIVER``-selected
driver/counter (``stub`` default — offline/free; ``replay`` — offline, the recorded real Gemini
numbers; ``vertex`` — live), derives the faithful source label, and serves the dashboard on
**localhost only**. Offline by default; no credentials needed unless you opt into the real path.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sprigagent.eval import make_driver_and_counter
from sprigagent.eval.selection import CredentialsMissing
from sprigagent.orchestrate import orchestrate
from sprigagent.ui.app import attribution, create_app

HOST = "127.0.0.1"  # localhost only — never bind a public interface
DEFAULT_PORT = 8765


def build(repo, file: str = "CLAUDE.md"):
    """Run the autonomous loop with the env-selected driver and return ``(result, source_label)``.

    The driver/counter come from ``$SPRIG_DRIVER`` (default stub); ``attribution`` derives the
    on-screen source from the ACTUAL objects, so the dashboard's numbers are never relabeled.
    May raise ``CredentialsMissing`` (real mode without a configured environment) — the caller
    surfaces it friendly. No model/Vertex call on the offline paths.
    """
    driver, counter = make_driver_and_counter()
    result = orchestrate(Path(repo), file=file, driver=driver, counter=counter)
    return result, attribution(driver, counter)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m sprigagent.ui", description=__doc__)
    parser.add_argument("repo", help="path to the target repo (e.g. ~/sprig-demo)")
    parser.add_argument("--file", default="CLAUDE.md", help="context file to prune (default CLAUDE.md)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"localhost port (default {DEFAULT_PORT})")
    args = parser.parse_args(argv)

    repo = Path(args.repo).expanduser()
    try:
        result, source = build(repo, args.file)
    except CredentialsMissing as exc:  # only reachable in vertex/replay mode without config
        print(exc, file=sys.stderr)
        print("\nNo dashboard was started (the offline default is `stub`).", file=sys.stderr)
        return 2

    approved_path = repo / ".sprigagent" / "approved.json"
    app = create_app(result, source=source, approved_path=approved_path)

    print(f"SprigAgent Approval UI → http://{HOST}:{args.port}")
    print(f"  repo:   {repo}/{args.file}")
    print(f"  source: {source}")
    print(f"  decisions written to: {approved_path}")

    import uvicorn  # imported lazily so the module loads (and tests run) without binding a socket

    uvicorn.run(app, host=HOST, port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
