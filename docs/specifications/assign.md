# UZE Assign — Technical Specification

**Status: BUILT AS MOCK.** Implemented in `services/compose/src/assign.py` and `services/compose/src/contributions.py` (2026-11-11, on the owner's tap: "Build the Assign expansion + contribution receipts as mocks now"). Every payload carries `mock: true`. There is **no custody, no escrow, and no settlement** in this module.

## 1. Listings

- Router: `/api/v1/assign`.
- A listing carries exactly one category from a **closed vocabulary** — unknown categories are refused (422), and the set is extended only by a filed change:
  `REAL_ESTATE_CONTRACT` · `OPERATING_BUSINESS` · `DEFUNCT_BUSINESS` · `BANKRUPTCY_ESTATE` · `COLLECTIBLE_CARDS` · `FINE_ART` · `VEHICLES` · `ON_CHAIN_NFT` · `SECONDARY_TICKETS`
- Listings and bids live in an in-memory registry and are written to the append-only EventLog (`assign.listing_created` / `assign.bid_placed`) as the audit surface.
- A bid is a recorded expression of interest. Closing a listing is out of scope for the mock.

## 2. Contribution receipts (fractional syndicates)

`contributions.py` models syndicate participation in an assignment or auction:

- Escrow **pools** collect member contributions against a target.
- Receipts are issued in basis points and are constrained to sum to **exactly 10,000 bps** across a pool.
- True-up instructions reconcile a member's receipt share against final amounts.
- Receipts execute nothing: they are accounting records over a mock pool, not claims on held funds.

## 3. Scope note

UZE Assign is deliberately **not** part of the hackathon submission narrative (owner's scope ruling, 2026-11-10: the submission stays B2B agentic / RWA). Categories outside that narrative remain an internal build item until the owner rules otherwise.

## 4. Production design (roadmap)

The production assignment market prices contracts through information markets (the Delphi protocol) and settles executed assignments with cryptographic proof. Neither the pricing integration nor settlement is implemented in the current build; §1–§2 are the implemented surface.
