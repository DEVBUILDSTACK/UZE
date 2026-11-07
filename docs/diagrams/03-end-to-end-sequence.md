<!--
  Repo:       DevBuildStack/UZEMARKETS
  Branch:     hackathon/nov-2026
  Sprint:     1.5 (Hackathon, Nov 2026)
  Merges to:  main by 2026-11-13 EOD Eastern
  Supersedes: none (additive — Sprint 2 seeds this content)
  Audience:   Both — business and engineering
-->

# End-to-End Sequence — The Demo Walkthrough

Five phases, two solvers, one settlement, one deliverable.

```mermaid
sequenceDiagram
    autonumber
    participant SYN as Syndicate<br/>(Human UI)
    participant MP as UZEMARKETS<br/>(FastAPI)
    participant NC as NEAR Contract<br/>(Rust)
    participant HUM as Human Specialist<br/>(Agent API)
    participant AGT as AI Agent<br/>(Agent API + NEAR AI)
    participant AI as NEAR AI Cloud<br/>(TEE Enclave)
    participant CS as Chain Signatures<br/>(MPC Signer)
    participant SOL as Solana<br/>(USDC)

    Note over SYN,SOL: Phase 1 — Spec Posted
    SYN->>MP: POST /specs<br/>340-room Aloft · Miami-Brickell
    MP->>NC: post_intent(spec)
    NC-->>MP: intent_id
    MP-->>SYN: spec_id (rendered page + JSON-LD)

    Note over SYN,SOL: Phase 2 — Bidding
    HUM->>MP: POST /bids<br/>$22,500 · 60 days
    MP->>NC: submit_bid(intent_id, human)

    AGT->>MP: POST /bids<br/>$4,200 · 48 hours
    AGT->>AI: Chat Completion<br/>(spec → operating analysis)
    AI-->>AGT: analysis + attestation receipt
    AGT->>AGT: verify_response(completion.id)
    MP->>NC: submit_bid(intent_id, agent + attestation)

    Note over SYN,SOL: Phase 3 — Selection
    SYN->>MP: GET /specs/{id}/bids
    MP-->>SYN: [human_bid, agent_bid + receipt]
    SYN->>MP: POST /settle<br/>(bid_id, choice)

    Note over SYN,SOL: Phase 4 — Cross-Chain Settlement
    MP->>NC: settle(intent_id, bid_id)
    NC->>CS: request_signature<br/>(recipient, amount)
    CS->>SOL: USDC transfer<br/>via derived address
    SOL-->>CS: tx_confirmed
    CS-->>NC: signature_receipt
    NC-->>MP: settlement_event

    Note over SYN,SOL: Phase 5 — Delivery
    MP-->>SYN: deliverable + receipt
    MP-->>AGT: payout notification
    MP->>MP: write comparable to<br/>micro-region dataset
```

What to read off this diagram

· The agent's bid is not a promise — it is backed by an executed inference call. verify_response fires before the bid is submitted.
· Chain Signatures sits between the contract and Solana. The marketplace never touches Solana directly.
· Phase 5 writes the comparable. This is the moment the business compounds.
