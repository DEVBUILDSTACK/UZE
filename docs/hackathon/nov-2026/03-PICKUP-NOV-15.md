# PICKUP NOVEMBER 15 — How the Project Resumes

**From:** James and DeepSeek
**To:** SoSem
**Effective:** November 15, 2026 (day after hackathon submission)
**Purpose:** What you do when you return to the filed sprint series.

---

## What changes at midnight November 14

The hackathon is over. Sprint 1.5 is closed. The `hackathon/nov-2026` branch is merged to `main`.

**You return to the October 30 sprint series, exactly as filed.**

Nothing about the sprint sequence changes:
- **Sprint 1:** Open, Slices 1–2 in progress
- **Sprint 2:** Ticket rail II + Solana rail, NEAR pairing contracts, `redeemed` writer design, Intent Gateway, Tag Registry, solver policy + Shield, attribution edges, `uze` CLI, Lean evaluation
- **Sprints 3–4:** Stay/flight, three-component bundles
- **Sprint 5:** ServiceTask state machine, ConciergeBrief
- **Sprint 6:** Tuning
- **Sprint 7:** Health, deferrable not droppable
- **Sprint 8+:** Post-launch

---

## What the hackathon added to Sprint 2

The following artifacts on `main` are Sprint 2's starting point:

### From `contracts/near/`

The scaffold is the foundation for the NEAR pairing contracts. Sprint 2 extends it with:
- NEP-171 NFT primitives for ticket credentials
- NEP-177 metadata standard for the pairing asset
- NEP-178 approvals for transferable attendance
- The real typed `Intent`, `Bid`, `Match` structs (not the demo `String` payloads)

### From `services/compose/`

The intent schema, intent API, Chain Signatures settlement, and NEAR AI inference integration are the seeds for Sprint 2's Intent Gateway and inference standards.

Sprint 2 additions:
- Real `classify()` for solver quote freshness
- `SOLVER_WITHDREW` divergence code (new, from R4 port design)
- `Commitment.solver_quote_ref` field for audit trail
- x402/x401 production-grade (replacing Day 5 mocks)

### From `apps/web/`

The read-only pages become the first content of the human UI. Sprint 2 extends with:
- Interactive bidding UI
- User accounts and authentication
- Approval gate UI (tied to x401 verification)
- Full site navigation

### From `docs/diagrams/`

The four diagrams are living documentation. Update them when the architecture changes. They do not get thrown away.

---

## What the hackathon did NOT add

These remain post-hackathon:

- NEAR pairing contracts (NEP-171/177/178) — Sprint 2
- Tag Registry (Rust, testnet) — Sprint 2
- `redeemed` writer design — Sprint 2
- Intent Gateway as a real module — Sprint 2
- Solver policy + Shield — Sprint 2
- `uze` CLI skeleton (Rust) — Sprint 2
- Lean evaluation on pairing invariants — Sprint 2
- Stay/flight rails — Sprints 3–4
- ServiceTask state machine — Sprint 5
- Health vertical — Sprint 7
- Arcium sealed-bid auction — Sprint 9, Nithin required
- Numbers Protocol provenance — Sprint 9+
- rNEAR liquid staking — post-MVP
- Altitude treasury integration — post-MVP
- Delphi information markets — Sprint 9
- Five-tier menu production billing — Sprint 2+
- Medical-recovery hospitality — Sprint 7 + CRE

---

## What you do the week of November 15

### Monday, November 15

**Resume Sprint 1, Slice 2.**

- Eight divergence codes wired to their firing map
- Proxy scoped to commit-path reconciliation only
- `SEAT_TAKEN` reason field populated
- Moderated-listing divergence test designed and queued

**Do not reopen the CRE pivot.** The vertical pivot is ratified. Additive extensions (Intent, Bid, Match, MicroRegion tables) are already on `main` and fold into Sprint 2, not Sprint 1.

### Tuesday, November 16

**Sprint 2 kickoff.**

Sprint 2 content:
- NEAR pairing contracts (NEP-171/177/178)
- `redeemed` writer design
- Intent Gateway as a real module
- Tag Registry (Rust, testnet)
- Solver policy + Shield
- Attribution edges (ticket rail)
- `uze` CLI skeleton
- Lean evaluation on pairing invariants

**The hackathon produced the Intent Gateway's skeleton.** Sprint 2 makes it real.

### Wednesday, November 17 onward

**Sprint 2 continues.** Two-month sprint (Nov–Dec). You have until end of December to complete it.

---

## The two-week checkpoint

**End of November 2026:** Sprint 2 at ~50% complete.

At that point, we review:
- What shipped
- What's at risk
- Whether the Sprint 2 timeline holds against the filed April 1–15 MVP target

**No checkpoint needed before then.**

---

## What to file on November 15

File a status note in `docs/sprints/sprint-2-kickoff.md`:

```markdown
# Sprint 2 Kickoff — November 16, 2026

## What Sprint 1.5 contributed
[Rust contract address, intent schema migration hash, API endpoints, settlement status, inference integration status, HTML pages delivered, diagrams]

## What Sprint 2 inherits
[Enumerate Sprint 2 objectives; note done vs. still-to-do]

## Timeline
- Nov 16 – Dec 31: Sprint 2 execution
- End-Nov checkpoint: ~50% complete
- Jan–Mar 2027: Sprints 3–5
- April 1–15, 2027: Commerce MVP
- First week July 2027: Production

## Standing rules
[Unchanged rules]
```

---

What remains open from before the hackathon

On James:

· Neon provisioning for staging (Route A)
· Ownership (a)/(b) confirmation
· x402/x401 tier A/B metering spec details
· "Lance" clarification
· Four verticals enumeration

On the project:

· services/api redeploy
· Divergence code firing map
· R4 read-through contract's affiliates pinning section

None block Sprint 2 kickoff.

---

One reminder

The hackathon is a bounded delivery. It is not the product. Sprint 2 begins the day after submission, and it is what matters.
