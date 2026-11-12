# ParleySwap × UZEmarkets — Arcium MPC sealed-bid integration scaffold

Status: **scaffold only** (built 2026-11-08, Sprint 1.5 idle-cycle
workstream). No live Arcium, Anchor, or Solana code runs from
this directory. It exists so Nithin Mengani's ParleySwap work can
plug into UZEmarkets in Sprint 2 without a boilerplate week.

## Source structure reviewed (2026-11-08)

Nithin's repo — `github.com/Nithin-Varma/parleySwap` (public):

- `intents/` — the Anchor + Arcium workspace:
  - `Anchor.toml`, `Arcium.toml`, workspace `Cargo.toml`
  - `encrypted-ixs/` — Rust crate holding the encrypted
    instructions (incl. the `determine_winner` circuit artifacts)
  - `programs/sealed_bid_auction/` — the Anchor program
  - `tests/sealed_bid_auction.ts`, `scripts/setup-devnet.ts`
- `solvers/` — TypeScript solver (`solver.ts`, `index.ts`, IDL)
- `app/` — Next.js front end; API routes for prepare-intent,
  suggest-fill, and Ika dWallet signing; `lib/programClient.ts`
- `config/addresses.ts`

## How this scaffold mirrors it

| Nithin (`parleySwap`) | Here (`integrations/parleyswap/`) |
| --- | --- |
| `intents/Cargo.toml` (workspace) | `Cargo.toml` (workspace, same member names) |
| `intents/encrypted-ixs/` | `encrypted-ixs/` (stub crate, same name) |
| `intents/programs/sealed_bid_auction/` | `programs/sealed_bid_auction/` (stub crate, same name) |
| `intents/Anchor.toml`, `intents/Arcium.toml` | same files, placeholder config |
| TS solver / app program client | Python adapter interface (below) — compose is Python; the TS solver stays his surface |

## The plug-in contract (Python side)

`src/uze_parleyswap_adapter/interface.py` defines
`ISealedBidAuctionAdapter` — the only surface compose will call:

- `create_auction(terms) -> AuctionHandle`
- `submit_sealed_bid(handle, bid) -> BidReceipt`
- `determine_winner(handle) -> WinnerResult`
- `close_auction(handle) -> AuctionCloseout`

Every method on the scaffold implementation raises
`ParleySwapNotPluggedIn`. Nithin's plug-in replaces the
implementation, not the interface. Auction terms and bids are
plain dataclasses; cross-system references are strings, never
foreign keys.

## Governance constraints (filed, binding on the plug-in)

- The auction adapter is reachable in the A/D/R pipeline only
  through `LISTING_APPROVAL_PENDING → AUCTION_ADAPTER`, and only
  with an explicit owner-instruction reference
  (docs/specifications/06-EVIDENCE-GATED-ARCHITECTURE.md).
- A listing is not a sale. Auction execution and USDC settlement
  are distinct stages; settlement of record stays USDC on Solana
  through compose's settlement path.
- On marketplace intents, this integration is the
  `executionEnvironment = ARCIUM_AUCTION` path; NEAR intents
  remain the default.
- Nithin is required for the UZEmarkets reinterpretation/
  extension of ParleySwap (James, 2026-11-01), possibly with
  Dipanshu. This scaffold does not reinterpret anything — it
  prepares the socket.
