# 17 — UZE Underwriting Gateway: HiCRE-Only, User-Directed Logic

The email ingestion architecture: HiCRE scope check, then the
user's intent (P&L vs Valuation) and use case (Refinancing,
Distressed Sale, Standard Acquisition, Cost Recovery) direct
SURA's analysis. Expected to evolve as use cases are added.

```mermaid
flowchart TD
    subgraph INPUT["Inbound (Email or API)"]
        EMAIL["Forward to ingest@uzemarkets.com<br/>(T-12 PDF, P&L, Rent Roll)"]
        SUBJECT["Subject Line Parsing<br/>(Intent + Use Case)"]
    end

    subgraph ROUTER["HiCRE Scope Check"]
        CHECK{"Is it HiCRE?"}
        REJECT["Reject: ANRD/Farm<br/>(422 Error)"]
    end

    subgraph INTENT["Analysis Direction"]
        PL["P&L Verification<br/>(Revenue, OpEx, Taxes, Insurance)"]
        VAL["Property Valuation<br/>(NOI ÷ Cap Rate)"]
    end

    subgraph USECASE["Use Case Modifiers"]
        REFI["Refinancing<br/>(Focus on Debt Service Coverage)"]
        DISTRESS["Distressed Sale<br/>(Focus on Rapid Liquidity)"]
        ACQ["Standard Acquisition<br/>(Focus on Market Comps)"]
        COST["Cost Recovery<br/>(Focus on OpEx Overspend)"]
    end

    subgraph AGENT["SURA (HiCRE Agent)"]
        SURA["SURA Engine<br/>(Assuraties Precedent Check)"]
    end

    subgraph OUTPUT["The Deliverable"]
        PDF["Verified PDF<br/>(Tailored to Intent & Use Case)"]
        CROSS["Cross-Sell:<br/>'Need a Property Manager?'"]
    end

    EMAIL --> SUBJECT
    SUBJECT --> CHECK
    CHECK -- "No (ANRD)" --> REJECT
    CHECK -- "Yes (HiCRE)" --> PL
    CHECK -- "Yes (HiCRE)" --> VAL

    PL --> REFI
    PL --> COST
    VAL --> DISTRESS
    VAL --> ACQ

    REFI --> SURA
    COST --> SURA
    DISTRESS --> SURA
    ACQ --> SURA

    SURA --> PDF
    PDF -.-> CROSS

    style INPUT fill:#e3f2fd
    style ROUTER fill:#ffcdd2
    style INTENT fill:#fff3e0
    style USECASE fill:#fce4ec
    style AGENT fill:#e8f5e9
    style OUTPUT fill:#f3e5f5
```
