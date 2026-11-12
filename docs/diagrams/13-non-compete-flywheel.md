# Diagram 13 — The Finalized Covenant & Flywheel

The Non-Competition Covenant, finalized 2026-11-10 (Final Doctrine
directive): advisors are empowered, never replaced — UZEmarkets
takes no advisory clients. Two carve-outs where UZEmarkets DOES
take the business: auction listings, and property management &
operations placement (the human talent layer).

```mermaid
flowchart TD
    subgraph ADVISORS["Advisors (We Empower, Do Not Replace)"]
        BROKER["Broker"]
        LAWYER["Lawyer / Accountant"]
    end

    subgraph UZE["UZEmarkets Core (Dual-Sided Talent Marketplace)"]
        DATA["x402 Research Data<br/>(Agentic Talent for Advisors)"]
        ASSURATIES["Assuraties Underwriting"]
        AUCTION["RWA Auction House"]

        subgraph HUMAN_TALENT["Human Talent Placement (Stay)"]
            ACTIVE_MKT["Active/Pilot Markets:<br/>Own Sourced Talent"]
            OUTSIDE_MKT["Outside Markets:<br/>Outstaffing Partners"]
        end
    end

    subgraph OWNER["Property Owner / Syndicate"]
        ASSET["HiCRE or A|NR|D Asset"]
    end

    %% The Advisory Flow (Non-Competitive)
    UZE -->|"Provides Data to"| BROKER
    UZE -->|"Provides Data to"| LAWYER
    BROKER -->|"Advises"| OWNER
    LAWYER -->|"Advises"| OWNER

    %% The Verification Flow
    OWNER -->|"Submits P&L for Verification"| ASSURATIES

    %% The Auction Carve-out (We DO compete here)
    OWNER -->|"Lists Asset for Sale"| AUCTION
    AUCTION -.->|"We take the listing"| ADVISORS

    %% The Management Carve-out (We DO compete here)
    OWNER -->|"Hires Property Manager / Staff"| HUMAN_TALENT
    HUMAN_TALENT -.->|"We take the management contract"| ADVISORS

    style ADVISORS fill:#fff3e0
    style UZE fill:#e8f5e9
    style OWNER fill:#fce4ec
    style AUCTION fill:#ffcc80,stroke:#f57c00,stroke-width:3px
    style HUMAN_TALENT fill:#81d4fa,stroke:#0288d1,stroke-width:3px
```
