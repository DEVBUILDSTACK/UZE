# READ-THROUGH CONTRACT (R4) — DRAFT v0.2

**Product:** UZEMARKETS commerce platform.
**Status:** Sprint 0's first authoring deliverable, written under the ratification of 2026-10-30 (James's tap, all six decisions; spec commits `03d9aec`, `e611aa4`). For review by James (reviewer of record) and the directing coding agent. This document supersedes the earlier partial R4 draft inside the Data-First build plan wherever the ratified terms are more specific.
**Revision v0.2 (2026-10-30):** adds the eighth divergence code, `UPSTREAM_UNAVAILABLE` (§5), per the directing agent's R4 review — the one gap in an otherwise passing review (five of six criteria passed; the sixth, the codegen fidelity check, is a separate pending addition, not a contract term). No other terms changed. (File retained at its v0.1 path.)
**Parties:** the **composition layer** (database `uzemarkets-compose`; the consumer) and **services/api** (the UZE monorepo's FastAPI + Prisma service over Neon Postgres; the entity of record for Event, Ticket, Listing, Auction, Bid).
**Nature:** this is a contract, not code. It defines endpoints consumed, reads proposed as additive, semantics, failure codes, and boundary law. Nothing in this document implements anything.

---

## 1. Source inventory (code-verified)

Verified against `services/api/src/routers/*.py` and `services/api/prisma/schema.prisma` on 2026-10-30. All responses use the `APIResponse` envelope.

### 1.1 Entities and field semantics

- **Event** — the supply-side root. Fields: `id`, `title`, `venue?`, `city?`, `startsAt`, `createdAt`, `updatedAt`; owns `Ticket[]` and optionally `Auction[]`. **Event has no status field**: an event exists or it does not. There is no cancel/delete path in the code, so there is no event-cancellation state for this contract to map; disappearance surfaces only as a 404 (§5, `SOURCE_NOT_FOUND`).
- **Ticket** — the unit of ownership. Fields: `id`, `eventId` (required FK to Event), `ownerId?` (FK to User; **null = unissued inventory**), `tier` (free string, default `general`), `status`, `createdAt`, `updatedAt`.
  - Status vocabulary: **active | listed | transferred | redeemed**.
  - Writers, exactly as coded: issuance (`POST /tickets/`) creates `active`; listing creation flips the ticket to `listed`; transfer (`POST /tickets/{ticket_id}/transfer`, owner-only) sets `ownerId` and flips status to `transferred`. **`redeemed` has no writer in the current code** — it is a schema-declared terminal state with no producing endpoint today.
  - Transfer checks ownership only; it has **no status guard**. A ticket whose status is `listed`, with a live Listing against it, can be transferred directly, and the Listing row is left untouched. This is a real divergence vector and is why §5 separates `TICKET_TRANSFERRED` from `LISTING_GONE`.
  - After a first transfer, status remains `transferred` permanently (later transfers do not change it).
- **Listing** — the UZED.si resale surface on a Ticket. Fields: `id`, `ticketId` (FK), `sellerId` (FK to User), `priceCents` (Int), `feeCents` (Int, default 0), `status`, `createdAt`, `updatedAt`. Prices are integer cents, set at creation; **no code path mutates `priceCents` or `feeCents` after creation**.
  - Status vocabulary: **active | sold | cancelled | flagged**.
  - Writers: creation sets `active` (and requires the caller to own the ticket and the ticket to be `active`, else 409); operator moderation (`POST /listings/{listing_id}/moderate`) maps approve → `active`, flag → `flagged`, remove → `cancelled`. Moderation touches the Listing row only — it does **not** reset the Ticket's `listed` status. **`sold` has no writer**: `POST /listings/{listing_id}/buy` returns **501 — settlement does not exist in services/api**. There is no seller-facing cancel endpoint.
- **Auction / Bid** — Auction status vocabulary: **scheduled | open | closed | settled**. Bids are sealed; `POST /auctions/{auction_id}/bid` requires status `open`. Auctions attach optionally to an Event. The ticket rail governed by this contract reads auctions only as Event context; auction settlement is outside this contract.
- **Affiliate** — **no entity exists in code**. The Prisma schema holds no affiliate model; `GET /affiliates/` and `GET /affiliates/leaderboard` are stubs returning empty lists, and `POST /affiliates/payout` returns 501. In services/api today, holding inventory is expressed entirely through **User** ownership (`Ticket.ownerId`, `Listing.sellerId`); the `User.role` vocabulary (user | operator | agent | admin) has no affiliate value. §7 pins the term contractually against this reality and flags the gap as an open line.

### 1.2 Endpoints consumed (existing)

| Endpoint | Semantics relied on |
|---|---|
| `GET /events/` | List events (limit, default 20, capped 100; ordered by `startsAt` asc). |
| `GET /events/{event_id}` | Single event; 404 `Event not found`. |
| `GET /tickets/mine` | Authenticated caller's own tickets (owner read). |
| `GET /listings/` | **Active listings only** (`status = active` filter is in the query). |
| `GET /listings/mine` | Authenticated caller's listings, any status. |
| `GET /listings/{listing_id}` | Single listing, any status; 404 if absent. This is the re-read used at approval and commit. |
| `GET /auctions/`, `GET /auctions/{auction_id}` | Auction context for an event; 404 if absent. |

Out of read scope but boundary-relevant (services/api operations the composition layer never performs on its own behalf against catalog rows): `POST /events/` (operator-only), `POST /tickets/`, `POST /tickets/{ticket_id}/transfer`, `POST /listings/`, `POST /listings/{listing_id}/moderate`, `POST /listings/{listing_id}/buy` (501 today).

### 1.3 Proposed additive endpoints — PROPOSED, contract only, not implemented

1. **`GET /events/{event_id}/inventory`** (carried from the earlier R4 draft): returns `eventId, title, venue, city, startsAt`; `byTier[]` = { tier, total, active, listed, transferred, redeemed }; `listingsActive`; `minAskCents` (lowest active listing); `projectedAt` (server timestamp of the read); `source: "services-api-postgres-read-through"`.
2. **`GET /tickets/{ticket_id}`**: single-ticket read by id. **This read does not exist today** — the only ticket reads are the caller's own (`/tickets/mine`). The commit-time reconciliation in §6 requires reading a referenced Ticket by id regardless of caller ownership, so this contract records the read as a proposed additive endpoint (or an equivalent operator/internal read path), to be implemented under a separate decision. Until it exists, §6 reconciliation cannot be executed as specified; that dependency is stated, not worked around.

---

## 2. Read-through semantics

1. Projected inventory is a **derived read model**. In Sprint 0 it is **read-through**: computed at request time from services/api's Postgres source of truth. There is no projection table and no cache in Sprint 0.
2. **Commitment and approval reads are always read-through at request time.** No approval gate and no commit may act on a cached, projected, or previously fetched copy of catalog state. Staleness on those paths is zero by construction (read-committed at request time).
3. **Surface parity:** the agent API and the human UI project the identical field set from a read. A field present on one surface and not the other is a defect (the plan's contract-first parity rule).
4. **Future cached projection rule:** if a cached projection is introduced after Sprint 0, it may serve **display only**; it must carry `projectedAt` and a stated max-staleness bound, with the staleness printed wherever it is shown; and it is **forbidden on the commitment path** — approval and commit reads remain read-through regardless.

---

## 3. sourceRef TTL

1. An OfferSnapshot's `sourceRef` (the supplier-side id: a Listing id, Ticket id, or Event id, per rail) is **fresh from the snapshot's `createdAt` until its `expiresAt`**. The interval `[createdAt, expiresAt)` is the snapshot's freshness window; the TTL of every source reference inside the snapshot is exactly that window — there is no separate per-reference TTL.
2. Within the window, a commit may proceed to the §6 reconciliation check against live state. The TTL does **not** make reads stale: §2 reads are always live. The TTL governs **commit validity**, not read freshness.
3. **At or after `expiresAt`, all source references in the snapshot are stale.** Any commit attempt against a stale snapshot fails with `SNAPSHOT_EXPIRED` (§5) before reconciliation begins.
4. Recovery from expiry is never a mutation: OfferSnapshots are immutable. The flow re-reads through services/api and issues a **new** OfferSnapshot with a new window. An expired snapshot is never extended, edited, or silently re-based onto current state.

---

## 4. Hold semantics — explicit absence

**Finding (code-verified, 2026-10-30): services/api has no hold, reservation, lock, or escrow mechanism.** Evidence: no hold/reserve/escrow field, status value, table, or endpoint exists in the Prisma schema or the routers; neither the Ticket nor the Listing status vocabulary contains a hold state; and settlement itself is unbuilt (`POST /listings/{listing_id}/buy` → 501). The nearest textual match in the codebase is an unrelated docstring in `auth.py`.

**Contract term — EXPLICIT ABSENCE:** the composition layer **cannot reserve, hold, or lock inventory through services/api**, and no party may design a flow that assumes it can. Between quote and commit, catalog state can change under a snapshot. The composition layer's only protection against that divergence is the typed failure at the approval gate and at commit (§5) plus the commit-time reconciliation (§6). Any future hold mechanism on the services/api side is a change to this contract, not an extension of it.

---

## 5. Typed divergence failure codes

Divergence is a difference, detected on a §2 read-through re-read, between the state frozen in an OfferSnapshot (and, for the ticket rail, its `payload` seat record) and services/api's current state. **Divergence never proceeds silently.** Every code below, when raised: (a) aborts the operation that detected it — no partial commit, no chain action; (b) kills the snapshot for commit purposes — except `UPSTREAM_UNAVAILABLE`, which blocks without killing (see the note after the table); (c) is returned identically on the agent API and the human UI; (d) is recorded in the composition layer's EventLog with the snapshot id, the referenced id, and the observed current state; and (e) permits continuation only through a fresh read-through and a **new** OfferSnapshot — never an edit to the failed one, never a silent substitution of a "nearest equivalent."

| Code | Trigger (services/api state at re-read) | Surfaces | Client-visible behavior |
|---|---|---|---|
| `SNAPSHOT_EXPIRED` | Commit or gate action attempted at/after `OfferSnapshot.expiresAt` (§3). | Approval gate, commit | Refused before reconciliation; re-quote required. |
| `SOURCE_NOT_FOUND` | A referenced Event, Ticket, or Listing id returns 404 at re-read. (For Event this is the only disappearance form: Event has no status or cancel state.) | Any re-read | Referenced inventory treated as nonexistent; snapshot dead. |
| `LISTING_GONE` | The referenced Listing exists but its status is `sold`, `cancelled`, or `flagged` at re-read. (`sold` is unreachable through current writers — buy is 501 — but is in the vocabulary and covered.) | Quote refresh, approval gate, commit | The quoted resale offer no longer exists; re-quote required. |
| `TICKET_TRANSFERRED` | The referenced Ticket's `ownerId` differs from the owner recorded at quote time, or its status is `transferred`, at commit re-read. Reachable today via the unguarded direct-transfer path (§1.1). | Commit (reconciliation) | Settlement aborted; the ticket's ownership moved under the quote. |
| `TICKET_REDEEMED` | The referenced Ticket's status is `redeemed` at commit re-read. (Vocabulary state; no writer exists today.) | Commit (reconciliation) | Settlement aborted; the ticket is consumed. |
| `SEAT_TAKEN` | The seat bound in `OfferSnapshot.payload` cannot be fulfilled by the referenced Ticket in its current state, for a reason not covered by `TICKET_TRANSFERRED` or `TICKET_REDEEMED`. Named triggers: (i) Ticket status is `listed` but no active Listing fulfills it — the fulfillment path is gone while the ticket persists (reachable today: moderation cancels a Listing without resetting Ticket status); (ii) the seat's Solana mint reference already carries a settlement — a `Commitment.chainTxRef` recorded against a different commitment (double-fulfillment guard). | Commit (reconciliation) | Settlement aborted; the specific seat is no longer fulfillable as bound. |
| `PRICE_MOVED` | The referenced Listing is active at re-read but its `priceCents` or `feeCents` differ from the snapshot's frozen price/terms. **Unreachable under current writers** — no code path mutates a listing's price after creation — and named anyway: the frozen-price defense requires the boundary to name it, and if a price-edit path is ever added to services/api this code activates with no contract change. | Approval gate, commit | Refused; the frozen quote is defended, never repriced in place. |
| `UPSTREAM_UNAVAILABLE` | The re-read itself fails at transport: services/api is unreachable, times out, or returns a server error (5xx) — no state could be observed at all. A transport condition, **not** a state: it is never reported as `SOURCE_NOT_FOUND` (which asserts the referenced inventory does not exist — a claim a transport failure cannot establish) and never treated as agreement with the snapshot. | Any re-read | Operation refused and retryable; no commit may proceed on an unobserved source. The snapshot is **not** killed — its truth is unknown, not falsified. Continuation is a fresh re-read once the source answers (a new snapshot only if the old one has meanwhile expired). |

Two codes are deliberately **absent**: there is no `EVENT_CANCELLED` (no such state exists in services/api — §1.1) and no hold-expired code (§4: there are no holds to expire). And one code is **not a state divergence**: `UPSTREAM_UNAVAILABLE` (added v0.2) covers transport failure, where the source could not be observed at all; it aborts and blocks like the state codes but does not kill the snapshot, for the reason stated in its row.

---

## 6. Commit-time reconciliation (ratified)

Reconciliation happens **at commit, and only at commit**. There is no continuous sync, no background watcher, and no periodic comparison between the two records of the same ticket in the MVP.

At settlement/commit for a ticket-rail commitment, before any chain action or settlement record is written, the composition layer performs this pre-settlement check, in order:

1. **TTL check** — the OfferSnapshot is inside its freshness window (§3); otherwise `SNAPSHOT_EXPIRED`.
2. **Read-through re-read** — the referenced Ticket (by id, §1.3 item 2) and its fulfilling Listing (by id) are read live from services/api.
3. **Comparison** — the live state is compared against the composition layer's own record: the seat assignment, the approval snapshot, and the Solana mint reference carried in `OfferSnapshot.payload`, plus the quote-time `ownerId`, Ticket status basis, Listing id, and frozen price.
4. **Divergence = typed failure** — any mismatch raises the applicable §5 code (`TICKET_TRANSFERRED`, `TICKET_REDEEMED`, `SEAT_TAKEN`, `LISTING_GONE`, `PRICE_MOVED`, `SOURCE_NOT_FOUND`) and aborts the commit. There is no silent proceed and no best-effort settlement.
5. **Clean pass** — settlement proceeds, and the composition layer records the settlement against the Ticket id: `Commitment.chainTxRef` carries the Solana transaction signature (null for off-chain settlement), per §8.

Rationale, as ratified: commit-time is the only point where reconciliation affects correctness. The seat record and the catalog record are allowed to differ at every other moment; they are required to agree at the moment of settlement, or the settlement does not happen.

---

## 7. Affiliates pinning (ratified named deliverable)

The commercial model, as corrected and ratified: **supply comes from affiliates and facilities; demand is B2C direct, or B2B through promoters, facilitators, and clinics.** Per James's positioning, the affiliates hold the supply. This contract pins the terms as follows:

1. **Affiliate = supply-side inventory holder.** An affiliate holds inventory: in services/api terms it owns Tickets (`Ticket.ownerId`) and offers them through Listings (`Listing.sellerId`). Facilities are the second supply source (the health rail; dormant in Sprint 0) and are likewise supply-side, never demand channels.
2. **Promoter, facilitator, clinic = demand-side channels.** They originate and route B2B demand on behalf of buyers. Under this contract they hold **no** inventory and carry **no** inventory-state obligations — unless the same party also lists supply, in which case, for that supply only, it acts as an affiliate and holder obligations attach to those rows.
3. **Obligations differ by side, not by label:**
   - *Holders (affiliates; facilities when live):* their Ticket and Listing rows are the read-through source of truth for quotes against their inventory; divergence codes in §5 fire on their inventory's state; §6 reconciliation compares against their rows at commit.
   - *Channels (promoters, facilitators, clinics) and direct B2C buyers:* no inventory obligations. Their commitments pass through the identical §5/§6 gates — the typed-failure protection runs to the buyer regardless of which channel originated the demand.
4. **Open line (flagged, not resolved):** services/api today has no affiliate entity, role value, or linkage (§1.1) — holding is expressed purely as User ownership, and the affiliate router is a stub. Whether an affiliate is one User, several Users, or a future entity mapped onto Users is **not defined in the code or in the ratified record**. This pin therefore operates on the *role a party plays in a transaction* (holder vs channel), which is fully determined by the ratified model, and leaves the entity-model question open for James and the directing agent. The contract does not invent the linkage.
5. **Open line (flagged, not resolved):** §6 is written for the per-Ticket binding of a seat (the NFT fulfills a specific Listing/Ticket). Whether every ticket-rail quote binds `payload` seat identity to a specific Ticket id at quote time — or whether primary, non-minted, non-resale quotes bind per-tier and resolve to a Ticket only at commit — is not pinned in the ratified record. Until it is, per-Ticket binding is the contract's stated assumption, and per-tier binding, if adopted, requires a contract revision, not an implementation choice.

---

## 8. Boundary rules (ratified — contract law)

1. **Reference, never own.** The composition layer references Event, Ticket, and Listing by id (`OfferSnapshot.sourceRef`) and records settlement against a Ticket id (`Commitment.chainTxRef`). It never owns, creates, or mutates those rows.
2. **Operations stay home.** Issuance, transfer, and redemption of tickets, and creation and moderation of listings, are services/api operations, performed through services/api only. The composition layer's own records (OfferSnapshot, its rail detail tables, Commitment, its seat records in `payload`) live in `uzemarkets-compose` and nowhere else.
3. **Vocabularies stay separate.** Ticket status (active/listed/transferred/redeemed), Listing status (active/sold/cancelled/flagged), Auction status (scheduled/open/closed/settled), OfferSnapshot state, and Commitment state are distinct vocabularies. They are mapped only at this contract boundary, in this document and its successors — never merged into a shared enum, never assumed interchangeable.
4. **No cross-database joins, ever.** The two databases (`uzemarkets-compose`; services/api's Neon Postgres) are never joined, linked, or read through a shared connection. All combination happens through the services/api surface inventoried in §1, at request time.
5. **Snapshots are immutable.** Price and terms are frozen at quote time in OfferSnapshot. Divergence, expiry, and repricing are all resolved by issuing a new snapshot, never by editing an existing one.
6. **Consistency with existing keys.** The RAG already keys chunks off the same ids (`DocumentChunk.source` = `event:<id>`, `listing:<id>`); this contract's reference discipline is consistent with that practice and changes nothing about it.

---

*End of R4 DRAFT v0.1. Open lines carried forward: §1.3 (two proposed additive reads, unimplemented), §7.4 (affiliate↔User linkage undefined), §7.5 (per-Ticket vs per-tier seat binding unpinned).*
