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
claim — or at least one recorded panel dissent (§9), which is
itself a reputation fact — appear; ordering is deterministic
(juror identity ascending). No authentication: scorecards are
reputation, and reputation only works published. External
agent systems deciding which juror seat to trust — or whether
to challenge a claim a weak seat upheld — read the same
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
  rendering; `precedentsUsed` on every outcome; defensive
  re-sanitization at render (§8); the canary trap (§8);
  panels — `panel_models` / `judge_claim_for_model` /
  `judge_panel` (§9).
- `src/assuraties.py` — precedent selection at judge time with
  the self-dealing exclusion and its count (§2); contested
  claims routed to the panel (§9); event-sourced scorecards at
  `GET /api/v1/jurors` (§3); `GET /api/v1/learning/recent`;
  panel attestation anchors recorded at verdict time (§10).
- `src/sanitize.py` — invisible-Unicode stripping for the
  juror path (§8).
- `src/models.py` + migration `c41a9e72d5b0` — the
  `attestation_anchor` table and `anchor_status` enum (§10);
  `src/near_client.py` — `anchor_attestation` under the
  standard chain gate.
- `tests/test_juror_team.py` — precedent injection proven
  against a capturing client (same micro-region in, different
  micro-region out), the self-dealing exclusion, scorecard
  math (incl. the event-sourcing test: superseded attempts
  counted), panel majority / no-majority / fallback, anchor
  recording with recomputed digests, feed ordering and limits,
  and the unavailable path's absence from the scorecards.
- `tests/test_sanitize.py` — §8's pins (see below).

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

## 9. Panels for contested claims (DeepSeek audit Q3)

A challenged claim is a contested claim, and a single juror is
the wrong shape for a contest. Since this amendment, judging
routes by contention: **unchallenged claims keep the
single-juror path unchanged; a claim carrying a challenge is
judged by a panel** (`juror.judge_panel`).

- **Seats.** Up to 3 juror seats, from env
  `JUROR_PANEL_MODELS` (comma-separated) when set, else the
  primary model plus the C-3 fallback model — deduped. A panel
  requires at least two **distinct** seats; below that, judging
  falls back to the single-juror path and the report carries
  `panelNote: "panel unavailable: fewer than two seats
  configured"` — the fallback is recorded, never silent.
- **Independence.** Each seat judges with the SAME
  deterministic prompt (precedents included): seats differ by
  model, not by evidence. A seat is judged by
  `juror.judge_claim_for_model` — the seat's model used
  exactly, with no fallback chain, because silently judging
  with a different model would falsify the seat's record.
  Each seat embeds its own canary (§8).
- **Verdict.** The panel verdict is the strict majority of
  seats that returned a parsed verdict. Unavailable/error
  seats abstain. A tie — or every seat abstaining — is not a
  verdict: the report is an error with reason
  `panel_no_majority`, and the claim rests UNDER_RESOLUTION.
  Finalize consumes the panel verdict exactly as it consumes
  a single verdict.
- **Record.** The claim's juror report carries `panel`,
  `panelVerdict`, and `panelReports` (every seat's full
  report, in seat order); the `claim.judged` event carries
  `panelAttempts` (per-seat juror/outcome/verdict), which is
  what the event-sourced scorecards (§3) read: seats whose
  verdict matched the panel outcome are credited with the
  terminal outcome; a seat whose verdict differed records a
  **dissent** (`panelDissents`); abstentions record neither.
- **Why panels, from the field.** The sibling project this
  design answers runs a single juror with an escalation-only
  council as its only check. A panel of independent models,
  scored per seat in public, is the stronger default for the
  claims that are actually disputed — which are precisely the
  claims whose judgments carry consequences.

## 10. On-chain attestation anchoring (DeepSeek audit, item 4)

The pattern worth taking from the field: an attestation hash
anchored next to the artifact it attests, with every revision.
When a panel reaches a verdict, compose records one
**attestation anchor** per verdict-returning seat:
`attestationHash` is the sha256 of the seat's report exactly as
recorded on the claim (canonical JSON — sorted keys, compact
separators), stored on the new `attestation_anchor` table
(migration `c41a9e72d5b0`: claimId FK, seat juror, hash,
nearTxRef nullable, `anchor_status` enum, createdAt), and
exposed on the claim as `attestationAnchors`. A panel with no
verdict anchors nothing.

The status is the honest outcome of the attempt, and anchoring
**never blocks or fails the judgment**:

- `DISABLED` — the chain gate (`COMPOSE_NEAR_CHAIN`) was off.
  This is the recorded outcome in the test environment and
  the demo dry run.
- `UNAVAILABLE` — the gate was on but the chain call failed;
  `reason` says why.
- `SUBMITTED` — a chain transaction carries the hash;
  `nearTxRef` holds its hash.

**Anchor method (DeepSeek §11.1, built 2026-11-09).** The
contract now exposes `anchor_attestation(claim_id, juror,
attestation_hash)` plus the `get_anchors(claim_id)` view
(contracts/near/uzemarkets-talent/src/lib.rs). Anchors live in
raw storage keys (`anchor-rec:` / `anchor-idx:` prefixes), NOT
in the root contract state — the state struct is exactly as
first deployed, so the redeploy needed no state migration and
the marketplace methods are untouched (verified post-redeploy:
`post_intent` still returns its value, `get_matches` still
answers). Anchoring is append-only and idempotent per
(claim, hash). Compose calls it through the same gated
near_client path as every chain call.

**Live proof (testnet, 2026-11-09).** Contract redeployed
(tx `BGt1KFLREJT7VPcEfP2mHPRVWd8jDGL6o7MWcMsYnT3S`). One
challenged claim (panel seats stubbed — inference is
credit-blocked; the anchor is what was proven) was judged to a
panel verdict; all three seats anchored SUBMITTED (claim
`b57b4260-997f-4cbe-bf84-46d8a9ca0a0d`; txs
`21kJP5KVsRyRNp9VJPeqNMFfbJPCCcrXcmn3U7xqPZvk`,
`23ycn3vyXNWvGBqFYkCBW9oDbghTonfAPdUFuZBERijm`,
`BtvizxwWpsfHdrjpgcuCQHvdfmxD4BMz97xAyU4oQdkQ`), and the
on-chain `get_anchors` read-back matched the
`attestation_anchor` rows' digests per juror — each digest
independently recomputed as the sha256 of the seat's report
as recorded on the claim. SUBMITTED is no longer a code path
waiting for a method; it is the recorded, verified outcome.
