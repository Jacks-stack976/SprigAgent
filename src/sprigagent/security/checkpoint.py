"""SprigAgent's pre-LLM security checkpoint — the one component built for real in Phase A.

Coding-agent context files are UNTRUSTED INPUT. Before any of that text reaches the
model, a deterministic (non-LLM) pass does two things:

  1. PII redaction — strips SSNs and credit-card numbers BEFORE the content can reach
     the model, the logs, or any human-approval payload, recording which categories were
     hit. Redaction runs first so that even a *blocked* item's human-review payload is
     already PII-free.
  2. Prompt-injection detection — flags text that tries to act as an INSTRUCTION
     (override the rules, subvert the human gate, or exfiltrate data). On a hit the item
     is BLOCKED: it bypasses the model entirely and is routed to human review as a
     security event.

All repo/tool content is treated as DATA, never as instructions. The logic here is pure
and deterministic (fully unit-testable in isolation), and it is wired into ADK as a
`before_model_callback` so enforcement happens at the model boundary itself — and so it
survives the Phase-7 Vertex flip without change.
"""

from __future__ import annotations

import re

from sprigagent.types import SecurityStatus, SecurityVerdict

# A short sentinel the blocked-path response carries, so downstream code can recognise a
# security short-circuit even without inspecting session state.
SECURITY_EVENT_PREFIX = "[SECURITY EVENT]"


# ---------------------------------------------------------------------------
# 1. PII redaction (runs first)
# ---------------------------------------------------------------------------
# SSN: 3-2-4 digit groups separated by a dash or a single space. Kept precise (requires
# separators) to avoid redacting every 9-digit number.
_SSN_RE = re.compile(r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b")

# Credit-card CANDIDATES: 13–19 digits, optionally split by single spaces/dashes. A
# regex match is only a *candidate* — it is redacted only if it also passes the Luhn
# checksum (below), which cuts false positives like long IDs or version strings.
_CC_CANDIDATE_RE = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")

_SSN_PLACEHOLDER = "[REDACTED:SSN]"
_CC_PLACEHOLDER = "[REDACTED:CC]"


def _luhn_ok(digits: str) -> bool:
    """Standard Luhn checksum — distinguishes real card numbers from arbitrary digits."""
    total = 0
    parity = len(digits) % 2
    for i, ch in enumerate(digits):
        d = ord(ch) - 48  # fast int(ch) for a known-ASCII digit
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _redact_pii(content: str) -> tuple[str, tuple[str, ...]]:
    """Return (sanitized_content, categories_hit).

    Structured as an ordered set of rules so new categories (email, phone, API keys)
    can be added later without touching the surrounding scan logic.
    """
    categories: list[str] = []
    sanitized = content

    # --- SSNs ---
    if _SSN_RE.search(sanitized):
        categories.append("SSN")
        sanitized = _SSN_RE.sub(_SSN_PLACEHOLDER, sanitized)

    # --- Credit cards (Luhn-validated) ---
    def _cc_sub(match: re.Match) -> str:
        raw = match.group(0)
        digits = re.sub(r"\D", "", raw)
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            return _CC_PLACEHOLDER
        return raw  # candidate failed Luhn -> not a card, leave it untouched

    cc_redacted = _CC_CANDIDATE_RE.sub(_cc_sub, sanitized)
    if cc_redacted != sanitized:
        categories.append("CC")
        sanitized = cc_redacted

    return sanitized, tuple(categories)


# ---------------------------------------------------------------------------
# 2. Prompt-injection detection
# ---------------------------------------------------------------------------
# Intent-based patterns. A hit means the input is trying to be an INSTRUCTION rather than
# DATA — to override the rules, subvert the human approval gate, or exfiltrate secrets.
# Any hit -> BLOCKED (the model is bypassed and the item goes to human review).
_INJECTION_PATTERNS: tuple[tuple[str, "re.Pattern[str]"], ...] = (
    (
        "override-instructions",
        re.compile(
            r"\b(ignore|disregard|forget|override)\b.{0,40}?\b(previous|above|prior|earlier|all|your)\b.{0,25}?\b(instruction|prompt|rule|direction|guideline)",
            re.I | re.S,
        ),
    ),
    (
        "role-hijack",
        re.compile(
            r"(you are now\b|new system prompt|system prompt\s*:|\bact as (an?|the)\b|\bpretend to be\b)",
            re.I,
        ),
    ),
    (
        "gate-subversion",
        re.compile(
            r"(auto[-\s]?approve|approve (this |it )?(without|with no) (review|approval|human|gate)|approve (this |it )?automatically|bypass.{0,20}?(review|human|gate|approval)|mark.{0,15}?as approved)",
            re.I,
        ),
    ),
    (
        "exfiltration",
        re.compile(
            r"((print|reveal|show|send|leak|dump|disclose|output).{0,30}?(system prompt|your (instructions|prompt)|api[\s_-]?key|secret|credential)|\bexfiltrate\b)",
            re.I,
        ),
    ),
)


def _detect_injection(content: str) -> str | None:
    """Return the matched intent label, or None if the content reads as plain data."""
    for label, pattern in _INJECTION_PATTERNS:
        if pattern.search(content):
            return label
    return None


def scan(content: str) -> SecurityVerdict:
    """The deterministic gate. Order matters:

    redact PII FIRST (so no payload — including a blocked item's human-review payload —
    ever carries raw PII), THEN test the redacted text for injection.
    """
    sanitized, categories = _redact_pii(content)

    intent = _detect_injection(sanitized)
    if intent is not None:
        # Carry the PII-redacted text into the security event, never the raw input, and
        # record any PII categories that were redacted from that payload.
        return SecurityVerdict.blocked(
            reason=intent, sanitized=sanitized, categories=categories
        )

    if categories:
        return SecurityVerdict.redacted(sanitized, categories)

    return SecurityVerdict.clean(sanitized)


# ---------------------------------------------------------------------------
# 3. ADK wiring — enforced at the model boundary (before_model_callback)
# ---------------------------------------------------------------------------
# Attached to every agent that will eventually call a model. ADK invokes this right
# before the model:
#   BLOCKED   -> return an LlmResponse        => ADK skips the model entirely
#   REDACTED  -> mutate llm_request in place  => the model proceeds on PII-free text
#   CLEAN     -> return None                  => the model proceeds unchanged
# Side effects are recorded on callback_context.state so the Orchestrator can route the
# item (security_event) and report what was redacted.


def _request_text(llm_request) -> str:
    """Concatenate the text parts of the request contents (the untrusted input)."""
    chunks: list[str] = []
    for content in (llm_request.contents or []):
        for part in (content.parts or []):
            if getattr(part, "text", None):
                chunks.append(part.text)
    return "\n".join(chunks)


def _redact_request_in_place(llm_request) -> None:
    """Replace each text part with its redacted form so the model never sees raw PII."""
    for content in (llm_request.contents or []):
        for part in (content.parts or []):
            if getattr(part, "text", None):
                part.text = _redact_pii(part.text)[0]


def security_before_model_callback(callback_context, llm_request):
    """ADK ``before_model_callback``: the deterministic gate at the model boundary.

    Parameter names (``callback_context``, ``llm_request``) must match ADK's keyword
    contract. Returns ``None`` to let the (possibly redacted) request proceed, or an
    ``LlmResponse`` to block the model call outright.
    """
    # Imported lazily so the pure scan() logic above stays import-light and ADK-free.
    from google.adk.models.llm_response import LlmResponse
    from google.genai import types as genai_types

    verdict = scan(_request_text(llm_request))

    if verdict.status is SecurityStatus.BLOCKED:
        # Record a security event for the Orchestrator to route to human review.
        callback_context.state["security_event"] = {
            "reason": verdict.reason,
            "categories": list(verdict.categories),
        }
        message = (
            f"{SECURITY_EVENT_PREFIX} Prompt-injection blocked "
            f"(intent: {verdict.reason}). The content was treated as untrusted data and "
            f"routed to human review; the model was not invoked."
        )
        return LlmResponse(
            content=genai_types.Content(
                role="model", parts=[genai_types.Part(text=message)]
            ),
        )

    if verdict.status is SecurityStatus.REDACTED:
        _redact_request_in_place(llm_request)
        callback_context.state["redactions"] = list(verdict.categories)
        return None

    return None
