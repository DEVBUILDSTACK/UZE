# Diagram 13 — The Non-Compete Flywheel & Auction Carve-out

The Non-Competition Doctrine (Final Architecture directive,
2026-11-10): advisors keep their clients and work from UZEmarkets
data; owners verify P&L through Assuraties; and the carve-out —
owners list assets directly with the RWA auction house, regardless
of advisor.

```mermaid
flowchart TD
    subgraph ADVISORS["Advisors (Keep Their Clients)"]
        BROKER["Broker"]
        LAWYER["Lawyer / Accountant"]
    end

    subgraph UZE["UZEmarkets Core"]
        DATA["x402 Research Data<br/>(Micro-Region P&L)"]
        ASSURATIES["Assuraties Underwriting"]
        AUCTION["RWA Auction House"]
    end

    subgraph OWNER["Property Owner / Syndicate"]
        ASSET["Asset (HiCRE or A|NR|D)"]
    end

    %% The Advisory Flow (Non-Competitive)
    BROKER -->|"Uses Data to Advise"| OWNER
    LAWYER -->|"Uses Data to Advise"| OWNER
    UZE -->|"Provides Data to"| BROKER
    UZE -->|"Provides Data to"| LAWYER

    %% The Verification Flow
    OWNER -->|"Submits P&L for Verification"| ASSURATIES
    ASSURATIES -->|"Returns Verified Truth"| OWNER

    %% The Auction Carve-out (We DO compete here)
    OWNER -->|"Lists Asset Directly"| AUCTION
    AUCTION -.->|"We take the listing,<br/>regardless of advisor"| ADVISORS

    style ADVISORS fill:#fff3e0
    style UZE fill:#e8f5e9
    style OWNER fill:#fce4ec
    style AUCTION fill:#ffcc80,stroke:#f57c00,stroke-width:3px
```
