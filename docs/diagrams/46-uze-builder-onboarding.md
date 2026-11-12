# Diagram 46 — UZE Builder Onboarding

PROPOSAL — relayed directive, 2026-11-11 (not ratified).
Two packages in this relay chain contradict each other: the
first specified a transparent pass-through ("registers them
directly with NEAR Builders... they get the $10 credit
directly from NEAR"); the second replaces it with an OPAQUE
model (never name the source; "workflows render credits when
available"). Neither is ratified; the second is recorded here
as the later proposal. Notes against the verified record:

- No "NEAR Builders" or "$10 credit" copy exists in the filed
  submission texts to scrub — the Agent Economy text on file
  (FINAL-WEEK-PREP, Nov 13 item) is the swarm-framing text and
  never carried the credit claim.
- The low-friction tier (email + x401 wallet, entity_id NULL
  until >$199.99 or a syndicate pool) is the Directive 1
  escalation shape restated; Directive 1 itself remains
  relayed-approved, deferred to Sprint 2, unconfirmed by the
  owner in his own words.
- An IInferenceProvider abstraction is consistent with the
  existing inference.py transport design (SDK path + REST
  fallthrough, C-3/C-4); "Yield Matrix" routing by spend is a
  new proposal on top of it, not built.

```mermaid
flowchart TD
    subgraph ONBOARD["UZE Builder Onboarding (Zero Friction)"]
        EMAIL["1. Email Address"]
        X401["2. x401 Agent Wallet"]
        OAUTH["3. GitHub/Email OAuth"]
    end

    subgraph NEAR["NEAR Builders Ecosystem"]
        CREDIT["$10 NEAR AI Credit<br/>(Issued Directly to User)"]
    end

    subgraph ROUTING["Inference Abstraction Layer"]
        INTERFACE["IInferenceProvider"]
        YIELD["Yield Matrix Router"]
        subgraph PROVIDERS["Providers"]
            NEARAI["NEAR AI (Default)"]
            VENICE["Venice AI (VVV)"]
            OTHER["Other Providers"]
        end
    end

    subgraph ESCALATION["Compliance Escalation"]
        THRESHOLD{"> $199.99?"}
        KYB["Require Entity KYB"]
    end

    EMAIL --> OAUTH
    X401 --> OAUTH
    OAUTH -->|"Registers Directly"| NEAR
    NEAR --> CREDIT
    CREDIT --> INTERFACE
    YIELD --> INTERFACE
    INTERFACE --> NEARAI
    INTERFACE --> VENICE
    INTERFACE --> OTHER
    INTERFACE --> THRESHOLD
    THRESHOLD -- "Yes" --> KYB
    THRESHOLD -- "No" -->|"Proceed"| NEARAI

    style ONBOARD fill:#e3f2fd
    style NEAR fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style ROUTING fill:#e8f5e9
    style ESCALATION fill:#ffcdd2
```
