# Diagram 41 — The Institutional Underwrite Flow

PROPOSAL — relayed directive, 2026-11-11 (not ratified).
Scoping notes against the verified record (SoSem, 2026-11-11):

- The email gateway ALREADY computes cap rate + implied value
  for the Acquisition/Valuation use case, with 12/18/36-month
  historicals (built 2026-11-10). Price per Unit and Price per
  SqFt are the genuinely new metrics here.
- The chart-of-accounts normalization, if built, maps INTO the
  ratified seven-bucket P&L taxonomy (James, 2026-11-10; Spec
  07 §2.2): Revenue / Operating Expenses / Taxes / Insurance(s)
  / Interest / Misc Net / Profit — OpEx never absorbs Taxes,
  Insurance, or Interest.
- SURA's underwriting analysis lives in agents.py +
  email_gateway.py. juror.py is the Assuraties claim-judging
  prompt (already taxonomy-updated 2026-11-10); the directive's
  "update juror.py" targets the wrong file.
- CoStar/STR: no license, no integration exists. An adapter
  would ship as an evidence-gated MOCK with synthetic data
  labelled synthetic — never presented as CoStar data.

```mermaid
flowchart TD
    subgraph INGEST["Data Ingestion"]
        EMAIL["UZE Underwrite Email Gateway"]
        T12S["Multiple Years of T-12s / P&Ls<br/>(Inconsistent PDFs/Excel)"]
        OCR["OCR & Line-Item Normalization<br/>(Standard Chart of Accounts)"]
    end

    subgraph DATA["Data Providers"]
        COSTAR["CoStar API<br/>(Mid-Atlantic Sales Comps)"]
        STR["STR Hospitality Data<br/>(Occupancy, ADR, RevPAR)"]
    end

    subgraph SURA["SURA (Institutional Analyst AI)"]
        CALC["Valuation Engine"]
        CAP["Cap Rate (NOI / Price)"]
        UNIT["Price per Unit"]
        SQFT["Price per SqFt"]
        HIST["Historical Analysis"]
        GROWTH["NOI Growth Rate"]
        FLUCT["Expense Fluctuations"]
    end

    subgraph OUTPUT["The Deliverable"]
        REPORT["Verified PDF Report<br/>(Underwriting Summary & Benchmarking)"]
    end

    T12S --> OCR
    EMAIL --> T12S
    OCR --> CALC
    COSTAR --> CALC
    STR --> CALC
    CALC --> CAP
    CALC --> UNIT
    CALC --> SQFT
    OCR --> HIST
    HIST --> GROWTH
    HIST --> FLUCT
    CAP --> REPORT
    UNIT --> REPORT
    SQFT --> REPORT
    GROWTH --> REPORT
    FLUCT --> REPORT

    style INGEST fill:#e3f2fd
    style DATA fill:#fff3e0
    style SURA fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style OUTPUT fill:#f3e5f5
```
