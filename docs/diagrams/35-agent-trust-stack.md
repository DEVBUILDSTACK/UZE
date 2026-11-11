# Diagram 35 — The Agent Trust Stack

Filed 2026-11-11 with the AgentKit & A2A compliance audit
(research note 35). Two annotations against the verified record:

- **x401's issuer of record is Proof** (the protocol's
  publisher; NIST IAL2-anchored credentials, WebTrust-audited
  CA). The "Arc x401 Issuer" framing in the originating
  directive is not what the public record shows: Arc is
  Circle's L1 and sits on the **settlement side** of the
  combined x401/x402 flow (Circle Agent Wallets, x402 rails).
  The diagram below labels the Arc box accordingly; research
  note 18 Parts 2–3 and note 35 §3 carry the full finding.
- **ERC-8004** appears twice in the current stack map by
  design: as an AgentKit action-provider family (relayed) and
  as the identity registry XSigLayer is already specified
  against in the SigLayer statement of record.

```mermaid
flowchart TD
    subgraph A2A["A2A Protocol (Google → Linux Foundation)"]
        CARD["Agent Card<br/>(JWS-Signed)"]
        RPC["JSON-RPC / gRPC / HTTP+JSON<br/>(v1.0 vs legacy dialect)"]
    end

    subgraph AGENTKIT["Coinbase AgentKit"]
        X402["x402 Action Provider<br/>(v2, multi-chain)"]
        ERC8004["ERC-8004 Action Provider<br/>(Agent Identity/Reputation)"]
    end

    subgraph TRUST["The Trust Layer"]
        X401["x401 Identity<br/>(PROOF-REQUIRED / PRESENTATION)<br/>Who authorized the agent?"]
        X402_RAIL["x402 Payment<br/>(HTTP 402 USDC)<br/>How does value move?"]
        ERC8183["ERC-8183 Escrow<br/>(What if the job fails?)"]
    end

    subgraph ARC["Arc Network (Circle)"]
        ARC_ID["Arc — settlement side of the<br/>x401/x402 flow (Agent Wallets, x402 rails)<br/>x401 issuer of record: Proof"]
    end

    subgraph UZE["UZEmarkets Integration"]
        SURA["SURA / GIRA"]
        TREASURY["Treasury Router"]
    end

    A2A --> AGENTKIT
    AGENTKIT --> TRUST
    ARC --> X401

    X401 -->|"Verifies Mandate"| SURA
    X402_RAIL -->|"Settles Payment"| TREASURY
    ERC8183 -->|"Holds Escrow"| TREASURY

    style A2A fill:#e3f2fd
    style AGENTKIT fill:#e8f5e9
    style TRUST fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style ARC fill:#f3e5f5
    style UZE fill:#fce4ec
```
