# Diagram 49 — Three-Tier x401/x402 Compliance — PROPOSAL

STATUS: PROPOSAL (relayed 2026-11-11 ~19:12 ET). The tier
thresholds refine Directive 1's compliance posture, which
remains unconfirmed by the owner in his own words; nothing
here is implemented. Enforcement point when built:
metering.py's identity seam (treasury_router.py is the
pre-task NEAR compute check, not a transaction validator).
Boundary defect noted for the build: Tier 1 "under $29.99"
and Tier 2 "$30.00–$199.99" leave $29.99 itself claimed by
the pseudo-logic's `29.99 <= amount` Tier-2 branch while the
tier text starts Tier 2 at $30.00 — settle the exact cent
boundaries at build time.

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
