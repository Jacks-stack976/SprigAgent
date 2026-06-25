# CLAUDE.md — SprigAgent

## What this is
SprigAgent is an autonomous config-pruning agent for the Kaggle/Google "Vibe Coding
Agents" capstone (Agents for Business track, due 2026-07-06, 11:59 PM PT). It prunes
coding-agent context files (CLAUDE.md / GEMINI.md / AGENTS.md) and **proves** each
prune is net-positive — by running the target coding agent against a frozen eval
suite, baseline vs candidate — before a human approves it.

## Core principle
Subtraction over addition (Ponytail / YAGNI). This agent's whole thesis is that lean
context beats bloated context, so keep THIS file lean too. Heavy reference lives in
`docs/`, never inlined here.

## Architecture — 4 ADK agents
- **Detector** — wraps a deterministic linter; flags suspect lines/files (decides *what*).
- **Rewriter** — proposes the specific lean edit (*how*).
- **Eval-Runner** — sandbox: runs the coding agent on the task suite, baseline vs
  candidate; grades by tests (primary) + LLM-judge (fallback); measures tokens.
  This is the differentiator.
- **Orchestrator** — sequences the above; decides when to stop.

A human approves/declines proven changes via a dashboard. Prune-only, never-delete
(removed lines quarantined), apply to a branch only — never main.

## Non-negotiables
- **Pre-LLM security checkpoint:** all config contents are untrusted input. A
  deterministic pass does PII redaction + prompt-injection detection before anything
  reaches the model; flagged content routes to human review as a security event and is
  never treated as an instruction.
- **No API keys or passwords in the repo, ever.** Secrets go in `.env` (gitignored);
  `.env.example` documents the variable names only.
- **Scope: context files only.** Never touch application code.
- CC-BY 4.0; preserve judge-facing implementation comments.

## Stack
Google ADK (orchestration) · Gemini via Vertex AI (runtime model) · GitHub MCP
(read repo, open PRs) · Cloud Run (deploy).

## Testbed
Developed against the separate `sprig-demo` repo (the prune target) — not this repo.

## Commands
_(fill in as the app takes shape: install, run, test, deploy)_

## Reference
- `docs/vibecoding-agents-capstone-COMPREHENSIVE.md` — full competition rules & rubric
- `docs/sprigagent-final-plan.md` — locked design (formerly ContextProof, now SprigAgent)
