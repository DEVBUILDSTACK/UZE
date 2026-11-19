# The UZEmarkets Development Approach — how the build loop works

**For: the developers we are considering — internal and external.** This README explains how work actually gets built here: who (and what) builds it, how it is verified, and what will be expected of you when you join a scope. Read it before your first assignment.

---

## 1. The shape of the work

Work is organized in **Scopes** — Scope 1 (the Talent platform / UZE Dev Library), Scope 2 (Assessment), Scope 3 (UZE Instant MCP) — each with its own **phased sprint**. Three rules govern everything:

- **Scope → Specification → Sprint.** SoSem proposes a scope; James approves it (his tap is the gate). A specification is then drafted and mutually agreed before anything is built.
- **Phased means sequential.** A phase completes, then the next begins. The next phase does not begin until **all blockers on the current phase are cleared** — the one exception: work from a later phase may be pulled forward when it *enables* the earlier phase to complete. A phase with open blockers is not closed, no matter how much of its build is done.
- **James's gates are absolute.** Nothing publishes, sends, or spends without his explicit tap. Blockers are reported to him the moment they are hit — what is blocked, the actual error, and the exact action that unblocks it.

## 2. The design principle — Agents first

Everything here is developed **Agents-first**: agent-to-agent commerce is the design center, with efficient and effective A2A patterns and data-science best practices observed throughout. The reasoning is the market's own trajectory — Coinbase's founder has put it at 99.999% of financial transactions happening between agents within ten years, and the infrastructure for that world is being built now. In practice: MCP-first surfaces, wallet-bound agent identity, metered calls (x402), an append-only chronicle on every agent action, and the dual-surface contract — the human console is a view over the same API the agents use; autonomous-first for money and execution, human-first for judgment.

## 3. The build loop — who builds

The build lead is **SoSem** (SYS_Administrator of DEVBUILDSTACK, a designated administrative role). SoSem does not build serially. For each phase, SoSem writes **builder assignments** and runs them **in parallel**:

- Each builder is an **instance of SoSem itself** — a child agent spawned for one assignment. It is not a separate product and not a human contractor.
- Every assignment is a written brief with four parts: the **task**, the exact **territory** it may touch (files, repos, surfaces — nothing outside it), the **invariants** it must hold, and the **proof** it must bring back.
- Builders work simultaneously in different territories — tonight, for example, three aspects (Scope 1 placement, Scope 3's MCP core, Scope 2's assessment system) were built in parallel in one evening. This is the efficiency of the loop: aspects complete concurrently instead of queuing.
- Builders commit in small, single-purpose pieces, each with its tests run and its output recorded.

**Verification is separate from building, and SoSem does it personally.** Nothing is reported as done on a builder's word. SoSem re-runs the test suites, compares behavior against the tree as it stood before the change (a pre-existing failure must be *proven* pre-existing, on the base tree, not asserted), and checks the live surface. Reports carry the **actual output** — endpoints, statuses, tallies — never a narrative summary of output.

## 4. Where Copilot fits — accurately

GitHub Copilot is connected as a **supplemental agent tool under SoSem's direction** (the owner's Copilot, via the Copilot CLI). Its proven use so far is codebase mapping and reading across the older core repositories. It can be run in sessions across different repos, and its future work — refactoring, expediting, second reads, including on Assurative V2, Fundio, and the Monolithic — goes through **the same verification gate** as any builder's work.

To be precise, because precision is a house rule: **the parallel builders are not Copilot instances.** The loop's parallelism is SoSem's own. Copilot adds capacity to the loop; it is not the loop.

## 5. Standards every builder is held to

- **Completion is an observable result in the running system** — tests alone do not complete anything (the Kitchen Standard).
- **From-empty replay:** every database migration is proven by replaying the whole chain from an empty database before it is filed. Migrations are frozen artifacts; a filed migration never imports live application source.
- **Statement-identical proof:** a change claimed not to alter behavior is proven identical, never merely asserted.
- **No tautological tests:** a check that mirrors the implementation proves nothing; every check must be able to fail.
- **Filed records govern.** Where memory and a filed record differ, the filed record wins and memory is corrected to match. Corrections are made **by addition** — dated notes that supersede, never silent rewrites.
- **Standard naming:** Scopes are Scope 1, Scope 2, Scope 3, with their own phases. Settled spellings govern (Assuraties / Assuratized; uze / uzing in brand copy). If you are unsure of a name, ask — do not invent one.
- **Nothing of yours enters a repo that shouldn't:** no correspondence, no email drafts, no credentials or tokens, ever. External AI input (e.g. DeepSeek) is design input only — it never authorizes a build; only James's tap does.

## 6. What this means for you

When you are brought into a scope, you will receive a written assignment in the same shape the builders get: task, territory, invariants, proof. Your work will be verified the same way — independently, against the running system, with actual output. Access is staged (prospect → contacted → recruiting → reading room → per-repo source access) and every step is recorded. Work outside your territory, however well-intentioned, is out of bounds: nobody uses access to change anything at their own will — the roadmap tied to your assignment is the work.

That is the whole approach: **scopes tapped by the owner, phases in sequence, builders in parallel, verification independent, and everything reported in actual output.** It completes aspects efficiently because nothing is built twice, nothing is taken on trust, and nothing waits in a queue it doesn't have to.

— SoSem, SYS_Administrator, DEVBUILDSTACK · 2026-11-18
