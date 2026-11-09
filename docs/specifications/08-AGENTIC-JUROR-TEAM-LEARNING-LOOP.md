# 08 — The Agentic Juror Team + Learning Loop

**Status:** built in Sprint 1.5 on top of spec 07 (Assuraties),
same branch, same Iron Rule. This note designs — and the code in
`services/compose/src/juror.py` / `src/assuraties.py` implements —
the layer that turns one attested juror into an **agentic team**:
many juror seats, public scorecards, precedent-aware judgment,
and a learning feed any external agent system can read.

The claim > judge > resolved mechanism and its Credence lineage
are spec 07's. The team-and-learning layer in this note — juror
seats with accumulating public scorecards, precedent as the
system's memory, and the learning feed as an external surface —
is UZEmarkets' own design.

---

## 1. The juror is a team, not a model

Spec 07 shipped one juror: the attested NEAR AI completion. But
nothing in the pipeline binds judgment to a single model. A
**juror seat** is identified by the model string actually used
(the C-3 fallback model when the fallback fires) — recorded on
every juror report as `juror` — together with the transport that
carried it (SDK, or the C-4 REST route with SDK verification
alongside). Different seats can judge different claims; seats
can be added, swapped, or retired without touching the claim
lifecycle, because the lifecycle trusts the *report shape*, not
a particular model.

What makes seats a team rather than a rotation is that their
work is **scored, in public, from outcomes** (§3) and **informed
by shared memory** (§2). A seat that judges well accumulates a
record financing partners and external agents can price. A seat
that judges badly cannot hide: its refutations and its overturns
are in the same record.

## 2. Precedent — Assuratized claims are the system's memory

Every Assuratized claim is resolved truth: a statement about an
asset or a period's total operating expenses that was bonded,
judged, and confirmed in resolution through the market parties.
That record is the comparable ledger of spec 07 §9. This note
makes it operational inside the judgment itself:

- **Selection.** Before the juror runs on a claim, the system
  selects precedents: claims in status ASSURATIZED whose Intent
  shares the claim's Intent micro-region — the same market —
  excluding the claim itself, ordered by resolution time
  descending (claim id breaks ties), capped at 3.
- **Rendering.** The precedents are rendered into the juror
  prompt in a clearly delimited **PRECEDENTS** block: statement,
  claimed value, and resolution outcome, including whether the
  precedent withstood a challenge. The rendering is part of
  juror.py's deterministic prompt: same claim + same precedents,
  same prompt — the REE leg of spec 07 §4 is preserved, now over
  claim *and* memory.
- **Record.** The juror report records `precedentsUsed` — the
  precedent claim ids in the order rendered — on every outcome,
  including unavailable/error. Anyone re-judging the claim can
  see exactly which settled record the juror was shown.
- **Discipline.** Precedents inform; they never decide. If
  inference is unavailable or errors, the claim stays
  UNDER_RESOLUTION with the reason recorded, exactly as spec 07
  requires. A precedent is never a verdict, and no code path
  converts one into one.

The loop this closes: resolutions become precedents, precedents
sharpen judgments, sharper judgments produce better resolutions.
The system's memory is its resolved claims — nothing else is
learned from, and nothing is learned silently: every judgment
carries the ids of the memory it used.

## 3. Scorecards — GET /api/v1/jurors

A public, read-only projection (the Day 6 pattern: derived on
every call, nothing stored, nothing invented). One scorecard per
juror identity, built from the claims that juror judged:

| field | derivation |
|---|---|
| `judgedCount` | claims that reached a terminal resolution under this juror: ASSURATIZED + RESOLVED_FALSE |
| `upheldCount` | finalized ASSURATIZED on this juror's UPHELD verdict |
| `refutedCount` | RESOLVED_FALSE on this juror's REFUTED verdict (finalize is refused for these by construction — the refutation is the terminal outcome) |
| `withstoodCount` | ASSURATIZED claims carrying a challenge this juror's verdict withstood |
| `unavailableCount` | claims currently resting on this juror's unavailable/error report — attempts recorded on the claim and not yet superseded by a successful judgment |

Only jurors with at least one judged claim appear; ordering is
deterministic (juror identity ascending). No authentication:
scorecards are reputation, and reputation only works published.
External agent systems deciding which juror seat to trust — or
whether to challenge a claim a weak seat upheld — read the same
numbers a financing partner reads. There is one record.

## 4. The learning feed — GET /api/v1/learning/recent

The system's terminal learning events, newest first
(`?limit=` defaults to 20, capped at 50). Two event kinds are
terminal for a claim, and the feed is built from exactly those
EventLog rows, joined back to the claim:

- `claim.finalized` — the claim became **ASSURATIZED** and
  entered the comparable ledger;
- `claim.judged` with outcome **RESOLVED_FALSE** — the
  refutation is terminal (finalize is refused for it), so the
  judgment event is its learning event.

Each entry carries only what the record holds: `claimId`,
`outcome` (ASSURATIZED | RESOLVED_FALSE), `juror`,
`precedentsUsedCount` (from the claim's juror report),
`comparableAdded` (true exactly when the outcome is
ASSURATIZED — the claim entered the comparable ledger),
`claimantEntityId`, and `resolvedAt` from the claim row.

This is the surface an external agent system — or a human desk —
watches to learn how the market is resolving: which micro-region
just gained a comparable, which claimant's claims keep failing,
which juror's recent judgments leaned on how much precedent.
Engagement stays on the existing surfaces: external agents
issue and challenge claims and read reliance material through
the spec 07 endpoints; the scorecards and this feed are how
they aim.

## 5. What is deliberately NOT in this build

The Grok / Hermes / KVM stacks are **out of the hackathon
build**. They are the comms and desk plane — the Hermes harness
on the Hostinger KVM, the native gateway into the Buzz Rooms
and the Technocore (flopsai.xyz) messaging, Grok Voice on the
KVM2 concierge — concerned with sensing, messaging, and human
engagement channels, not with the claim ledger. Bolting them
onto the resolution core inside a deadline build would couple
the system's memory to its loudest channel. The integration
point is designed instead: those stacks engage Assuraties
exactly the way any external agent system does — through the
claim, challenge, and reliance surfaces, reading the scorecards
and the learning feed — when James scopes that work after the
hackathon. Nothing in this note requires them, and nothing here
blocks them.

## 6. Invariants carried over, unchanged

- **The Iron Rule (spec 07 §7).** No transition executes a
  financial transaction. Bonds are mock units recorded on the
  claim; scorecards and the feed move no value; settlement stays
  USDC on Solana.
- **Honesty of outcomes.** A juror that cannot run records
  unavailable/error with its reason; no verdict is fabricated,
  by precedent or otherwise.
- **Terminology.** Claims as issued and standing are
  **Assuraties** (plural-only). Claims confirmed in resolution
  through the market parties are **Assuratized**. The
  confidential tier's mark remains **ASSURATIZED @ARCIUM** (a
  data flag in this build, per spec 07 §6). The layer this runs
  on is **AssurativeV2**.
- **No new storage.** This layer is derivation over the claim
  table and the EventLog: no migration, no counters, no cache
  that can drift from the record.

## 7. As built

- `src/juror.py` — `juror` identity on every report (the model
  actually used); PRECEDENTS block in the deterministic prompt
  rendering; `precedentsUsed` on every outcome.
- `src/assuraties.py` — precedent selection at judge time;
  `GET /api/v1/jurors`; `GET /api/v1/learning/recent`.
- `tests/test_juror_team.py` — precedent injection proven
  against a capturing client (same micro-region in, different
  micro-region out), scorecard math, feed ordering and limits,
  and the unavailable path's absence from the scorecards.
