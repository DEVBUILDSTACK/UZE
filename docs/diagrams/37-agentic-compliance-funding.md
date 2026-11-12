# STATUS (updated 2026-11-11): Contribution Receipts + mock
escrow pool + true-up BUILT AS MOCK (owner's tap, commit
c3f9c82) — accounting only, no custody. The KYB/KYC compliance
half remains PROPOSAL (relayed approval recorded, not acted
on; see diagram 36).

This diagram arrived inside a relayed "master directive" package.
Under the standing relay rule it is filed as a PROPOSAL: it does
not replace the ratified architecture records, and the builds it
describes happen only on James's own tap. Points where it
diverges from the verified/ratified record are annotated in the
file that carries them.

Divergences from the verified record:
- x401's issuer of record is Proof (NIST IAL2 credentials);
  Arc is the settlement side of the flow, not the verifier
  (research note 18). The "Arc Network Verified" label below
  is the package's framing, kept as received.
- The Solana escrow pool, Contribution Receipts, and post-
  auction true-up are NEW and unbuilt. They are money-adjacent
  (pooled entity capital) and sit behind the custody gate:
  design/mock only until James directs otherwise.

```mermaid
flowchart TD
    subgraph COMPLIANCE["Compliance & Identity"]
        KYB["Entity KYB<br/>(Cayman LLC)"]
        KYC["Partner KYC"]
        X401["Agent x401 Identity<br/>(Arc Network Verified)"]
        X402["Agent x402 Account"]
    end

    subgraph FUNDING["A2A Fractional Funding"]
        AGENT_A["Partner A Agent<br/>($100k)"]
        AGENT_B["Partner B Agent<br/>($100k)"]
        AGENT_C["Partner C Agent<br/>($100k)"]
    end

    subgraph ESCROW["Solana Escrow Contract"]
        POOL["Entity Capital Pool<br/>($300,000 Total)"]
        RECEIPT["Mints Contribution Receipts<br/>(33.3% Each)"]
    end

    subgraph POST_AUCTION["Post-Auction True-Up"]
        EQUITY["Legal Equity Split<br/>(e.g., 50/25/25)"]
        P2P["Agent-to-Agent Send/Receive<br/>(Balancing the Ledger)"]
    end

    KYB --> KYC
    KYC --> X401
    X401 --> X402
    X402 --> AGENT_A
    X402 --> AGENT_B
    X402 --> AGENT_C
    AGENT_A -->|"Deposits"| POOL
    AGENT_B -->|"Deposits"| POOL
    AGENT_C -->|"Deposits"| POOL
    POOL --> RECEIPT
    RECEIPT --> EQUITY
    EQUITY --> P2P

    style COMPLIANCE fill:#fff3e0
    style FUNDING fill:#e3f2fd
    style ESCROW fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style POST_AUCTION fill:#fce4ec
```
