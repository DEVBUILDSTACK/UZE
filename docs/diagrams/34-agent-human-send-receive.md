# Diagram 34 — Agentic & Human Configuration (Send/Receive & X401)

Filed 2026-11-11 with the Autonomous Treasury build (owner's
override). The distinction this diagram carries (directive,
2026-11-11; verified state per research note 18):

- **x402 Payments / Swaps — CDP (target integration).** The
  hackathon build runs the mock x402 tariff + a mock CDP swap
  router. Fundio's reusable contribution is its CDP **onramp
  session** pattern only — Fundio has no embedded AgentKit and
  no swap module (code-read, 2026-11-11). AgentKit integration
  is a Sprint 2 build item.
- **x401 Identity — PENDING RESEARCH.** x401 is Proof's open
  identity protocol (draft 0.2.0): the server challenges with a
  verifiable-credential request (HTTP 401), the agent presents
  a selectively-disclosed credential + a transaction-bound
  signed approval, and the backend verifies against the
  issuer's published keys before the x402 transaction proceeds.
  Arc is a supported network on the settlement side of that
  flow. Research is filed (note 18, Parts 2–3); no x401 build
  until James directs it.

```mermaid
flowchart TD
    subgraph ACTORS["Actors"]
        HUMAN["Human / Syndicate"]
        AGENT["AI Agent"]
    end

    subgraph ONRAMP["On-Ramp Configuration"]
        INCREMENT{"Increment Rules"}
        I1["$5 - $100 (Step $5)"]
        I2["$101 - $250 (Step $10)"]
        I3["$251 - $1,750 (Step $50)"]
        INCREMENT --> I1 & I2 & I3
    end

    subgraph IDENTITY["Identity & Routing"]
        X401["X401 Identity<br/>(Proof protocol — pending research;<br/>Arc = supported settlement network)"]
        X402["X402 Payment Rails<br/>(CDP target integration;<br/>Fundio = onramp session pattern)"]
    end

    subgraph SEND_RECEIVE["Send & Receive Engine (No Off-Ramp)"]
        CDP["CDP Swap Router<br/>(mock in hackathon build)"]
        SOL["Solana USDC"]
        EVM["Base / Ink / Robinhood"]
        NEAR["Native NEAR"]

        CDP <--> SOL
        CDP <--> EVM
        CDP <--> NEAR
    end

    subgraph EXECUTION["Execution"]
        SURA["SURA/GIRA Inference"]
        ARC_AUC["Arcium Auction"]
    end

    HUMAN --> ONRAMP
    AGENT --> SEND_RECEIVE

    ONRAMP -->|"Funds Wallet"| SEND_RECEIVE
    SEND_RECEIVE --> X401
    SEND_RECEIVE --> X402

    X401 --> EXECUTION
    X402 --> EXECUTION

    style ACTORS fill:#f3e5f5
    style ONRAMP fill:#fff3e0
    style IDENTITY fill:#ffcdd2
    style SEND_RECEIVE fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style EXECUTION fill:#e8f5e9
```
