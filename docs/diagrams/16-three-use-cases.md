# 16 — Three Use Cases: One Email Gateway

How the single email gateway handles three completely different
client emergencies: emergency replacement, acquisition due
diligence, and operational staffing.

```mermaid
flowchart TD
    subgraph CLIENT["Client Urgency"]
        U1["Emergency Replacement<br/>(Fired PM/Analyst)<br/>'Need P&L now!'"]
        U2["Acquisition Due Diligence<br/>(Is the price fair?)<br/>'Need Valuation & Forward P&L'"]
        U3["Operational Staffing<br/>(Need a human)<br/>'Need a Property Manager'"]
    end

    subgraph GATEWAY["Single Email Gateway"]
        EMAIL["ingest@uzemarkets.com"]
        ROUTER{"Subject Keyword Router"}
    end

    subgraph AGENTS["AI Verification (SURA / GIRA)"]
        PL["P&L Verification<br/>Revenue, Expenses, Taxes, Insurance"]
        VAL["Valuation Engine<br/>12/18/36-mo Historicals + NOI/Cap Rate"]
    end

    subgraph TALENT["Talent Placement"]
        HUMAN["Human Property Manager<br/>(Sourced or Outstaffed)"]
    end

    subgraph OUTPUT["The Deliverable"]
        PDF_PL["Verified P&L PDF<br/>(+ Cross-sell for PM)"]
        PDF_VAL["Valuation & Benchmark PDF<br/>(Micro-Region Benchmark Verified)"]
        PLACEMENT["Placed Manager<br/>(Active/Pilot or Outstaffed)"]
    end

    %% Routing Logic
    U1 -->|"Subject: URGENT P&L"| EMAIL
    U2 -->|"Subject: ACQUISITION"| EMAIL
    U3 -->|"Subject: HIRING"| EMAIL

    EMAIL --> ROUTER

    ROUTER -->|"P&L"| PL
    ROUTER -->|"VALUATION"| VAL
    ROUTER -->|"TALENT"| HUMAN

    %% Output Logic
    PL --> PDF_PL
    VAL --> PDF_VAL
    HUMAN --> PLACEMENT

    PDF_PL -.->|"Cross-sell"| U3

    style CLIENT fill:#e3f2fd
    style GATEWAY fill:#fff3e0
    style AGENTS fill:#e8f5e9
    style TALENT fill:#81d4fa,stroke:#0288d1,stroke-width:2px
    style OUTPUT fill:#fce4ec
```
