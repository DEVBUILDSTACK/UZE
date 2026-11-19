# P2 Assessment — Scope and Phased Sprint v0.1 (Separated Track)

**Status: SEPARATED TRACK — FOR JAMES'S TAP.** This document consolidates the P2 Assessment track into a single build-order instrument. **It authorizes nothing by itself**: no build begins before James's tap on this track, and the tap — when it comes — authorizes no send, no spend, no rail enable, and no real grant; those keep their own gates. P2 is **Scope 2** in the consolidated set. Per James's direction it stands **separate** from the merged P1 + P3 program (`docs/merged/P1-P3-MERGED-SCOPE-AND-PHASED-SPRINT-v0.1.md`); its seam with that program is specified in §5 of this document and nowhere else.
Produced by SoSem, 2026-11-18.
**Addressee:** James.

**Sources consolidated:** `P2-SCOPE-AND-SPEC-v0.1.md` (James's specification, including its composite-ingestion amendment and outcome note); `ADDENDUM-P2-ATTESTATION-AND-ACCESS-2026-11-18.md` (including James's Gradify confirmation correction); `DEEPSEEK-COMPOSITE-FEEDBACK-2026-11-18.md` (Part B, esp. B.6); `DIAGNOSIS-COMPOSITE-FEEDBACK-2026-11-18.md` (the adopted corrections, and its outcome section recording DeepSeek's response to the diagnosis); the merged program's §5 (M1, M3) and §6 (the P2 seam, incl. amendments S1–S2). **Where the sources differ, the latest governing correction governs and is named where it applies**: the two-gate model (§2.3) supersedes the single gate of the original spec; the template-moat generation model (§2.2) corrects the attestation addendum's frontier-agent-authors-the-spec model; the pinning-home sequencing (§2.6, §5) follows the diagnosis outcome — Filebase/Pinata operating, UZE-IPFS conditional target — over the composite's earlier framing.

---

## 1. The track in one paragraph

An engaging employer configures a role; agents build a skills assessment for that role **from a curated template library** — role-signal extraction, template selection, slot-filling, calibration against a reference population; **two human gates**, both console-only and human-signed, stand between generation and any run — the employer confirms intent, a per-vertical approver of record confirms validity; assessed talent is fulfilled through the autonomous market (Path A) or a pre-gated client engagement (Path B); and every engagement carries a published copy on the shared publication layer under a hard redaction rule — visibility of work, invisibility of people. The track's records key to the Role × Realm taxonomy the merged program's M1 enforces, and its outcomes are what activate the merged program's three Talent MCP tools (§5).

## 2. Scope — the assessment pipeline

### 2.1 Role configuration

The engaging employer — human or agentic — submits and configures the role: vertical, title, seniority, skills, judgment dimensions, market, engagement mode, budget. The configuration lands as a structured Role record keyed to the **Role × Realm taxonomy of record** (the pairs M1 enforces). Work history is a required input on the talent side (§3, Sprint 2 carries its attestation layer). Access to configure is itself gated and paid — the access gate of §3 (P2-9): KYC/KYB first, then the access products.

### 2.2 Generation — the template moat

Generation **fills slots in curated templates; it does not author instruments**. Four stages, in order:

1. **Role-signal extraction** — the configured role is reduced to the signals that select and parameterize an instrument.
2. **Template selection** — from a **curated template library**, per vertical × role (a hospitality role is assessed as hospitality; an H&I CRE financial-underwriting role is assessed on financial statement analysis, valuation, and DealFi-style acquisition screens — the worked example of record in the attestation addendum).
3. **Slot-filling** — content per vertical fills the selected template's slots.
4. **Calibration** — the instrument carries a calibration record against a reference population. Without this stage there is a test, not an instrument.

### 2.3 The two gates

Both gates are **console-only, human-signed**, and recorded as Events. Neither can be performed by an agent, on any surface — the MCP surface (§5) inherits them unchanged.

- **Gate 1 — Employer confirmation of intent.** The configuring employer confirms: *this assessment is for the role we configured.* Rejection returns the role to generation/reconfiguration; nothing is assessed against an unconfirmed role.
- **Gate 2 — Approver-of-record confirmation of validity.** A **per-vertical** approver confirms: *this is a valid, calibrated instrument for this vertical.* The approver is a named human with the competence the vertical requires (a CRE reviewer has a financial-underwriting background; a smart-contract reviewer has audit experience) and the time to reject — approver competence is a governance requirement, not a courtesy. The approver may confirm, edit, or regenerate. The approver of record per vertical is ruling 6 (§6).

### 2.4 The run — scoring is the center

Scoring is the center of the layer; if scoring is wrong, the flow around it is decorative. The run's stated mechanics:

- **AI grade** on every run, with a **human-review flag** and a **stated threshold** for automatic human review (borderline results route to a human; the flag is part of the result, not an afterthought).
- The result is **keyed to the Role × Realm pair** it was earned against.
- **Validity is claimed only in one form**: *"calibrated against reference population X with metric Y."* Stratified calibration, or an explicit acknowledgment of the gap — no surface may call an assessment "valid" without the named population and metric.
- **Retake policy: one retake per six months, maximum two total, logged.** (A parameter of record; James may adjust it.)

### 2.5 Fulfillment — the two paths

- **Path A — the autonomous market.** The talent is a **UZE Markets paid employee**; the client is billed the labor rate **plus a markup** set per labor market. Starting parameters of record (James, 2026-11-18 — adjustable per engagement, never silently changed; recorded on the engagement before work begins): **India 17.5%–23.5%**; **Singapore help desk from 33.75%**; other markets per ruling 5 (§6).
- **Path B — pre-gated client engagements.** The engagement is **accepted** and an **advance is held on account** before fulfillment runs, under the commercial models of record: **outstaffing** (UZE pays the talent, bills the client) or **placement** (fee of at least one month — 30 days — of salary; the client pays the individual directly). The advance is the deposit leg of the confidentiality doctrine (§2.6).

### 2.6 Publication and disclosure

Every engagement carries a **published copy** — its terms of record and its progress/activity, viewable as it proceeds — on the shared publication layer (§5), under the **hard redaction rule: no talent names, no talent or agent email addresses, no company names — ever.** The public copy proves the engagement exists and is progressing; it identifies nobody. The architecture that enforces this is §4.

**Disclosure timing, stated as design:** the client sees the assessment **outcome under an engagement-scoped pseudonym before signing**; the talent's **identity is revealed at engagement + deposit** — the same moment the confidentiality doctrine permits exposure in either fulfillment path, and not before.

## 3. The phased sprint

Two sprints. Sprint 1 is the composite's **reordered 13-day sequence** (B.6), restated as phases P2-1–P2-7 with exits. Sprint 2 carries the attestation layer, the access gate, further verticals, and the calibration population (P2-8–P2-11). Each phase starts on the track's tap and its own sequencing; durations are the composite's, recorded as estimates, not commitments.

### Sprint 1 — the core loop (13 days)

**P2-1 — Role config schema + intake UI** *(Day 1; composite B.6).*
- The role-configuration schema (§2.1) and the employer intake surface; configurations land as structured Role records keyed to Role × Realm pairs.
- **Exit:** a real role is configured end-to-end and stored as a keyed Role record.

**P2-2 — Assessment generator + template library seeded** *(Days 2–4).*
- The four-stage generator (§2.2) built for the two seed verticals — **hospitality** and **CRE underwriting** — with the curated template library seeded for both.
- **Exit:** for each seed vertical, a configured role produces an instrument through extraction → selection → slot-filling, carrying its calibration record.

**P2-3 — Two-gate console** *(Days 5–6).*
- Gate 1 (employer intent) and Gate 2 (approver validity) as console-only, human-signed steps (§2.3); rejection at either gate returns the instrument to generation; every decision and its signer recorded as an Event.
- **Exit:** no instrument reaches a run without both signatures; a rejection at each gate is demonstrated to return the instrument to generation.

**P2-4 — Talent-run UI + scoring** *(Days 7–8).*
- The candidate run surface and the scoring center (§2.4): AI grade, human-review flag at the stated threshold, result keyed to the Role × Realm pair, retakes enforced and logged per the retake policy.
- **Exit:** a run grades end-to-end; a borderline result demonstrably raises the human-review flag; a third retake is refused by the policy, and the refusal is logged.

**P2-5 — Publisher + public viewer** *(Days 9–10).*
- The publication pipeline (§4) on the shared publisher (§5) — redaction isolated by construction — and the public engagement view (terms + progress/activity, redacted).
- **Exit:** an engagement publishes with the minimum-anonymity-set check passing; the publisher is demonstrated to hold **no identity-store read path** (§4).

**P2-6 — Rate/markup engine** *(Day 11).*
- Quote composition from the band structure (§2.5): labor rate + markup per market, placement-fee terms for Path B; the composed terms **lock onto the engagement before work begins** and are recorded on it.
- **Exit:** a quote composes from the starting parameters of record and locks; no engagement starts work on unlocked terms.

**P2-7 — End-to-end loop proof** *(Days 12–13).*
- The full loop on a real role: **role → spec → gates → run → score → publish → quote.**
- **Exit:** the loop completes with both gates signed, the outcome published redacted, and the quote locked. **This exit is also the merged program's activation event** (§5): the first assessment outcome published under the two gates is the trigger (amendment S2) for the three Talent MCP tools.

### Sprint 2 — attestation, access, breadth

**P2-8 — The attestation layer.**
- Work history (a required assessment input, §2.1) becomes a proprietary **on-chain attestation of work experience**, tiered by education level: **post-high-school**, **post-college / university**, **post-master's** — attesting what the person has actually done in work environments in those roles after each level.
- **Partner rail of record: Gradify** — Gradify Labs' credentials-on-chain rail (Gradify University) — named here per **James's confirmation on file** (2026-11-18, in the attestation addendum): the aid his dictation rendered as "Tridesh" is **Shradesh Jodawat**, founder of Gradify (G-R-A-D-I-F-Y, with a D). Shradesh Jodawat is a distinct person from Shradhesh Jain, the full-stack developer; the two are never conflated.
- **Exit:** a work-history record issues attestations at the applicable tier(s) on the Gradify rail, keyed to the talent's record without entering the publication store (§4).

**P2-9 — The access gate.**
- **Identity first:** every configuring employer — human or agentic — completes **KYC/KYB**, as a client or as an affiliate, before access.
- **Two access products, not two payment methods:** **x402 meters candidate-runs** (casual use — the first-time employer, burst hiring); **NEAR staking buys a builder access window** (platform commitment — the long-term, repeat employer). **Combined use earns the best rate.**
- **Documented-relationship rule:** the affiliate-vs-client differential (an employer who is an affiliate before becoming a client receives the affiliate rate; a direct client is offered the affiliate path) is governed by a documented-relationship rule — without it, the differential inverts into discount arbitrage.
- This layer is distinct from fulfillment billing (§2.5): access pays for building and running assessments; fulfillment pays for the talent.
- **Exit:** an employer passes KYC/KYB and obtains access under each product; the differential is shown to follow the documented relationship, not the order of asking.

**P2-10 — Further verticals.**
- The template library and generator extend beyond the two seed verticals, each new vertical carrying its own template set, calibration record, and per-vertical approver (§2.3).
- **Exit:** one further vertical runs the full Sprint 1 loop (configure → generate → gates → run → score → publish) without new machinery.

**P2-11 — Calibration population.**
- The reference populations the validity claim names (§2.4) are built out and maintained: stratified calibration where the population supports it, explicit gap acknowledgment where it does not.
- **Exit:** every live instrument's validity statement names a reference population and metric that exist in this layer — or carries the explicit gap acknowledgment.

## 4. Redaction as architecture

Redaction here is **construction, not policy** — the publisher cannot exfiltrate identities because it never had them.

- **Three-store separation.** **Identity store** — PII, DID-to-name mapping; never touched by the publisher. **Engagement store** — facts keyed to DIDs; no names. **Publication store** — the published projection; a different process, different secrets, different DB credentials. **The publisher has NO identity-store read path.**
- **Triangulation mitigation.** "No names" does not equal "unidentifiable" — a single engagement's milestone timeline can identify the talent to a reader with independent knowledge. Mitigations, all mandatory: **coarse bucketing** (day, not hour; banded amounts), **aggregate-first publication**, a **minimum-anonymity-set threshold (e.g. 5)** below which an item does not publish, and **engagement-scoped pseudonyms** (the same pseudonym discipline as the disclosure rule, §2.6).

## 5. The seam to the merged program — tonight's state

The merged P1 + P3 program touches this track at exactly three interface points (merged §6), and nowhere else. Stated with **tonight's actual state (2026-11-18)**, which postdates the merged document's filed state of record:

1. **Assessment records → placement (M1).** **M1 is BUILT**: the Role × Realm taxonomy and engagements are live in the Dev Library. This track's assessment records key to the **Role × Realm pairs M1 enforces** — the interface is the keyed record, not a shared build. Until this track lands, M1's placement runs **desk-mediated** (amendment S1: the desk makes the staffing call on the built Scope 1 data as supporting evidence, not as a gating signal); when this track lands, the assessment record assists the desk's call.
2. **The three Talent MCP tools (M3).** **M2 is BUILT**: `submit_assessment(role_config)`, `score_assessment(talent_did, assessment_id)`, and `publish_assessment_outcome(assessment_id)` are **in the catalog, dark**. They activate on this track's demonstrable trigger (amendment S2): **the first assessment outcome published under the two gates** — which is Sprint 1's exit event (P2-7). The tools' gating inherits the two console-only human gates unchanged; the console remains a view over the API, never a parallel path (dual-surface contract).
3. **The publisher — shared.** One publication layer serves both programs. **Filebase/Pinata is the operating pinning home**; **UZE-IPFS** (real IPFS on NEAR Cloud) is the conditional target state, gated on the **four-point P0 verification** (persistent CID-verifiable nodes; retrieved CID = published CID; persistence guarantees; per-GB-pin cost inside the Markets envelope) **and NEAR AI Cloud credits**. A bucket is never labeled IPFS. This track owns its redaction spec (§4); the merged program consumes the publisher as a service.

No merged phase blocks on this track except Talent-tool activation, which is designed to ship dark. This track's tap and rulings (§6) are its own; the merged program's tap did not adopt them and does not move this track.

## 6. Rulings carried for James on this track

Three of the consolidated seven rulings belong to this track. They are **James's individually**; nothing in this document or in the merged program's tap settles them.

| Ruling | Governs | Recommendation of record |
|---|---|---|
| **5 — Markup-bands framework** | Path A pricing (§2.5); P2-6 | Publish the framework now with the starting parameters of record (India 17.5%–23.5%; Singapore help desk from 33.75%); fill the remaining markets quarterly (Q1 2027: US, UK, EU, LATAM, SEA, EMEA) |
| **6 — Approver of record per vertical** | Gate 2 (§2.3), from track entry | Named **at track entry**, per vertical, **with a stated deputy** |
| **7 — IPFS home** | Publication (§2.6, §4, §5) | **UZE-IPFS as target state / Filebase-Pinata as operating home**, per the diagnosis outcome |

**Gates restated.** On this document: nothing. On James's tap of this track: the phased sprint of §3 becomes this track's build order. What does **not** happen on the tap: any send, any spend, any rail enable, any real grant. Those keep their own gates, here as everywhere.

## 7. Invariants carried from v3.1

- **Status is derived, never written**; every transition emits a chronicle **Event** — gate decisions, scores, retakes, publications, and revocations included.
- **The human gates are hard gates**, in the same class as v3.1's human-`promotedBy` ladder rule: no agent action substitutes for a named human's signature.
- **Revocation cascades atomically** at the next boundary — access, engagements, and publication rights revoke together, never piecemeal.
- **Markup and fee parameters are engagement terms** — recorded on the engagement before work begins, visible in its published copy only as the redaction rule allows (figures yes, identities no).
- **The talent is never exposed** — no identity or contact information in either fulfillment path — before a signed engagement and the deposit/advance are both in hand.

---

*Prepared by SoSem, 2026-11-18. Filed records govern over summaries of them; the sources listed in the header are this document's authorities, and where they are amended by later filed corrections, those corrections govern.*
