# Diagram 09 — WhatsApp Outreach & Americas Diaspora Flow

**Status: business/marketing flow per DeepSeek's MIV/WhatsApp directive
(relayed by James, 2026-11-09). Strategy diagram — the funnel it draws is
the Sprint 2+ build target, not a live channel. Technical counterpart:
Diagram 08. Channel policy note: outbound WhatsApp use remains governed
by the comms rules on file (warm engagement; James's gates) until James
revises them.**

```mermaid
flowchart LR
    subgraph TARGETS["Target Demographics"]
        T1["80,000 Brazilian Business Owners<br/>(Farms, Feedlots, CRE)"]
        T2["US East Coast Diaspora<br/>(Boston to Miami Portuguese Speakers)"]
    end

    subgraph FUNNEL["Messaging & Intelligence VPS"]
        META["Meta-Business API<br/>(WhatsApp Group Deployment)"]
        HERMES["Hermes Lead Qualifier"]
    end

    subgraph CORE["UZEmarkets Marketplace"]
        GIRA["GIRA<br/>(A N R & D Underwriting)"]
        SURA["SURA<br/>(HiCRE Underwriting)"]
    end

    subgraph OUTPUTS["Capital & Deal Flow"]
        LOANS["Debt Financing (US / Brazil)"]
        AUCTION["RWA Auctions (Paraguay/Uruguay Crisis)"]
        US_RE["US CRE Investments (FL / Mid-Atlantic)"]
    end

    T1 --> META
    T2 --> META
    META -->|"Inbound Requests"| HERMES

    HERMES -->|"ARD Intent"| GIRA
    HERMES -->|"HiCRE Intent"| SURA

    GIRA --> LOANS
    GIRA --> AUCTION
    SURA --> US_RE
```

**Reading the diagram.** The funnel starts from two populations: the
80,000-member Brazilian business-owner network (farms, feedlots, CRE) and
the Portuguese-speaking diaspora along the US East Coast, Boston to
Miami. Both enter through the Meta-Business API on the MIV, where Hermes
qualifies the lead and formulates the intent — A·N·R·D to GIRA, HiCRE to
SURA. Underwriting outputs land as capital and deal flow: debt financing
in the US and Brazil, RWA auctions in the Paraguay/Uruguay crisis
corridor, and US CRE investment in Florida and the Mid-Atlantic.
