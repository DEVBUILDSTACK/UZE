# Diagram 49 — Three-Tier x401/x402 Compliance — PROPOSAL

STATUS: PROPOSAL (consolidated relay version, 2026-11-11
~19:17 ET; supersedes the ~19:12 relay text). Directive 1's
compliance family remains unconfirmed by the owner in his
own words; nothing here is implemented. Enforcement point
when built: metering.py's identity seam — the consolidated
version now agrees.
FIXED by this version: the cent boundaries are exact
($29.999 Tier 1 / $30.00 Tier 2 / $199.99 Tier 2 / $200.00
Tier 3).
FAILED PREMISE in this version: Tier 2's rule that x401
verification "must route through Circle and Arc." Per
research note 18 (verified 2026-11-11 against the primary
source), x401 is Proof's protocol (proof.com/x401) and Arc
is Circle's settlement L1 — Arc issues no credentials and
routes no identity verification. The submission copy in
this package repeats the claim ("routed through
Circle/Arc") and cannot ship as written; identity
verification routes through the x401 issuer/verifier, and
Arc's role stays settlement-side.

```mermaid
flowchart TD
    subgraph TXN["Incoming Transaction Request"]
        AMT{"Amount?"}
    end

    subgraph T1["Tier 1: Micro (< $29.99)"]
        X402_ONLY["x402 Payment Only"]
        PROCEED1["Proceed Frictionless"]
    end

    subgraph T2["Tier 2: Verified Agent ($30 - $199.99)"]
        CHECK_X401{"Has x401 ID?"}
        REJECT2["401 Unauthorized"]
        PROCEED2["Proceed with x402"]
    end

    subgraph T3["Tier 3: Syndicate (> $200)"]
        CHECK_KYB{"Has Entity KYB?"}
        REJECT3["403 Forbidden"]
        PROCEED3["Proceed with x402"]
    end

    AMT -- "< $29.99" --> X402_ONLY
    X402_ONLY --> PROCEED1

    AMT -- "$30 - $199.99" --> CHECK_X401
    CHECK_X401 -- "No" --> REJECT2
    CHECK_X401 -- "Yes" --> PROCEED2

    AMT -- "> $200.00" --> CHECK_KYB
    CHECK_KYB -- "No" --> REJECT3
    CHECK_KYB -- "Yes" --> PROCEED3

    style TXN fill:#e3f2fd
    style T1 fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style T2 fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style T3 fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px
```
