# Diagram 08 — NEAR AI Core, Intent Routing, and the KVM Edge

**Status: architecture per DeepSeek's refined directive (relayed by James,
2026-11-09). Spec: `docs/specifications/10-NEAR-AI-CORE-INTENT-ROUTING-KVM-EDGE.md`.
The KVM/Hermes integration is NOT built during hackathon week; Sprint 2
(Nov 15) begins it.**

Filed as Diagram 08 (the directive package said 06; 06 is the Assuraties
claim-resolution diagram and 07 is the agentic-team diagram — real paths
govern).

```mermaid
flowchart TD
    subgraph KVM["Hostinger KVM (External Edge Infrastructure)"]
        X["X.com / Voice Inputs"]
        GROK["Grok AI (Sensing & Drafting)"]
        HERMES["Hermes Harness (Orchestrator)"]
        SEC["Untrusted Input Sanitizer"]
    end

    subgraph UZE["UZE Monorepo (NEAR AI Core)"]
        INTENTS["NEAR Intents Router"]

        subgraph AGENTS["Agentic Team of Response (NEAR AI Cloud)"]
            GIRA["GIRA (A N R & D)"]
            SURA["SURA (HiCRE)"]

            subgraph JURORS["Juror Team (Assuraties)"]
                J1["Juror TEE"]
                J2["Juror TEE"]
                J3["Juror TEE"]
            end
        end

        DB[("Postgres (Precedent Index & Snapshots)")]
        CONTRACT["Rust Smart Contracts (Chain Signatures)"]
    end

    subgraph APPROVAL["Human Gate"]
        JAMES["James (Double-Tap)"]
    end

    X --> GROK
    GROK --> HERMES
    HERMES --> SEC
    SEC -->|"Formulates Intent"| INTENTS

    INTENTS -->|"Routes to"| GIRA
    INTENTS -->|"Routes to"| SURA
    INTENTS -->|"Routes to"| JURORS

    GIRA --> DB
    SURA --> DB
    JURORS -->|"Writes Verdicts"| DB
    JURORS -->|"Anchors TEE Hash"| CONTRACT

    DB -->|"Feedback Loop"| INTENTS
    HERMES -->|"Drafts for Approval"| JAMES
```

**Reading the diagram.** The hard line is between the two subgraphs. The
UZE monorepo is the NEAR AI-native core: intents are formulated and routed
inside it, the Agentic Team of Response runs on NEAR AI Cloud inference,
verdicts write to the Postgres Precedent Index, and juror TEE hashes anchor
to the Rust contracts. The KVM is edge only: it senses, drafts, and
orchestrates, holds no schemas, and reaches the core strictly through
authenticated REST APIs and NEAR Intents. Drafts for publication route to
James's Double-Tap, never around it.
