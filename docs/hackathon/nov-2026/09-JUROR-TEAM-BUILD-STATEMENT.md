# 09 — Build Statement: The Agentic Juror Team + Learning Loop

**Date:** 2026-11-09 · **Branch:** hackathon/nov-2026 · **Specs:** 07 (Assuraties)
and 08 (Juror Team) · **Commits:** `157f70e` (spec 07) · `225ad20` (claim model +
migration `4ab128b8c311`) · `f0dbe63` (claims API + juror) · `89de363` (claims
tests) · `f6e2079` (spec 08) · `74f11d6` (precedents, scorecards, learning feed)
· `238d110` (juror-team tests) · Diagram 06 (`5166096`) · **Suite: 183 passed** ·
Demo dry run complete, Beat 7 gate OK.

---

## 1. The problem we are solving

Lending against income real estate runs on numbers nobody has to defend.
A seller or advisor states a property's operating expenses — monthly,
quarterly, annual, historical — in a document; a financing partner relies on
the document; if the numbers were wrong, the discovery arrives after the
money moves. The specific failures:

- **No standing.** A stated number has no claimant bound to it by anything
  stronger than a signature on a PDF.
- **No test.** There is no standard way for a rival, an analyst, or an agent
  to dispute a specific figure and force it to be proven.
- **No memory.** Each underwriting starts from zero. Proven expense truth
  from the last deal in the same micro-region does not inform the next one.
- **No accountable judge.** Where verification exists, it is a black box:
  no public record of who or what judged, on what evidence, or how often
  the judge has been right.

Assuraties (spec 07) solves the first two: claims are issued with a claimant
and a bond, challenged by counter-bond, judged by an attested AI juror, and —
once confirmed in resolution through the market parties — **Assuratized**,
the reliance grade served to financing partners through the Reliance API.

The Juror Team + Learning Loop (spec 08) solves the second two: **memory**
and **an accountable judge**.

## 2. Our process

Built inside Sprint 1.5's standing discipline, in one day, on top of the
ratified packet (D1–D11) without reopening it:

1. **Scope → spec → build.** Spec 07 first (claim > judge > resolved for
   properties), shipped and tested; then spec 08 as a separate, additive
   layer — no claim-lifecycle change, no new migration.
2. **Verification standards held.** Full suite green at every step
   (164 → 178 → 183); from-empty replay for the one migration (spec 07's
   `4ab128b8c311`, verified twice); the demo dry run completes end to end;
   no tautological tests — the precedent test asserts the actual prompt a
   capturing client received, and the feed test watches precedent counts
   accumulate 0 → 1 → 2 across real resolutions.
3. **Honesty as a build rule.** The juror never fabricates: with NEAR AI
   inference unavailable (org credits pending — HTTP 402 on the live key),
   judgments record "unavailable" and claims rest in UNDER_RESOLUTION.
   Nothing in the code, the specs, or this statement claims a live attested
   receipt that has not occurred.

## 3. The code — what was built

**Spec 07 layer** (`services/compose/src/assuraties.py`, `src/juror.py`):

- `claim` table (migration `4ab128b8c311`): claimClass (RWA · HICRE_ASSET ·
  HICRE_PERIOD), periodKind (MONTHLY · QUARTERLY · ANNUAL · HISTORICAL_TOTAL),
  statement, claimedValue, claimantEntityId, bondAmount (mock units — no real
  funds move; the Iron Rule), status (ISSUED · CHALLENGED · UNDER_RESOLUTION ·
  RESOLVED_TRUE · RESOLVED_FALSE · ASSURATIZED), confidentialTier (STANDARD ·
  ARCIUM), jurorReport and challenge records. EventLog rows for every
  transition.
- Endpoints: `POST /claims` · `GET /claims/{id}` · `POST /claims/{id}/challenge`
  · `POST /claims/{id}/judge` · `POST /claims/{id}/finalize` ·
  `GET /reliance/claims` (x401-gated; Assuratized claims only, with the full
  resolution trail and the ASSURATIZED / ASSURATIZED @ARCIUM marks).

**Spec 08 layer** (same files, additive):

- **Precedent selection** (`_select_precedents`): before judging, the system
  selects Assuratized claims whose Intent shares the claim's micro-region —
  self excluded, resolution-time descending, cap 3.
- **Precedent rendering** (`juror.render_claim_as_prompt`): precedents enter
  the deterministic juror prompt in a delimited PRECEDENTS block (statement,
  claimed value, outcome, withstood flag). Same claim + same precedents =
  same prompt: the reproducible (REE) leg now covers claim *and* memory.
- **Juror identity on every report**: `juror` = the model actually used
  (the C-3 fallback model when the fallback fires), plus `precedentsUsed`
  (ids in render order), recorded on every outcome including unavailable.
- **Scorecards** (`GET /api/v1/jurors`, public): per juror — judgedCount,
  upheldCount, refutedCount, withstoodCount, unavailableCount — derived from
  finalized outcomes. No new storage; derivation from the claim/EventLog
  record.
- **Learning feed** (`GET /api/v1/learning/recent`, public): terminal
  learning events, newest first — claimId, outcome, juror,
  precedentsUsedCount, comparableAdded (true exactly when a claim became
  Assuratized and entered the comparable ledger), claimant, resolution time.

## 4. The value it creates

**For agentic users** (external agent systems working through UZEmarkets):

- A machine-readable trust surface: an agent can issue claims, challenge
  claims, judge whom to trust (claimant track records, juror scorecards),
  and consume only Assuratized data through the Reliance API — the full
  loop without a human in it.
- Precedent is an API-visible asset: an agent pricing work in a micro-region
  can read what the system has already proven there.

**For human users** (owners, brokers, advisors, analysts):

- Their numbers stop being documents and become positions with a public
  record: claims that resolve build a track record that lowers their cost
  of being believed on the next deal.
- The judge is accountable to them too: scorecards show which juror seats
  perform, in the open.

**For financing partners** (private lenders, banks, institutions):

- The Reliance API returns due-diligence-grade evidence: the claim, the
  bond, the claimant's record, the juror's record, the precedents the
  judgment stood on, and the resolution trail — an underwriter's file,
  assembled by the market itself.
- Every financing decision made on Assuratized data feeds back: settled
  deals generate period actuals, which become the next precedents.

**For UZEmarkets:** the compounding asset is the comparable ledger plus two
reputation graphs (claimants, jurors) that no competitor can fork — the
mechanism can be copied; the accumulated, publicly verifiable record cannot.

## 5. Pathways — private/public API pipeline and partnerships

**Public pipeline (open to scrutiny):** the read surfaces — juror
scorecards, the learning feed, micro-region pulses, talent/spec projections —
are public by design. The system's learning is *open to public scrutiny*:
anyone can watch resolutions land, precedents accumulate, and juror records
move, and can re-derive every scorecard from the underlying claim record.
**This is a transparency posture, not a license**: the implementation is
UZEmarkets' proprietary code (456iP); scrutiny is invited, reuse is not
granted. (The Credence mechanism that inspired spec 07 is MIT-licensed and
is credited as such; the team-and-learning layer is our own design.)

**Private pipeline:** the Reliance API is the partner surface — x401
identity-gated today, metering-ready (x402 rails already in the stack) —
through which financing partners consume Assuratized claims inside their
own underwriting. The DevPartner portal is the data-supply counterpart:
partners (Agro Digital, BDCS, Effatha class) ingest spatial/agricultural
data through the staging-gated API that feeds GIRA's A/NR/D claims.

**Partnership pathways, in order of proximity:**

1. **Financing partners** — Reliance API pilots against live HiCRE
   assessments (South Florida, Baltimore–Washington) and A/NR/D assessments
   (southern Brazil, Uruguay, Paraguay).
2. **Data partners** — DevPartner ingestion feeding claim supply; resolved
   claims return as the partner's own credibility record.
3. **Juror-seat partners** — model providers and agent systems whose jurors
   earn public scorecards; a seat with a proven record is a distributable
   credential, and seat admission policy is the governance surface.
4. **Confidential-tier partners** — the Arcium integration (ASSURATIZED
   @ARCIUM) for sealed-bid and reverse auctions, at the ParleySwap adapter
   scaffold, for assets whose claims or bids cannot be public.

## 6. Known limits (stated, not hidden)

- No live attested inference yet: NEAR AI org credits are pending (402);
  all juror behavior is verified through the structural test path.
- Bonds are mock units in the hackathon build; NEAR anchoring of claims and
  NEAR Intents bond funding are spec-07 design, not shipped code.
- Scorecards derive on read from the claim record — correct at this scale,
  a materialization candidate at volume.
- Precedent selection is micro-region + recency only (cap 3): no
  asset-class or period-kind weighting, no staleness decay, and the
  poisoning surface (seeding favorable precedents) is currently priced
  only by the bond. These are the open design questions, listed for review.
