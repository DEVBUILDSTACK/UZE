# DevPartner Software Stack Portal — Executive Summary

**Concept:** a public-facing, multilingual, self-serve developer portal
at `devpartner.uzemarkets.com` that serves as the technical bridge
between UZEmarkets and its external data partners — software stack
partners, integrated via API, to extend the reach of landowners and
business owners through WhatsApp and messaging-based sources.

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

## Assuraties & the Reliance API — verified claims for financing partners

Partner data tells UZEmarkets what a parcel *is*. **Assuraties**
establish what a financing partner may *rely on*.

Financial packages for income real estate and land rest on advisory
and seller financials that nobody stands behind in any checkable way.
Assuraties turn the load-bearing numbers into **claims**: discrete
assertions — about a real-world asset, a HiCRE property, or a HiCRE
asset's operating period (total operating expenses and historicals) —
each issued by an identified claimant, priced, and backed by a bond.

**The juror pathway.** Claims are judged by AI jurors running on
NEAR AI, inference executed in a trusted, attested environment. A
juror evaluates the claim against its evidence and against precedent:
prior resolved claims in the same micro-region. Any party may
challenge a claim by posting a counter-bond, which escalates it to a
juror panel. Every juror judgment is **anchored on the NEAR
blockchain** — the judgment's digest is written on-chain, so the
verdict a financing partner relies on can be verified against the
chain itself. A claim resolved in its favor, or challenged and
upheld through the process, is finalized as **Assuratized**: the
reliance grade. A confidential tier, **ASSURATIZED @ARCIUM**, covers
claims whose evidence or bids must remain sealed.

**How a financing partner consumes it.** Only Assuratized claims are
served, through the **Reliance API**:

- **An agent** at the financing firm queries the API
  programmatically — identity-verified, payment authorized per call —
  and checks the claim's on-chain anchor before a credit decision.
- **A human evaluator** sees the identical record: the claim, the
  bonds posted for and against it, each juror's report including
  dissents, and the anchor proving the record was not altered after
  the fact.

For a **HiCRE** parcel, the stated operating expenses behind a loan
application arrive pre-judged and verifiable in minutes instead of
weeks of document diligence. For an **ANRD** parcel — agriculture,
natural resources, development — the parcels are polygon-mapped, and
new land surveys configured with IoT (drones, agricultural machinery
telemetry, and robots) generate the survey evidence — boundaries,
soil, and water — that claims are judged against, including the
mandatory subterranean context for land and resource tracks.

The record compounds: every Assuratized claim becomes a comparable —
actual operating results by period, micro-region, and asset class —
and every claimant's track record is locked in the ledger.

**Governance status (binding, per the Evidence-Gated Architecture,
`docs/specifications/06-EVIDENCE-GATED-ARCHITECTURE.md`):** every
partner is an **UNVERIFIED** provider until an agreement is signed and
its API is reviewed. Snapshots are stored with
`provider_status = "UNVERIFIED"`; a snapshot is partner-claimed data
cached for review, never verified fact, and no snapshot triggers
financing, treatment, or auction execution. The downstream
underwriting endpoint shown in the diagrams is design intent for a
later sprint and is **not built**.

**Markets note:** the paired primary markets are Mid-Atlantic
(Baltimore + Washington, DC metro) and South & Central Florida
(Miami, Fort Lauderdale, Tampa, Orlando). UZEmarkets' Mid-Atlantic focus is anchored by Dugan's Wharf in Baltimore — the historic Pratt Street wharf, now Pier 4 of the Inner Harbor, home to the National Aquarium's Marine Mammal Pavilion and a marked Network to Freedom site.

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

## Software Stack Implementations

The providers the stack itself runs on — search, financial data, and
other metered capabilities — are registered separately from data
partners, in [`software-stack-implementations/`](software-stack-implementations/README.md),
with their developer documentation links.
