# PROPOSAL — relayed architecture package, 2026-11-11 (not ratified)

This diagram arrived inside a relayed "master directive" package.
Under the standing relay rule it is filed as a PROPOSAL: it does
not replace the ratified architecture records, and the builds it
describes happen only on James's own tap. Points where it
diverges from the verified/ratified record are annotated in the
file that carries them.

Divergences from the verified record:
- A Delphi market close PROGRAMMATICALLY triggering an Arcium
  auction contradicts the ratified evidence-gated rule (Nov 8):
  no auction auto-executes; a human gate stands in front of
  execution. Delphi itself is a grant-stage proposal (no
  application sent; open-source commitment unconfirmed).
- The Commitment Ladder (100 USDC / 30% / 90% / 100%) is a new
  proposal; no escrow ladder exists in the built system.

```mermaid
sequenceDiagram
    autonumber
    participant Buyer as Entity (Capital Pool)
    participant Escrow as Solana Escrow
    participant Delphi as Gensyn Delphi
    participant Arcium as Arcium MPC Auction

    Note over Buyer, Delphi: T-30 Days: Market Open
    Buyer->>Escrow: Locks 100 USDC (Entry)
    Escrow-->>Buyer: Whitelisted for Market

    Note over Buyer, Escrow: T-7 Days + 12 Hours
    Buyer->>Escrow: Locks 30% of Target Bid
    Note right of Escrow: Fail to lock 30% = Removed from Whitelist

    Note over Buyer, Escrow: T-72 Hours
    Buyer->>Escrow: Locks 90% of Target Bid
    Note right of Escrow: Fail to lock 90% = Notified of Removal

    Note over Buyer, Escrow: T-12 Hours
    Buyer->>Escrow: Locks 100% of Target Bid
    Note right of Escrow: Fail to lock 100% = Refunded & Barred

    Note over Delphi, Arcium: T-0: THE TEMPORAL TRIGGER
    Delphi-->>Delphi: Information Market Closes
    Delphi->>Arcium: Programmatically Triggers Auction
    Buyer->>Arcium: Submits Sealed Bid
    Arcium-->>Arcium: Computes Winner (MPC)
    Arcium->>Buyer: Asset Transferred to Entity
    Arcium->>Escrow: Losing Bids Unlocked
```
