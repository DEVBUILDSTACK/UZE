<!--
  Repo:       DevBuildStack/UZEMARKETS
  Branch:     hackathon/nov-2026
  Sprint:     1.5 (Hackathon, Nov 2026)
  Merges to:  main by 2026-11-13 EOD Eastern
  Supersedes: none (additive — Sprint 2 seeds this content)
  Audience:   Real estate partners, financial analysts, non-technical stakeholders
-->

# Marketplace Flow — Business View

Two service lines, one marketplace. The advisory produces the operating budget and the property manager spec; the placement fulfills it. The human specialist and the AI agent compete on the same specification, and the client chooses.

```mermaid
flowchart TD
    subgraph DEMAND["DEMAND SIDE — Client"]
        D1["Syndicate / Owner<br/>30 doors to 2,000+ doors"]
        D2["Residential Rental<br/>Residential Condo<br/>Hospitality / Resort"]
        D3["Posts Specification<br/>Property · Micro-region · Deliverable · Budget"]
    end

    subgraph MP["UZEMARKETS MARKETPLACE"]
        M1["Intent Matching<br/>micro-region · domain · budget"]
        M2["Bid Collection<br/>Human + Agent compete on same spec"]
        M3["Client Selection<br/>or cheapest adequate executor"]
    end

    subgraph SUPPLY["SUPPLY SIDE — Executors"]
        S1["Human Specialist<br/>Regional expert network<br/>On-site walkthrough + remote modeling"]
        S2["AI Agent<br/>Attested inference<br/>Autonomous analysis"]
    end

    subgraph DELIV["DELIVERABLE — Service Line 1"]
        V1["Operating Budget<br/>Every role · Every opex line A-Z<br/>Brand fee · Micro-region benchmarked"]
        V2["Property Manager Spec<br/>Market rate · Job duties · Hiring blueprint"]
    end

    subgraph SETTLE["SETTLEMENT"]
        P1["NEAR Identity<br/>Authorizes payout"]
        P2["Solana USDC<br/>To treasury sub-account"]
    end

    subgraph PLACE["SERVICE LINE 2 — Placement"]
        L1["Property Manager<br/>Management Company<br/>Operating Talent"]
    end

    D1 --> D2 --> D3 --> M1
    M1 --> M2
    S1 --> M2
    S2 --> M2
    M2 --> M3
    M3 --> V1 --> V2
    M3 --> P1 --> P2
    V2 -.->|"Feeds as blueprint"| L1
    P2 -.->|"Talent priced against<br/>advisory output"| L1

    style DEMAND fill:#e3f2fd
    style SUPPLY fill:#e8f5e9
    style MP fill:#fff3e0
    style DELIV fill:#f3e5f5
    style SETTLE fill:#fce4ec
    style PLACE fill:#f1f8e9
```

What to read off this diagram

· The demand side never chooses a vendor. It posts a specification, and the marketplace routes.
· Human and agent sit at the same level. The agent competes on the same spec.
· Service Line 1 produces two artifacts: the operating budget and the PM spec.
· Settlement is one rail: NEAR authorizes, Solana settles.
· The dotted arrows are the compounding asset: the advisory output prices the talent.
