"""Record-replay cache for the real eval path — capture a paid call once, replay it free.

This is a cost guard, not a convenience. The Vertex driver and the Gemini token counter are
the only two places SprigAgent spends money; both route through this store. A hash of the
exact request keys a committed JSON record of the response. On a hit the recorded value is
replayed with **no API call** (so the offline replay test and the demo video reproduce a real
run for free); a miss is only ever serviced by a real call in *record* mode, and is a hard
error in *replay-only* mode (so a stale or absent recording fails loudly instead of silently
reaching for credentials).

Two record kinds, each in its own subtree under ``tests/eval/cache/``:

  * patches  ``patches/<task-id>/<key>.json`` -> ``{patch, input_tokens, output_tokens, model}``
             ``key = sha256(model, TEMPLATE_VERSION, system_instruction, user_content)``
  * tokens   ``tokens/<key>.json``            -> ``{total_tokens, model}``
             ``key = sha256(model, text)``

Records hold only diffs and integer counts — never secrets — so they are safe to commit.
The model name and ``TEMPLATE_VERSION`` are folded into the patch key so that swapping the
model or editing the prompt template invalidates stale recordings instead of replaying them.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

# Bump when the driver's prompt TEMPLATE changes, so old recordings stop matching and are
# re-captured (in record mode) rather than silently replayed against a new prompt.
TEMPLATE_VERSION = "v1"


class ReplayMiss(RuntimeError):
    """Raised in replay-only mode when no recording exists for a request.

    Carries the human-facing meaning "this would have cost money": replay mode is offline by
    contract, so a miss must never fall through to a real call — it stops the run instead.
    """


def _default_cache_dir() -> Path:
    # The recorded cache lives in this repo's tests tree (committed alongside the fixtures),
    # so tests and the demo replay it without credentials. Mirrors tokens/_default_fixtures.
    return Path(__file__).resolve().parents[3] / "tests" / "eval" / "cache"


def _sha(*parts: str) -> str:
    """Order- and boundary-unambiguous digest of several strings (NUL-delimited)."""
    h = hashlib.sha256()
    for part in parts:
        h.update(part.encode("utf-8"))
        h.update(b"\x00")  # delimiter so ("ab","c") and ("a","bc") never collide
    return h.hexdigest()


def patch_key(model: str, system_instruction: str, user_content: str) -> str:
    """Key for a coding-agent patch: model + template version + the exact payloads sent."""
    return _sha(model, TEMPLATE_VERSION, system_instruction, user_content)


def token_key(model: str, text: str) -> str:
    """Key for a token count: model + the exact text measured."""
    return _sha(model, text)


class Cache:
    """A thin JSON record-replay store. The driver/counter decide *when* to call; this only
    stores and loads, and knows whether a miss is allowed (``record``) or fatal (replay-only).
    """

    def __init__(self, cache_dir: Path | None = None, *, record: bool) -> None:
        self._dir = Path(cache_dir or _default_cache_dir())
        # record=True  -> miss is allowed; the caller makes a real call and records it.
        # record=False -> replay-only; a miss raises ReplayMiss (never reaches the network).
        self.record = record

    @property
    def dir(self) -> Path:
        """The root of this cache's record tree (read-only accessor for tests/tooling)."""
        return self._dir

    # --- patches -----------------------------------------------------------------------
    def _patch_path(self, task_id: str, key: str) -> Path:
        return self._dir / "patches" / task_id / f"{key}.json"

    def get_patch(self, task_id: str, key: str) -> dict | None:
        path = self._patch_path(task_id, key)
        return json.loads(path.read_text()) if path.exists() else None

    def put_patch(self, task_id: str, key: str, record: dict) -> None:
        path = self._patch_path(task_id, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")

    # --- token counts ------------------------------------------------------------------
    def _token_path(self, key: str) -> Path:
        return self._dir / "tokens" / f"{key}.json"

    def get_tokens(self, key: str) -> dict | None:
        path = self._token_path(key)
        return json.loads(path.read_text()) if path.exists() else None

    def put_tokens(self, key: str, record: dict) -> None:
        path = self._token_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")

    def has_any(self) -> bool:
        """True if any recording exists — lets the offline replay test skip when empty."""
        patches = self._dir / "patches"
        tokens = self._dir / "tokens"
        return any(patches.glob("**/*.json")) or any(tokens.glob("*.json"))
