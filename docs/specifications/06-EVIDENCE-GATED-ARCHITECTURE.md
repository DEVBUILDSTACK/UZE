<!--
  SPECIFICATION: Evidence-Gated Architecture & Authorization Rules
  Target: SoSem (Implementing Agent), Engineering Team
  Status: Mandatory Governance Rule
  Applies To: All Tracks (H, I, A, D, R), specifically the AgTech and RWA pipelines.
  Filed: 2026-11-08 (DeepSeek specification, relayed by James)
-->

# Evidence-Gated Architecture & Authorization Rules

## 1. Core Principle: Evidence-Gated Transitions

UZEmarkets is an agentic orchestration layer, not an autonomous principal. An incoming intent (e.g., from a WhatsApp webhook or API) can propose an action, but it must not automatically authorize treatment, certify a yield gain, initiate financing, or list land for auction.

Every transition from Advisory to Execution must be gated by evidence, explicit consent, and a state change.

**The Iron Rule: No macroeconomic signal (e.g., fiat_collapse) and no AI calculation (e.g., estimated yield delta) can independently trigger an irreversible transaction.**

## 2. The State Machine (No Shortcuts)

The Python/FastAPI orchestration layer must enforce the following state machine for Tracks A/D/R. The Rust contracts and database must reflect these states.

```text
INTENT_RECEIVED
    ↓
INPUT_VALIDATED
    ↓
SPATIAL_ASSESSMENT_PENDING
    ↓
SPATIAL_ASSESSMENT_COMPLETED
    ↓
PROVIDER_ELIGIBILITY_PENDING
    ↓
PROVIDER_PROPOSAL_RECEIVED
    ↓
FARMER_APPROVAL_PENDING  <-- (Explicit human/entity consent required here)
    ↓
SERVICE_AUTHORIZED
    ↓
SERVICE_REPORTED_ACTIVE
    ↓
OBSERVATIONS_COLLECTED
    ↓
OUTCOME_ASSESSED
```

Allowed Branches (Separately Authorized):

· OUTCOME_ASSESSED → FINANCING_REVIEW (Requires explicit request)
· OUTCOME_ASSESSED → SALE_ELIGIBILITY_REVIEW → LISTING_APPROVAL_PENDING → AUCTION_ADAPTER (Requires explicit owner instruction)

## 3. Schema Rules: Intent vs. Evidence

The Intent table is a summary of the request. It is not the database for treatments, measurements, or verifications.

### A. The Intent Payload (operational_optimization_context)

This JSONB structure must remain lightweight:

```json
{
  "schema_version": "1.0",
  "track": "A",
  "transaction_type": "agtech_referral",
  "crop_type": "CORN",
  "production_purpose": "SILAGE",
  "provider_preference": "EFFATHA",
  "provider_status": "UNVERIFIED",
  "requested_next_action": "ELIGIBILITY_ASSESSMENT",
  "consent_record_ids": ["<uuid>"],
  "outcome_status": "NOT_ASSESSED"
}
```

### B. Linked Records (The Evidence)

Do not overwrite Intent data. Create separate, linked tables for:

· SpatialAssessment: Stores geometry, registry matches (e.g., CAR), and confidence scores.
· ProviderProposal: Stores what the provider offers and for how much.
· Observation: Stores metric, value, unit, method, source (e.g., provider_reported vs. instrument_measured).
· AIAssessment: Stores the model version, input evidence references, estimated difference, and review_status. Never equate signed = true with scientifically_verified = true.

## 4. Adapter Rules (Partners & Protocols)

Until commercial agreements and technical documentation are signed and reviewed, external integrations are Unverified Adapters.

· Agro Digital: Build behind an ISpatialProvider interface. Use a mock adapter for the hackathon. A spatial match (GeoJSON to CAR) does not establish land ownership.
· Effatha: Build behind an IAgTechProvider interface. Do not assume a treatment API exists. Treat the flow as a referral/eligibility request.
· Arcium Auction / Altitude Treasury: Keep auction execution and USDC settlement as distinct stages. A listing is not a sale.
· x401 / x402: Treat as unresolved protocol dependencies. Separate attestation logic from billing middleware until specifications are confirmed.

## 5. Directive to SoSem

Execute the following steps immediately:

1. File this document: Save the text above as docs/specifications/06-EVIDENCE-GATED-ARCHITECTURE.md.
2. Update the Diagram: Check for docs/diagrams/05-agtech-cattle-stack.md. If it exists, update it to reflect this state machine (showing the FARMER_APPROVAL_PENDING gate). If it doesn't exist, note it and create it based on this spec.
3. Refactor API Routes: Ensure POST /api/v1/webhooks/agriculture/intent enforces idempotency, authentication, and the INTENT_RECEIVED state.
4. Mock External Calls: Ensure any code hitting Effatha, Agro Digital, or Arcium is mocked and returns a PROVIDER_ELIGIBILITY_PENDING status rather than auto-executing.
5. Update Narrative Docs: Apply these constraints to SUBMISSION.md and DEMO-SCRIPT.md so the demo explicitly shows the human/entity approval gate before financing or sale.
6. Return to Trust Layer: Once this governance spec is filed and the code reflects these state boundaries, return to the Assurative V2 Trust Layer and Compose identity resolution.

Proceed on standing authority.
