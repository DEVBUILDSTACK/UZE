# Diagram 08 — Multi-Agentic Team & MIV Technical Architecture

**Status: architecture per DeepSeek's MIV/WhatsApp directive (relayed by
James, 2026-11-09). This version supersedes the earlier Diagram 08 (NEAR AI
core / KVM edge) filed the same day: the Messaging & Intelligence VPS (MIV)
and the Meta-Business/WhatsApp layer are now drawn explicitly. Spec:
`docs/specifications/10-NEAR-AI-CORE-INTENT-ROUTING-KVM-EDGE.md`.
Companion: Diagram 09 (WhatsApp business flow). The MIV/Hermes integration
is NOT built during hackathon week; Sprint 2 (Nov 15) begins it.**

```mermaid
flowchart TD
    subgraph MESSAGING["External Messaging & Target Markets"]
        WA["WhatsApp (Meta-Business API)"]
        X["X.com / Voice Inputs"]
    end

    subgraph MIV["Messaging & Intelligence VPS (Hostinger KVM)"]
        HERMES["Hermes Harness (Orchestrator)"]
        GROK["Grok AI (Sensing & Drafting)"]
        SEC["Untrusted Input Sanitizer"]
    end

    subgraph UZE["UZE Monorepo (NEAR AI Core)"]
        INTENTS["NEAR Intents Router"]

        subgraph AGENTS["Agentic Team (NEAR AI Cloud)"]
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

    WA -->|"Inbound Offers/Inquiries"| HERMES
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

**Reading the diagram.** Two inbound channels reach the MIV on the
Hostinger KVM: WhatsApp through the Meta-Business API (offers and
inquiries from the Brazilian business-owner network and the US East Coast
diaspora) and X/voice through Grok's sensing. Hermes orchestrates on the
MIV; everything it formulates passes the sanitizer before becoming a NEAR
Intent at the core's router. Inside the core, intents route to GIRA,
SURA, or the Juror Team; verdicts write to the Precedent Index and juror
TEE hashes anchor to the contracts. The edge holds no schemas, and drafts
for publication route to James's Double-Tap.
