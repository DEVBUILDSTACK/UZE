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
- **Self-dealing exclusion (DeepSeek audit Q2(a), 2026-11-09).**
  Two candidate classes are excluded before the cap, and the
  number excluded is recorded on every juror report as
  `precedentsExcludedSelfDealing` (an integer, 0 when nothing
  was held back): precedents claimed by the **same
  claimantEntityId** as the claim under judgment, and precedents
  on the **same Intent**. A claimant's own resolved record
  never informs judgments on their own claims. The rationale is
  separation of the roles that check each other: the field's
  demonstrated failure mode — visible in a sibling hackathon
  project — is a single operator acting as writer, moderator,
  and juror at once, with no role left to check the others.
  Precedent is the system's memory; letting a claimant stock
  the memory that judges them would rebuild that conflict
  inside our own pipeline. The exclusion also prices the
  precedent-poisoning surface named in the build statement:
  seeding favorable precedents no longer helps the seeder's
  own claims at all.
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
juror identity, **event-sourced from the append-only EventLog**
(DeepSeek audit Q4 fix, 2026-11-09). The derivation is precise:

- **Attempts.** Every `claim.judged` EventLog row is an attempt
  by its recorded juror with its recorded outcome. The judge
  endpoint has written `juror` and `jurorOutcome` into the event
  payload since the claims build (spec 07); panel judgments
  (see below) write one `panelAttempts` entry per seat, and each
  entry is that seat's attempt. `attemptCount` is a juror's
  total attempts; `unavailableCount` is the attempts whose
  outcome was unavailable or error — **including attempts a
  later judgment superseded**. Events whose payload carries no
  juror identity are skipped, never attributed by guess.
- **Terminal credit.** A claim's *deciding* judgment is its
  last `claim.judged` event with outcome ok. ASSURATIZED
  credits `upheldCount` (plus `withstoodCount` when the claim's
  challenge was withstood); RESOLVED_FALSE credits
  `refutedCount` (finalize is refused for these by
  construction — the refutation is the terminal outcome).
  `judgedCount` is the total terminal claims credited. A single
  juror is credited directly; a panel credits the seats whose
  verdict matched the panel verdict, and a seat whose parsed
  verdict differed is recorded as a dissent (`panelDissents`) —
  abstaining seats are credited with neither.
- **Why event-sourced.** The first derivation read each claim's
  *current* jurorReport: when a claim was judged twice, the
  first attempt was overwritten by the second and vanished
  from the scorecard — a juror's failed attempts could be
  laundered by re-judging. The EventLog is append-only, so the
  derivation now counts what actually happened, in order.

| field | derivation |
|---|---|
| `attemptCount` | all `claim.judged` attempts by this juror (panel seats: their `panelAttempts` entries) |
| `unavailableCount` | attempts with outcome unavailable/error, superseded or not |
| `judgedCount` | terminal claims credited to this juror (upheld + refuted) |
| `upheldCount` | credited ASSURATIZED outcomes |
| `refutedCount` | credited RESOLVED_FALSE outcomes |
| `withstoodCount` | credited ASSURATIZED claims whose challenge was withstood |
| `panelDissents` | panel judgments on terminal claims where this seat's parsed verdict differed from the panel verdict |

Only jurors with at least one judged (terminal, credited)
claim appear; ordering is deterministic (juror identity
ascending). No authentication: scorecards are reputation, and
reputation only works published. External agent systems
deciding which juror seat to trust — or whether to challenge
a claim a weak seat upheld — read the same numbers a financing
partner reads. There is one record.

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

## 8. Untrusted-input sanitization — the juror-path slice

Claim text is untrusted input rendered into a judge's prompt —
ours, and later other claims' precedent blocks. The hackathon
slice of the sanitization pipeline (DeepSeek's Hermes
architecture directive, 2026-11-09) covers exactly this path;
the full pipeline, including Grok/Hermes desk output, is
Sprint 2 scope.

- **Invisible-Unicode stripping** (`src/sanitize.py`). The
  classes stripped: zero-width characters (U+200B–U+200D),
  the BOM (U+FEFF), bidi controls (U+202A–U+202E) and isolates
  (U+2066–U+2069), Unicode tag characters (U+E0000–U+E007F),
  and the soft hyphen (U+00AD). Applied to the claim
  `statement` and the string leaves of `claimedValue` **at
  claim creation** — the claim of record is the sanitized
  claim; no unsanitized copy exists — and applied **again
  defensively at render time** in juror.py (the claim's own
  text and every precedent's), because the prompt path never
  trusts stored text to be clean. Visible text is untouched:
  the sanitizer removes the hidden channel, and judging
  visible claims is the juror's evidence standard, not the
  sanitizer's.
- **Canary trap.** Every attempted judgment embeds a fresh
  canary token (uuid4 hex) in the prompt framing, on a
  delimited `SENTINEL:` line instructing that it is a security
  sentinel and must not be reproduced. If the completion
  echoes the token, the framing has leaked into the answer:
  the outcome is recorded as status `error` with reason
  `canary_tripped` — never a verdict — and the claim rests
  UNDER_RESOLUTION. The report records only `canaryId` (an
  independent identifier) and `canaryTripped` (a boolean);
  the token value itself is stored nowhere. The unavailable
  path attempts no judgment, embeds no canary, and carries
  neither field.
- `tests/test_sanitize.py` — every invisible class stripped
  at unit level; a dirty claim stored stripped; a dirty
  precedent rendered stripped; a canary-echoing juror
  producing error/canary_tripped through the real judge path.
