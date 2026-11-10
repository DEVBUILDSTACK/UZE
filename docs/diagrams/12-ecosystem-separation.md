# Diagram 12 — Ecosystem Separation: The Three Repositories

The three-repo architecture (Final Architecture directive,
2026-11-10): UZEmarkets the Truth & Verification Layer; TradeLayer
and SigLayer the separate Treasury Stack. Zero code overlap.

```mermaid
flowchart TD
    subgraph UZE["UZEmarkets (Repo 1: DEVBUILDSTACK/UZE)"]
        direction TB
        VERIFY["Verification & Information Markets"]
        GIRA["GIRA (A|NR|D)"]
        SURA["SURA (HiCRE)"]
        AUCTION["RWA Sealed-Bid Auction"]
        VERIFY --> GIRA
        VERIFY --> SURA
        VERIFY --> AUCTION
    end

    subgraph TREASURY["Treasury Stack (Separate Repos)"]
        direction TB
        TRADE["TradeLayer (Repo 2)"]
        SIG["SigLayer (Repo 3)"]

        TRADE_DEF["Standard Treasury<br/>Open to Affiliates"]
        SIG_DEF["VIP Treasury<br/>Priors Borrowing<br/>Requires FLP Holding"]

        TRADE --- TRADE_DEF
        SIG --- SIG_DEF
    end

    CLIENT["Affiliates / Owners / Syndicates"]

    CLIENT -->|"Verifies Assets"| UZE
    CLIENT -->|"Optimizes Capital"| TREASURY

    UZE -.->|"Zero Code Overlap"| TREASURY

    style UZE fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style TREASURY fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
```
