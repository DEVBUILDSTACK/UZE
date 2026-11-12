# DECISIONS LOG — November 7, 2026

**Purpose:** Capture the ratified decisions made in tonight's session.

---

## D1. Product vertical: income commercial real estate

**Decision:** UZEMARKETS serves income commercial real estate, not travel/venue.

**Three asset classes:**
- Residential rental (30 doors to 1,500–2,000+)
- Residential condo (same scale)
- Hospitality/resort (same scale, short-stay, extended stay only for relocation)

**Supersedes:** The travel-and-venue marketplace framing from Sprint 0.

---

## D2. Two service lines

**Decision:** Two distinct services on one marketplace:
- **Service Line 1:** Assessment and Managed Services Advisory
- **Service Line 2:** Property Manager and Operating Talent Placement

**The advisory feeds the placement. The placement fulfills the advisory.**

---

## D3. Micro-region as analytical unit

**Decision:** All analysis is benchmarked to micro-region, not metro.

**Examples:** Brickell, Aventura, Bethesda, Arlington, Northwest Baltimore, Orlando/Kissimmee, Tampa.

**Schema:** `micro_region_id` FK to `MicroRegion` reference table.

---

## D4. Dual-surface, not headless-only

**Decision:** UZEMARKETS is dual-surface by architecture. One backend, two projections.

**For the hackathon:** Agent surface fully interactive. Human surface read-only for SEO/GEO.

**Supersedes:** The "headless only" framing that appeared in earlier hackathon scoping.

---

## D5. Hackathon extended to November 14

**Decision:** Build through November 13 EOD Eastern. Submit before November 14, 11:29 UTC.

**Supersedes:** The November 10 submission target.

---

## D6. Sprint 1.5 — encapsulated, not a fork

**Decision:** The hackathon is Sprint 1.5. It pulls forward Sprint 2 content. Sprint 2 (filed) is unchanged.

**No prior decision superseded. New framing.**

---

## D7. Repo and branch

**Decision:** Work in `DevBuildStack/UZEMARKETS`. Branch `hackathon/nov-2026`. Merge to `main` by November 13 EOD Eastern.

**UZEMARKETS-International is not touched.**

---

## D8. Demo narrative

**Decision:** The demo is a 340-room Aloft in Miami-Brickell, two bidders (human $22,500 / agent $4,200), cross-chain settlement via Chain Signatures, agent's analysis attested via NEAR AI Cloud, comparable written to micro-region dataset.

---

## D9. Four diagrams in the repo

**Decision:** Four Mermaid diagrams live in `docs/diagrams/`:
- `01-marketplace-flow.md`
- `02-technical-stack.md`
- `03-end-to-end-sequence.md`
- `04-intent-lifecycle.md`

---

## D10. Non-negotiables carried over

These decisions from Sprint 0 carry over into Sprint 1.5 without change:

- Additive migrations only
- From-empty replay before filing
- Statement-identical proof for behavior-neutral edits
- Bidirectional tests for ledger-class bindings
- No tautological tests
- Kitchen Standard
- Frozen migrations never import live application source
- USDC-only settlement invariant (af20ad9)
- No LLM in classify()
- Schema supports both surfaces

---

## D11. Post-hackathon pickup

**Decision:** Sprint 1 resumes November 15. Sprint 2 kicks off November 16. Sprint 2 timeline unchanged.

---

## Standing open items (not decisions — track them)

- Neon provisioning for staging
- Ownership (a)/(b) confirmation
- x402/x401 tier A/B metering spec details
- "Lance" clarification
- Four verticals enumeration
- Divergence code firing map
- R4 read-through affiliates pinning section
- `services/api` redeploy

**None block Sprint 1.5 or Sprint 2 kickoff.**
