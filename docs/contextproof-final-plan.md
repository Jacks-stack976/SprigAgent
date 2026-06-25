# ContextProof — Final Agent Plan

> A config-pruning agent that **proves** each change makes your coding agent measurably better, then asks before applying it.
> Capstone track: **Agents for Business** · Solo · Deadline July 6, 2026, 11:59 PM PT · Open-source CC-BY 4.0

---

## 1. Why I'm building this

This is a scratch-my-own-itch build, which is the strongest reason to build anything. Working on SaintStudy, I hit the exact problem this solves: coding-agent context files (CLAUDE.md and friends) bloat over time, bury the rules that matter, waste tokens, and quietly degrade the agent — and nobody can tell which lines are dead weight versus load-bearing, because instruction-following is probabilistic.

It's also validated beyond me: 2026 research (the UFMG config-smell catalog, the ETH context-file study) confirms bloated context lowers task success and raises cost, and Anthropic shipped **AutoDream** to prune/merge CLAUDE.md natively — which proves the problem is real *and* hands me my wedge. AutoDream prunes by **heuristic and just does it**. ContextProof prunes by **measured proof and asks first**. That contrast is the whole pitch.

Strategic fit: the judges are Google/Kaggle AI specialists who personally maintain these files, so they feel the pain instantly; and the design is strongest exactly where the rubric is heaviest (70% on implementation, 50 of that on technical quality + meaningful/clever agent use).

---

## 2. What it is

An autonomous agent that continuously tends the context files a coding agent loads every session. It decides on its own what looks like dead weight, **proves** a removal is safe by measuring the coding agent's performance with and without the line, and surfaces only proven, net-positive changes to a dashboard where I approve or decline.

**The autonomy boundary (non-negotiable):**

| The agent does autonomously | The human does |
|---|---|
| Scan config, decide which lines/files are suspect (what, where) | Approve or decline each proposed change |
| Propose the specific edit (how) | Provide the initial eval-task suite (one-time; in production it reads tasks from the repo) |
| Run the eval, measure, iterate until net-positive or give up | — |
| Assemble the recommendation + evidence | — |

The human never tells it *what to fix*. The human only ratifies *proven* changes. That keeps it a real autonomous loop with a safety gate — not a script with a UI.

---

## 3. The verification loop (the core)

Pruning a config line can't break your app — config changes how the *coding agent reasons*, not how your software runs. So the loop verifies a claim about **agent behavior**: *with this line vs without it, does the agent still do its job, for less?*

**One cycle:**

1. **Mutate** — on a throwaway copy, remove a suspect line.
2. **Run** — run the coding agent on a frozen **eval-task suite** (the practice jobs), twice: baseline config vs candidate.
3. **Measure** — compare:
   - **Task success (primary): tests passing.** Objective, believable, quantifiable — the headline evidence.
   - **Task success (fallback): LLM-judge rubric** — for tasks without a test, so it's never blocked.
   - **Token cost** — the savings claim.
4. **Decide** — accept only if quality holds and cost drops. Else the Rewriter tries a gentler edit and re-runs, or drops it.
5. **Surface** — proven change → dashboard card with the diff + the numbers.

**Worked example:** removing `"Always run typecheck after edits"` drops success 4/4 → 2/4 → **rejected, line was load-bearing**. Removing 40 lines of linter-covered style rules keeps 4/4 success at −73% tokens → **surfaced for approval.** The reject case is the point — the loop catches harm instead of rubber-stamping it.

**Eval tasks — where they live:** I hand-write ~4 to start, **each paired with a test**, stored in the repo (e.g. `.contextproof/tasks/`) so the agent discovers them autonomously in production. Auto-deriving tasks from recent commits/issues is a **stretch goal (P1)** — a "look, it bootstraps itself" demo moment, not a dependency of the core.

---

## 4. Scope & boundaries

- **In scope:** `CLAUDE.md`, `GEMINI.md`, `AGENTS.md` to start (GEMINI.md weighted for the Google judges), architected to extend to all context files (skill/subagent docs, `.cursorrules`, etc.).
- **Out of scope:** application code. A config prune is provable (watch the agent); a code deletion is not (passing tests ≠ proof the deleted path was dead — the scary deletions live where coverage is thin). Touching app code would collapse this into a generic refactorer and break the one promise that makes it special.
- **Operation:** prune-only, human-gated, never-delete (removed lines quarantined, not destroyed).

---

## 5. Architecture

```
   repo context files
   + .contextproof/tasks/
          │
          ▼
   ┌──────────────┐   wraps a deterministic linter; flags bloat /
   │  Detector    │   stale refs / cross-file dupes / conflicts.
   └──────┬───────┘   Decides what's suspect — autonomously.
          │ candidate edit (diff)
          ▼
   ┌──────────────┐
   │  Rewriter    │   proposes the specific lean edit
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐   SANDBOX: run coding agent on the task suite,
   │ Eval-Runner  │   baseline vs candidate. Grade: tests (primary),
   │              │   LLM-judge (fallback). Measure tokens.
   └──────┬───────┘   Loop until net-positive or give up.
          │ proven diff + evidence
          ▼
   ┌──────────────┐
   │ Orchestrator │   sequences the above, decides when to stop
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐   dashboard card: diff + numbers
   │ Approval UI  │   (100% → 100% success, −73% tokens). Approve / Decline.
   └──────┬───────┘
          │ approved only
          ▼
   apply to a branch (never main)
```

**Security checkpoint (the differentiator, sits in front of the model):** config file contents are untrusted input. A deterministic pre-LLM pass does PII redaction + prompt-injection detection; anything flagged routes to human review as a security event, never to the model as an instruction. This is graded "Security features" and almost no hackathon agent does it.

---

## 6. Tooling decisions — use only if it earns its place

Honoring YAGNI (and Ponytail): every tool below is justified by a need, not by name-dropping.

| Tool | Verdict | Why / where |
|---|---|---|
| **Google ADK** | ✅ Use | Core framework; orchestrates the 4 agents. → concept: Multi-agent |
| **Gemini via Vertex AI** | ✅ Use | Runtime model for all agents; Google optics; cheap at demo volume |
| **GitHub MCP Server** | ✅ Use | Read repo files, open PRs with approved diffs. → concept: MCP Server |
| **Cloud Run** | ✅ Use | Deploy the dashboard + backend; reproducible. → concept: Deployability |
| **Security checkpoint** | ✅ Use | PII + injection defense + human gate. → concept: Security features |
| **Agent skills** | ✅ Use | Package detection/rewrite as loadable skills. → concept: Agent skills |
| **Pub/Sub** | ⚠️ Optional | Only if you want the *ambient* trigger to be real: commit event → topic → worker. Decouples trigger from work nicely, but a webhook or button is enough for the demo. Add only if P0 lands early. |
| **Vertex AI Agent Engine** | ⚠️ Optional | Managed alternative to hosting the ADK agent on Cloud Run. Extra Google optics, but Cloud Run already covers deployability — don't run both. |
| **Antigravity** | ⚠️ Optional | Show GUI verification in the video = easy 6th concept. Nice-to-have, video-only. |

You clear the ≥3-concept bar with the ✅ rows alone — you hit **5–6**. The ⚠️ rows are upside, not obligations.

---

## 7. Rubric concept coverage

| Concept | Where it shows | Shown in |
|---|---|---|
| Agent / Multi-agent (ADK) | Detector / Rewriter / Eval-Runner / Orchestrator | Code |
| MCP Server | GitHub MCP — read repo, open PRs | Code |
| Security features | PII + injection checkpoint, never-delete, human gate | Code + Video |
| Deployability | Cloud Run with repro docs | Video |
| Agent skills | Detection/rewrite as skills | Code |
| Antigravity (optional) | GUI verification | Video |

---

## 8. The demo

**Build a sample repo** (`contextproof-demo`): a small codebase whose config is deliberately **clean in some areas and messy in others** (linter-covered style rules, a stale file ref, a duplicated convention stated two different ways, one genuinely load-bearing rule). Bundle the 4 eval tasks, each with a test. This is the live testbed and a realistic source for the agent to find work.

**60-second core (the gasp):**
1. Point ContextProof at the demo repo. It scans, autonomously flags suspects.
2. Show a **reject**: it tries removing the typecheck rule, the eval drops to 50%, it refuses — "this line is load-bearing, keeping it."
3. Show an **approve**: it removes 40 lines of linter-covered noise, eval holds 100% at −73% tokens, card pops up with the numbers → I click Approve → PR opens.
4. (P1 stretch) the "create" moment: agent failed a task twice, proposes a one-line rule, success goes 60% → 100%.

Pre-run/cache the eval so the video isn't waiting on live agent runs — that's the #1 demo risk.

---

## 9. 13-day build plan

- **P0 — core, fully demoable:** demo repo + 4 tasks-with-tests → Detector (wrap a linter) → Rewriter → Eval-Runner (tests primary, LLM-judge fallback) → Orchestrator → Approval dashboard → branch-only apply + quarantine. Security checkpoint in front of the model.
- **P1 — if P0 lands early:** auto-derive eval tasks from commits/issues; the "create missing rule" path; Pub/Sub ambient trigger; Antigravity in the video.
- **Always:** clean project-scoped CLAUDE.md, judge-facing comments preserved, **no API keys or passwords in the repo**, CC-BY 4.0 license file.

---

## 10. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Eval runs slow/expensive/flaky | Tiny task suite (4); cache runs for the video; report measured evidence, not "proof" |
| Suite blind spot (prune harms something no task exercises) | Curate tasks to cover the rules most likely to matter; be honest in the writeup that coverage = trust boundary |
| "Seen it" vs AutoDream | Lead every surface with "proven, not heuristic, human-gated"; frame AutoDream as validation + contrast |
| Loop ≈ prompt optimization (DSPy) | Position as a *product* for real repo config files with a human gate, not a new technique |
| Scope creep into app code | Hard architectural line: context files only |

---

## 11. Submission checklist

- [ ] Kaggle Writeup ≤ 2,500 words (title, subtitle, problem, solution, architecture, journey)
- [ ] Cover image + YouTube video ≤ 5 min
- [ ] Public project link / GitHub repo with README (problem, solution, architecture, setup, diagrams)
- [ ] CC-BY 4.0 license; no secrets in code
- [ ] Track selected (Business); click **Submit**, not just Save
