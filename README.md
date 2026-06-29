# SprigAgent

An autonomous agent that prunes bloated coding-agent context files (CLAUDE.md,
GEMINI.md, AGENTS.md) and **proves** each change makes the coding agent measurably
better before a human approves it.

Capstone: Kaggle/Google Vibe Coding Agents — Freestyle track.
Status: in development. See `CLAUDE.md` for architecture and `docs/` for full design.

## Setup
_TBD — added as the agent takes shape._

## Eval-Runner: offline by default, real on opt-in

The Eval-Runner proves a prune by running the coding agent against a frozen task suite,
baseline vs candidate. It runs **offline and free by default** and only spends money when
you explicitly turn the real path on.

```bash
# Default: offline, deterministic, no credentials. Stub replays cached patches; chars/4 tokens.
python -m sprigagent.eval ~/sprig-demo accept

# Replay: offline, but using the REAL recorded Gemini patches + token counts (no calls).
SPRIG_DRIVER=replay VERTEX_MODEL=gemini-2.5-pro python -m sprigagent.eval ~/sprig-demo accept
```

`SPRIG_DRIVER` selects the driver: `stub` (default, offline/free), `vertex` (real Gemini,
paid), `replay` (offline, replays the committed `tests/eval/cache/`).

### Enabling the real Vertex path

```bash
gcloud auth application-default login            # ADC — credentials stay with you, never in the repo
export GOOGLE_CLOUD_PROJECT=<your-gcp-project>
export GOOGLE_CLOUD_LOCATION=us-central1
export VERTEX_MODEL=gemini-2.5-pro
export SPRIG_DRIVER=vertex

# Cost-guarded probe: exactly ONE real call on one task, then apply + grade. Stops here.
python -m sprigagent.eval ~/sprig-demo --smoke 001-split-evenly
```

Every paid call is guarded: the security checkpoint scans untrusted context **before** any
request, temperature is 0, output is bounded, and a record-replay cache (`tests/eval/cache/`)
means each request is paid for at most once and the offline `replay` path reproduces it for
free. Credentials are never read from or written to the repo; copy `.env.example` to `.env`
(gitignored) or export the variables in your shell.

## License
CC-BY 4.0 (see `LICENSE`).
