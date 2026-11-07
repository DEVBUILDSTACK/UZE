<!--
  Repo:       DevBuildStack/UZEMARKETS
  Branch:     hackathon/nov-2026
  Sprint:     1.5 (Hackathon, Nov 2026)
  Merges to:  main by 2026-11-13 EOD Eastern
  Supersedes: none (additive — Sprint 2 seeds this content)
  Audience:   Rust contract engineers, backend engineers
-->

# Intent Lifecycle — Contract State Machine

The states the Rust contract must enforce, and nothing else.

```mermaid
stateDiagram-v2
    [*] --> POSTED: post_intent
    POSTED --> BIDDING: first bid arrives
    BIDDING --> BIDDING: more bids
    BIDDING --> SELECTED: client selects bid
    BIDDING --> EXPIRED: available_until passes
    SELECTED --> SETTLING: settle called
    SETTLING --> SETTLED: Chain Signatures confirms
    SETTLING --> SETTLE_FAILED: signature or transfer fails
    SETTLE_FAILED --> SELECTED: retry (within window)
    SETTLED --> DELIVERED: artifact + receipt confirmed
    DELIVERED --> [*]

    EXPIRED --> [*]

    note right of SETTLING
        x401 identity verified here
        x402 payment attached here
        (Sprint 2 — stubbed for demo)
    end note

    note right of SETTLED
        Comparable written to
        micro-region dataset
    end note
```

What to read off this diagram

· Five active states plus two terminal branches. Every other state is a bug.
· SETTLE_FAILED returns to SELECTED, not BIDDING. The client's choice is preserved.
· EXPIRED is terminal. No resurrection, no late bids.
· The two notes mark the two phase-boundaries: x401/x402 fire during SETTLING; the comparable write fires during SETTLED.
