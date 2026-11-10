# 07 — ASSURATIES: the Claim → Judge → Resolved Extension

**Status:** Sprint 1.5 build (NEAR Hackathon, Nov 2026). Implemented in
Compose as `services/compose/src/assuraties.py` + `src/juror.py`,
table `claim`, Alembic revision `4ab128b8c311`.

**Provenance and license:** this extension interprets and improves
the claim-market mechanism of **Credence**
(https://github.com/Paramchoudhary/Credence), a fellow NEAR
Hackathon build released under the MIT License. Credence's core
moves — every factual claim is a priced market; an AI juror reports
first with an attestation; anyone can overrule the juror by posting
an escalating bond; big bonds escalate to a council; claims finalize
and settle — are adapted here, not copied: no Credence code is
vendored, and the design below is written against UZEmarkets'
own rails (Compose, the AssurativeV2 trust layer, NEAR, Arcium).
Credence is credited here per its MIT terms and because the
attribution is true.

---

## 1. What this is

Financial packages in the Americas' income-real-estate markets —
advisory analyses and seller financials — are PDFs full of numbers
nobody stands behind in any checkable way. This extension turns the
load-bearing numbers into **claims**: discrete, attributable
assertions that are priced, bonded, judged, and resolved on
evidence, and whose resolution record a financing partner can rely
on through the Reliance API.

The claim lifecycle is the Credence pipeline, mapped to properties:

```
claim ──issue──▶ ISSUED ──challenge (bond)──▶ CHALLENGED
                   │                            │
                   └────────── judge ───────────┴──▶ UNDER_RESOLUTION
                                                            │
                              juror reports (attested)      │
                                   ┌────────────────────────┤
                                   ▼                        ▼
                            RESOLVED_TRUE              RESOLVED_FALSE
                                   │
                     finalize (authorization ref) │
                                   ▼
                             ASSURATIZED
```

If the juror cannot run (no key, org credits blocked, transport
failure), the claim rests at UNDER_RESOLUTION with the reason
recorded. A verdict is never fabricated: the juror's outcome states
are exactly inference's — `ok | unavailable | error` — and only
`ok` moves a claim to a resolved state.

## 2. Claim classes — mapped to properties

Every claim attaches to a marketplace Intent (`intentId`) and
carries a claimant Entity (`claimantEntityId`, an AssurativeV2
trust-layer Entity id — a plain string reference, never a foreign
key out of this database, per the R4 rule).

| Class | What the claim is about | Examples |
|---|---|---|
| `RWA` | A real-world asset as such | title/encumbrance assertions, existence and condition of the asset, subterranean context on A/D/R tracks |
| `HICRE_ASSET` | A hospitality / income CRE asset | door count, brand affiliation, occupancy history, acquisition stage |
| `HICRE_PERIOD` | **One accounting period of one HiCRE asset: its full P&L — revenue, operating expenses, and net operating income (see §2.1)** | monthly / quarterly / annual total operating expenses, and historical total operating expenses in total; room revenue and occupancy for the period; net operating income |

`HICRE_PERIOD` claims REQUIRE a `periodKind`
(`MONTHLY | QUARTERLY | ANNUAL | HISTORICAL_TOTAL`); non-period
claims must NOT carry one. Period claims are the sharp end of the
design: operating-expense projections are the numbers financing
partners actually underwrite against — and, per §2.1, the revenue
side and the aggregate are claimable on the same terms.

`claimedValue` is the claim's payload as JSON — for a period claim,
the expense lines and their total; for an asset claim, the asserted
facts. `bondAmount` is the claimant's skin in the game, in mock
units in this build: bonds are recorded, never moved (see §7).

### 2.1 The full P&L — revenue, expenses, and the aggregate

*Scope expansion (directive, 2026-11-10). Documentation only:
`claimedValue` is JSON, so no schema or code change is required for
the Nov 13 merge; what this sharpens is prompt engineering and
evidence routing in Sprint 2.*

"P&L" in this specification means the complete financial truth of
the asset — both sides, and their combination. A claim may assert
a fact about:

- **Revenue / income** — e.g., actual room revenue, occupancy
  rates, crop yield revenue, land lease income.
- **Expenses / operating costs** — e.g., labor, maintenance, brand
  fees, fertilizer costs, extraction costs.
- **The aggregate P&L** — net operating income, or the period's
  total financial performance.

For `HICRE_PERIOD`, this supersedes the expenses-only reading of
the class table: a period claim may carry revenue lines, expense
lines, or the aggregate, for a monthly / quarterly / annual period
or as a historical total. For `HICRE_ASSET`, revenue-performance
facts (occupancy history is the filed example) are asset claims on
the same terms. For `RWA` claims on the A/D/R tracks, yield
revenue, lease income, and input / extraction costs are the
corresponding sides.

The Juror Team evaluates the side in dispute, with the evidence
schema that matches it — revenue ledgers for a revenue assertion,
expense receipts for an expense assertion (SURA judges HiCRE
claims; GIRA judges ANRD claims). A contested claim, stated
plainly, is one of three things: a **revenue overstatement**, an
**expense understatement**, or a **disagreement over the final
net income**.

## 3. Terminology — Assuraties / Assuratized

James's coinage (2026-11-09), built from the `ASSUR-` root of
**AssurativeV2** without using the layer's full name, so that
product and litigation risk around the claim layer never touches
the AssurativeV2 brand or the AssurativeV2 core layer UZEmarkets
is built on. (SURETY is a legal term of art and is not used;
ASSURETY and ASSURITY were checked and are taken by existing
firms.)

- **Assuraties** — the present-use branding for claims as issued
  and standing. **Plural-only**: there is no singular form. It is a
  branding term, never a URL or domain.
- **Assuratized** — the past-use form: claims **confirmed in
  resolution through the market parties**. The juror reports;
  the market parties confirm — the challenge window lapsing
  unchallenged, or the claim withstanding a challenge, is the
  confirmation. Reliance-grade claims are the Assuratized ones.
  In the Compose schema this is the terminal claim status
  `ASSURATIZED`, reached only through the guarded finalize step
  (§5), which is where the confirming party's authorization
  reference records the confirmation; a claim resolved FALSE is
  never confirmed and never becomes Assuratized.

## 4. The REE/TEE environment

The resolution environment is designed to be simultaneously
**reproducible** and **trusted** — the two properties a lender's
credit committee needs before it relies on a machine judgment:

- **TEE (trusted execution) leg — the juror.** The judge is NEAR AI
  Cloud attested inference: the same enclave stack Compose already
  uses for agent property analysis (`src/inference.py`), driven by
  `src/juror.py`. The juror's report on a claim records the model,
  the completion id, and the verification result (signature kind /
  attestation receipt) **when genuinely present**. Where the SDK
  path cannot run, the C-4 Option A REST route runs with SDK
  verification alongside, and the transport note is attached only
  when verification actually succeeded. Where inference cannot run
  at all — the known NEAR AI org-credit block (HTTP 402) is the
  live example — the report records `unavailable`/`error` with the
  reason, and the claim does not resolve.
- **REE (reproducible execution) leg — deterministic rendering.**
  The juror sees exactly one prompt, rendered deterministically
  from the claim record (`juror.render_claim_as_prompt`: same
  claim, same prompt, byte for byte). The prompt, the model, the
  completion id, and the verification outcome are all recorded on
  the claim and in the append-only EventLog, so any later party can
  re-run the same claim through the same rendering and compare.
  Reproducibility is a property of the recorded trail, not a claim
  about the model's internals.
- **Ledger of record — NEAR blockchain.** In the full design the
  claim, its bond, the juror's report, and the resolution are
  anchored on NEAR: NEAR is the intent / identity / agent-control
  plane of the UZEmarkets architecture, and the Compose row mirrors
  the chain record (the `chainIntentRef` precedent). In this
  Sprint 1.5 build the Compose database row plus its EventLog trail
  are the operative record; the chain anchor is the filed design,
  stated as such.
- **Bond funding — NEAR Intents (design).** In the full design,
  claimant and challenger bonds are funded cross-chain through
  NEAR Intents (the 1Click route Credence also uses for funding):
  a bond posted in any supported asset lands as the claim's bond
  balance. Intents has no testnet, so on testnet the route is a
  dry-run quote; in this build bonds are mock units recorded on
  the claim — no funds move in any case (§7).

## 5. The pipeline, step by step (as implemented)

1. **Issue** — `POST /api/v1/claims` validates the claim (class /
   period rules; the Intent must exist → 404; `claimantEntityId`
   required) and records it `ISSUED` with an EventLog row
   `claim.issued`.
2. **Challenge** — `POST /api/v1/claims/{id}/challenge`, lawful
   only from `ISSUED` (single-step guard; any other state → 409).
   The challenger names its Entity and posts a bond (mock units).
   Recorded on the claim and as `claim.challenged`. One challenge
   per claim in this build: a second challenge is a state error,
   not a bidding war (Credence's escalating-bond ladder is the
   full design; see §8).
3. **Judge** — `POST /api/v1/claims/{id}/judge` moves the claim to
   `UNDER_RESOLUTION` and runs the juror (`src/juror.py`). An `ok`
   report carries a verdict: `UPHELD` → `RESOLVED_TRUE`,
   `REFUTED` → `RESOLVED_FALSE`, with the full report (model,
   completion id, verification) stored on the claim and
   `claim.judged` logged. An `unavailable`/`error` report is
   recorded with its reason and the claim **stays**
   `UNDER_RESOLUTION` — re-judging from `UNDER_RESOLUTION` is
   lawful, so a claim blocked on juror availability resolves when
   the juror can run.
4. **Finalize** — `POST /api/v1/claims/{id}/finalize` requires an
   explicit **authorization reference** in the body (the
   evidence-gated architecture's guard pattern; missing → 422) and
   is lawful only from `RESOLVED_TRUE` (anything else → 409).
   Finalizing marks the claim `ASSURATIZED` and logs
   `claim.finalized`. Finalize is the market parties'
   confirmation of the resolution the juror reported (§3): the
   authorization reference is the confirming party's act — an
   unchallenged claim is confirmed with its challenge window
   lapsed, and a claim that was challenged and then upheld
   finalizes with `withstood = true` recorded on the claim's
   challenge record and in the finalize event — challenged and
   withstood is the strongest form of the mark.
   `RESOLVED_FALSE` can never finalize.

## 6. The Arcium tier — ASSURATIZED @ARCIUM

Some claims and some sale processes cannot have their evidence or
their bids visible — a distressed seller's true opex, a sealed
bidder's price. Those run on the confidential tier:

- Claims carry `confidentialTier`: `STANDARD` (the NEAR AI / NEAR
  ledger environment of §4) or `ARCIUM`.
- An `ARCIUM`-tier claim that reaches resolution carries the mark
  **ASSURATIZED @ARCIUM**: its evidence and its judging ran under
  Arcium's MPC network (the encrypted supercomputer), so the
  resolution is public but the underlying evidence never was.
- **Sealed-bid auctions and reverse auctions** are the auction
  forms of the same tier: sellers (or buyers, in reverse) solicit
  bids that must stay sealed until determination. These run
  through the existing `integrations/parleyswap/` scaffold
  interface, `ISealedBidAuctionAdapter` — create auction with
  terms (including the mandatory authorization reference), submit
  **sealed (encrypted) bids only**, determine the winner inside
  the encrypted computation, close out. The adapter never sees a
  plaintext bid outside the MPC boundary, and settlement is
  deliberately NOT part of the interface: Compose settles USDC on
  Solana through its own path, keeping auction execution and
  settlement distinct stages (governance spec 06, §4; Q-2:
  auction-path withdrawals reconcile as `SOLVER_WITHDREW`).
- **In this build the Arcium tier is a data flag plus this spec's
  alignment — no Arcium calls are made.** The scaffold adapter
  refuses every method (`ParleySwapNotPluggedIn`) until the
  Sprint 2 plug-in lands with Nithin's ParleySwap reinterpretation.
  An `ARCIUM` claim is accepted, flagged, judged on the standard
  juror path, and marked; claiming live MPC execution for it today
  would be fabrication.

## 7. The Iron Rule — claims never move money

No claim state transition executes, authorizes, or triggers a
financial transaction. Bonds in this build are mock units recorded
on the claim row. In the full design, bonds are escrowed value
recorded against the claim — released or forfeited only by a
separate, explicitly authorized settlement step that this pipeline
never invokes. Settlement of marketplace deals stays what it has
always been: **USDC on Solana**, through the settle flow, entirely
outside the claim lifecycle. A macro signal, a market price, an AI
judgment — none of them moves funds (Evidence-Gated Architecture,
spec 06, the Iron Rule).

## 8. The Reliance API

`GET /api/v1/reliance/claims?intentId=` is the financing-partner
read surface. It is gated by the x401 identity stub (the same
verifier the metered and agent surfaces use; no `X-IDENTITY` →
401; the stub swaps for AssurativeV2 trust-layer verification in
Sprint 2). It returns **only ASSURATIZED claims** — open,
challenged, under-resolution, and resolved-false claims are not
reliance material and are excluded by construction — each with:

- the claim itself (class, period kind, statement, claimed value);
- the bond fields (claimant bond; challenger bond where a
  challenge occurred, with `withstood` where it applies);
- the claimant Entity;
- the juror report summary (outcome, verdict, model, completion
  id, verification);
- the **resolution trail**: the claim's EventLog rows in order —
  issued, challenged, judged, finalized — the documented due
  diligence a credit committee relies on.

Credence prices each claim in an LMSR market and lets the price
speak. This build carries no live market price (a thin market's
price is not evidence — the Iron Rule's spirit); the reliance
surface instead carries the bond at risk and the juror's verified
report. The full design adds the Credence-style credence price as
one more field of the same response, funded by disclosed operator
agents seeding liquidity — designed here, not built, and never a
substitute for resolution: **a price is a prior, not a proof;
placement and lending gate on resolved claims.**

## 9. The moat

The mechanism is copyable — Credence is MIT-licensed. What
accumulates inside UZEmarkets is not:

- **Resolved truth compounds.** Every Assuratized claim becomes a
  comparable: actual total operating expenses, by period, by
  micro-region, by asset class, proven on evidence. That dataset
  exists nowhere else and grows with every deal that passes
  through the marketplace.
- **Reputation is locked in the ledger.** Claimants whose claims
  resolve true build a public track record; financing partners
  learn whose numbers hold. The history lives on these rails and
  does not transfer to a fork.
- **The Reliance API embeds in the credit decision.** Once a
  lender's underwriting calls the API, the resolution trail is
  part of its documented due diligence. Switching providers means
  abandoning the evidence trail its credit committee already
  relies on.
- **Our own operations feed the supply.** Assessment & Advisory
  generates the projections, GIRA's partner data generates the
  agriculture / NR claims, settled deals generate the period
  actuals. Claims come from work UZEmarkets already does, not
  from hoping strangers arrive to trade.

## 10. Scope boundaries of this build

Built: the claim table + API, the single-step lifecycle guards,
the juror on the existing attested-inference discipline, the
Reliance read surface, EventLog trails, the Arcium data flag.

Not built (designed above, stated plainly): NEAR chain anchoring
of claims; NEAR Intents bond funding (dry-run only on testnet by
design); the escalating-bond dispute ladder and council escalation
(the Credence full design — this build takes one challenge and
the juror); live Arcium MPC (Sprint 2 plug-in behind the scaffold
interface); the credence price.
