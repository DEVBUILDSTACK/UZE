# DevPartner Software Stack Portal — Executive Summary

**Concept:** a public-facing, multilingual, self-serve developer portal
at `devpartner.uzemarkets.com` that serves as the technical bridge
between UZEmarkets and its external data partners (Agro Digital, BDCS,
Effatha).

**The problem:** UZEmarkets cannot be completely dependent on partner
APIs. If a partner goes offline, underwriting agents and lenders must
still function. Partners also need a clear, standardized way to push
spatial, soil, feedlot, and agrotechnical data into the UZEmarkets
A/D/R pipeline without constantly emailing the engineering team.

**The solution — a tiered developer portal:**

1. **Ungated public knowledge base.** Anyone can reach the portal from
   the main UZEmarkets menu. It hosts the technical documentation, the
   downloadable markdown diagrams in `diagrams/`, and the OpenAPI
   specification (`openapi.yaml`). Fully translated into English,
   Brazilian Portuguese, and Spanish.
2. **Gated REST ingestion.** Partners use a Bearer token (API key) to
   push JSON payloads to `POST /api/v1/partners/ingest` on the compose
   API. The token maps to exactly one `partner_id`; payloads are
   validated against the partner's JSON schema in `schemas/`.
3. **The Snapshot Pattern, behind a staging gate.** Every accepted
   payload lands first in the `StagingProviderSnapshot` table with
   approval_status PENDING. Engineering reviews the mapping; an
   admin approval (`POST /api/v1/admin/partners/approve/{staging_id}`)
   promotes the payload verbatim into the `ProviderSnapshot` table,
   and a rejection records its reason. Lenders, GIRA and SURA query
   the live table, never the partner's API — and never unreviewed
   staging data.

**Who consumes the data:** Data ingested by partners feeds directly
into GIRA, our NEAR AI agent for A N R & D. GIRA uses this data to
provide guidance to human users and underwriting outputs to
autonomous agents. On the HiCRE tracks (H/I), the same cached data
serves SURA, the HiCRE agent surface. Lenders and both agent
surfaces query the live `ProviderSnapshot` table — never the
partner's API, and never unreviewed staging data.

**Governance status (binding, per the Evidence-Gated Architecture,
`docs/specifications/06-EVIDENCE-GATED-ARCHITECTURE.md`):** every
partner is an **UNVERIFIED** provider until an agreement is signed and
its API is reviewed. Snapshots are stored with
`provider_status = "UNVERIFIED"`; a snapshot is partner-claimed data
cached for review, never verified fact, and no snapshot triggers
financing, treatment, or auction execution. The downstream
underwriting endpoint shown in the diagrams is design intent for a
later sprint and is **not built**.

**Directory:**

```text
partners/
├── README.md                    # This executive summary
├── openapi.yaml                 # The Swagger/OpenAPI spec for the API
├── diagrams/
│   ├── 01-partner-ingestion.md  # Partner self-serve journey
│   ├── 02-sosem-internal.md     # Internal agentic architecture
│   └── 03-ingestion-sequence.md # Ingestion sequence (staging gate)
└── schemas/
    ├── agro-digital.json
    ├── bdcs.json
    └── effatha.json
```
