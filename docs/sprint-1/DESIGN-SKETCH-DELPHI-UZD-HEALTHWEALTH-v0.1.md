# Design Sketch — Delphi Layer, UZD Attribution, HealthWealth (v0.1, end of Sprint 1)

Status: DESIGN SKETCH ONLY. One page, no code, no schema changes. Filed per the
tracked architectural question in the UZEMARKETS Data-First Build Plan (Reading C,
James's tap 2026-11-01). Input to Sprint 9+ design; nothing here is built.

## Frame (Reading C)

The transaction layer (the Oct 30 sprint series) is built first and emits an
append-only EventLog. Two consumer layers sit on top of it, both additive:
the BELIEF layer (Delphi information markets — prices beliefs about utility)
and the REWARD layer (UZD — incentivizes utility-attesting behavior).
UZE counts and credits usefulness (a derived view over EventLog + attribution
data — computed, never a stored balance). USDC settles every purchase.
Neither consumer layer writes back into the transaction schema.

## 1. Delphi information market — a read-through contract

Modeled on R4's discipline: define the contract before building against it.

- **MarketQuestion** — a utility claim over a transaction-layer entity:
  "Will this venue/event/package deliver the utility it claims by date X?"
  The entity under question is an OfferSnapshot (immutable; its
  [createdAt, expiresAt) window is the market's evidence window).
- **Outcomes / Odds** — declared before trading opens, immutable once live
  (Delphi's rule). Pricing per the standing TradeLayer architecture: DPM for
  app markets, LMSR on the competition network. Odds are read through at
  request time, never cached — the same posture as R4 commitment reads.
- **SettlementReceipt** — Delphi's REE receipt (model, inputs, output,
  cryptographic hash; re-runnable by anyone). In compose terms it plays the
  role the divergence annotation plays for snapshots: a typed, permanent,
  evidence-carrying outcome record appended to the EventLog.
- **Creator / Position** — the market creator is an affiliate (creator fee
  1.5% of volume at settlement, USDC); a position is a CommitmentClass-shaped
  record — who holds what belief, at what odds, against which snapshot.
- **Access shape (of record):** Delphi trading/market creation is unavailable
  in the US — trading non-US, information US + global. The agent surface and
  the human surface both trade (Delphi supports agents natively); the
  dual-surface architecture needs no reshaping.

## 2. UZD attribution and reward

- **Accrual triggers are EventLog events the transaction layer already
  records** — COMMITMENT_RECORDED (purchase) and redemption events — with
  attribution metadata attached. The EventLog is the accrual source of
  record; Sprint 1's substrate serves this unmodified.
- **Accrual queries UZE at accrual time.** UZE (the score) is computed from
  events + the attribution graph at the moment of accrual — no balance to
  keep in sync, no drift. No token custody, no transfer semantics, no
  on-chain state in this layer until UZD issuance itself.
- **Flag A — the attribution graph is the open structural piece.** UZE's
  measurement half rides on EventLog today; its credit half needs a graph of
  affiliate -> referred activity -> credit, and no affiliate entity exists
  upstream (services/api /affiliates is a stub). Home decision, Sprint 9+:
  compose layer (per directive 2) or an additive services/api entity.
- **Flag B — one attestation primitive or two?** UZD accrual may require
  attestation of the purchase/redemption event; Delphi settlement already
  produces REE receipts. If the accrual attestation and the settlement
  attestation are the same primitive, Sprint 9 builds it once and both
  layers consume it. The sketch's position: design them as one primitive
  (an evidence receipt over an EventLog event) unless a requirement forces
  them apart — to be settled at Sprint 9 design, not assumed here.

## 3. HealthWealth — the first named markets on the Delphi layer

Two domains, two upstream populations, independent clocks (filed sequencing
note: schedule the halves independently).

- **Health** — medical-travel utility markets. Questions price over Sprint
  7's health population (FacilityProfile, PackageTemplate,
  ProcedureClassBand; the consent-gated restricted namespace is the evidence
  boundary — markets reference outcomes, never restricted attributes).
- **Wealth** — SME treasury-management utility markets (treasury
  accumulation, cash-flow management, best practices — not individual/HNW).
  Questions price over Altitude + Range: treasury/finance data,
  counterparties + Squads multisig connection, address screening, the
  dashboarding layer. Altitude + Range is a separate track (not in the
  Oct 30 series; deployment window Apr–Jun 2027).
- Build-out slated early summer 2027, on the critical path to first
  production (first week of July 2027).

## Connection points, explicit

EventLog -> Delphi (market inputs: snapshots under question, outcomes as
events) and -> UZD (accrual triggers). Attribution graph -> UZE credit ->
both layers. OfferSnapshot -> the entity every market question and every
accrual ultimately references. Settlement stays USDC on the transaction
rail throughout; the Delphi layer's creator fees are USDC; UZD never
settles anything.

## Open at Sprint 9 design (not decided here)

Integration depth — record points to (i), markets on the live Delphi
protocol (TradeLayer is built on it). Flag A home. Flag B sameness.
Market-creation authority and geo gating per market. Whether HealthWealth's
two halves launch as one component or two.
