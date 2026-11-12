# Diagram 12 — Ecosystem Separation: The Three Repositories

The three-repo architecture, revised 2026-11-10 (Final Doctrine
directive): UZEmarkets as the Dual-Sided Talent Marketplace under
the original taxonomy — Talent, Tickets, Touring, Stay (Stay =
hospitality managed real estate) — with the Truth Layer (agentic
talent), the Venue (auctions), and the Human Talent Layer.
TradeLayer and SigLayer remain the separate Treasury Stack.

```mermaid
flowchart TD
    subgraph UZE["UZEmarkets (Repo 1: DEVBUILDSTACK/UZE)"]
        direction TB
        TAXONOMY["Original Taxonomy: Talent, Tickets, Touring, Stay<br/>(Stay = Hospitality Managed Real Estate)"]

        subgraph TRUTH["The Truth Layer (Agentic Talent)"]
            GIRA["GIRA (A|NR|D)"]
            SURA["SURA (HiCRE)"]
            ASSURATIES["Assuraties Verification"]
        end

        subgraph VENUE["The Venue"]
            AUCTION["RWA Sealed-Bid Auction"]
        end

        subgraph TALENT["The Human Talent Layer (Stay)"]
            PLACE["Property Management Placement<br/>(GMs, Ops, Maintenance)"]
        end
    end

    subgraph TREASURY["Treasury Stack (Separate Repos)"]
        direction TB
        TRADE["TradeLayer (Repo 2)<br/>Standard Treasury / Open to Affiliates"]
        SIG["SigLayer (Repo 3)<br/>VIP Treasury / Priors Borrowing / FLP Gated"]
    end

    CLIENT["Affiliates / Owners / Syndicates"]

    CLIENT -->|"Verifies Assets & Lists Auctions"| UZE
    CLIENT -->|"Optimizes Capital"| TREASURY

    style UZE fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style TREASURY fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style TALENT fill:#81d4fa,stroke:#0288d1,stroke-width:2px
```
