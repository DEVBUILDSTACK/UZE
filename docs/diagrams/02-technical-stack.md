<!--
  Repo:       DevBuildStack/UZEMARKETS
  Branch:     hackathon/nov-2026
  Sprint:     1.5 (Hackathon, Nov 2026)
  Merges to:  main by 2026-11-13 EOD Eastern
  Supersedes: none (additive — Sprint 2 seeds this content)
  Audience:   Blockchain engineers, systems architects
-->

# Technical Stack — Layer View

Four language boundaries. Rust owns the chain. Python owns orchestration and inference. TypeScript owns the surface. The payment protocols sit as thin stubs at the orchestration layer.

```mermaid
flowchart TB
    subgraph CLIENTS["CLIENTS"]
        C1["Human Browser<br/>Read-only HTML + JSON-LD"]
        C2["AI Agent<br/>JSON API client"]
    end

    subgraph FE["FRONTEND — TypeScript / Next.js"]
        F1["Next.js SSR<br/>SEO · GEO · Structured data"]
        F2["Agent API Surface<br/>POST /specs · POST /bids · POST /settle"]
    end

    subgraph ORCH["ORCHESTRATION — Python 3.12+ / FastAPI"]
        O1["FastAPI Core<br/>Business logic · Routing"]
        O2["py-near<br/>NEAR RPC client"]
        O3["nearai-inference-sdk<br/>Attested inference client"]
    end

    subgraph NEAR["NEAR BLOCKCHAIN — Rust"]
        N1["UZEMARKETS Contract<br/>post_intent · submit_bid · settle"]
        N2["Named Accounts<br/>Human + Agent identity"]
        N3["Chain Signatures<br/>MPC signer · v1.signer"]
    end

    subgraph NEARAI["NEAR AI CLOUD — Attested Inference"]
        A1["Private TEE Enclave<br/>GLM 5.3 Flash · DeepSeek V4.1 Flash"]
        A2["Attestation Receipt<br/>Response Signature · verify_response"]
    end

    subgraph SOL["SOLANA — Settlement"]
        S1["Derived Solana Address<br/>from NEAR identity"]
        S2["USDC Transfer<br/>devnet → mainnet"]
        S3["Treasury Sub-account<br/>Altitude (post-MVP)"]
    end

    subgraph PAY["PAYMENT & IDENTITY"]
        X1["x402<br/>HTTP 402 · per-call USDC"]
        X2["x401<br/>HTTP 401 · NIST IAL2 identity"]
    end

    C1 --> F1
    C2 --> F2
    F1 --> O1
    F2 --> O1
    O1 --> O2
    O1 --> O3
    O2 --> N1
    N1 --> N2
    N1 --> N3
    O3 --> A1
    A1 --> A2
    N3 --> S1
    S1 --> S2
    S2 --> S3
    O1 -.->|"metering"| X1
    O1 -.->|"admission"| X2

    style NEAR fill:#e1f5ff
    style SOL fill:#f3e5f5
    style NEARAI fill:#fff3e0
    style ORCH fill:#e8f5e9
    style FE fill:#fce4ec
    style PAY fill:#fff9c4
```

What to read off this diagram

· Rust owns exactly three things: the contract, the named accounts, and Chain Signatures.
· Python owns orchestration and inference. It talks to NEAR via py-near, to NEAR AI via nearai-inference-sdk, never to Solana directly.
· TypeScript owns the surface. Read-only HTML for humans, JSON API for agents.
· NEAR never settles. It signs. Solana never matches. It settles.
· x402 and x401 are stubs at the orchestration layer. Interfaces are named so Sprint 2 slots them in.
