# Diagram 09 — WhatsApp Outreach & Americas Diaspora Flow

![Rendered diagram](09-whatsapp-business-flow.jpg)

**Status: business/marketing flow per DeepSeek's MIV/WhatsApp directive
(relayed by James, 2026-11-09); this version (v2, supplied by James
2026-11-09) replaces the first version filed the same day — targets are
now segmented by population AND sector. Strategy diagram — the funnel it
draws is the Sprint 2+ build target, not a live channel. Technical
counterpart: Diagram 08. Channel policy note: outbound WhatsApp use
remains governed by the comms rules on file (warm engagement; James's
gates) until James revises them.**

```mermaid
flowchart LR
    subgraph TARGETS["Target Demographics & Sectors"]
        T1["Brazilian Business Owners<br/>& US Portuguese Diaspora"]

        T2["HiCRE Sector<br/>(Hotels, Resorts, Commercial Income)<br/>Brokers, Property Managers, PE Syndicates"]

        T3["A N R & D Sector<br/>(Agriculture, Natural Resources, Dev)<br/>Raw Land, Farmland, Ag Brokers"]
    end

    subgraph FUNNEL["Messaging & Intelligence VPS"]
        META["Meta-Business API<br/>(WhatsApp Group Deployment)"]
        HERMES["Hermes Lead Qualifier"]
    end

    subgraph CORE["UZEmarkets Marketplace"]
        SURA["SURA<br/>(HiCRE Underwriting)"]
        GIRA["GIRA<br/>(A N R & D Underwriting)"]
    end

    subgraph OUTPUTS["Capital & Deal Flow"]
        US_RE["US CRE Investments (FL / Mid-Atlantic)"]
        LOANS["Debt Financing (US / Brazil)"]
        AUCTION["RWA Auctions (Paraguay/Uruguay Crisis)"]
    end

    %% Routing to WhatsApp
    T1 --> META
    T2 --> META
    T3 --> META

    %% Into the MIV
    META -->|"Inbound Requests"| HERMES

    %% Intent Routing
    HERMES -->|"HiCRE Intent"| SURA
    HERMES -->|"ANRD Intent"| GIRA

    %% Output Routing
    SURA --> US_RE
    GIRA --> LOANS
    GIRA --> AUCTION
```

**Reading the diagram.** Three target segments enter through the
Meta-Business API on the Messaging & Intelligence VPS: the Brazilian
business-owner population together with the US Portuguese diaspora; the
HiCRE sector itself (hotels, resorts, commercial income — brokers,
property managers, PE syndicates); and the A·N·R·D sector (raw land,
farmland, ag brokers). Hermes qualifies each inbound request and routes
by intent — HiCRE to SURA, A·N·R·D to GIRA. Outputs land as capital and
deal flow: US CRE investment in Florida and the Mid-Atlantic from SURA;
debt financing (US / Brazil) and RWA auctions in the Paraguay/Uruguay
crisis corridor from GIRA.
