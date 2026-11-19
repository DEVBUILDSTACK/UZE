# Merged P1 + P3 — Scope and Phased Sprint v0.1

**Status: TAPPED by James, 2026-11-18 20:17 ET — with amendments A1–A6.** This document, as amended by the audit-ingestion section at its end, is the build order for Scopes 1 and 3. The tap authorizes no send, no spend, no rail enable, no real grant, and not the Phase 6 open-repo gate; those keep their own gates. The seven rulings in §7 remain James's to rule individually; the tap adopted the amendments, not the rulings. M0-A step 1 (state confirmation, per C7) is complete — record at `docs/merged/M0A-STATE-CONFIRMATION-2026-11-18.md`; M0-A's remaining steps wait on the two owner acts named there.
Produced by SoSem, 2026-11-18, on James's directive of 20:05 ET: a full SoSem detailed merge of the P1 and P3 Scope(s)/Phased Sprint(s).
**Addressee:** James.

**Label mapping (read first).** In James's labels: **P1 = Scope 1** — the Talent platform / UZE Dev Library line (directive v3.1; `docs/talent/`). **P3 = Scope 3** — UZE Instant MCP (`docs/instant-mcp/`), the new scope, accepted as filed when the DeepSeek diagnosis loop closed on 2026-11-18. **P2 = Scope 2 (P2 Assessment) is SEPARATED** — per James's direction it is addressed on its own track and is **not** merged here; its seam with this program is specified in §6 and nothing else in this document governs it.

**Standing note (added 2026-11-18, per audit item C1):** "Phase N" references in documents prior to 2026-11-18 mean the directive v3.1 phase, not this merge's M-phases and not the scope numbers. Read older documents' phase numbers through the v3.1 mapping.

**Naming correction (James, 2026-11-18 21:38 ET — governs all reporting):** the standard naming is **Scope 1, Scope 2, and Scope 3**, with each scope's own phases. The "M" labels used inside this document (M0–M5) and the phrase "merged program" are **not** James's naming and are not to be used in reports to him; they survive in this document only as internal cross-references, translated here once: **M0-A = Scope 1 close-out items** (Resend placement, mailer, master token, owner OTP test) · **M0-B = Scope 3 Phase 0** (verification) · **M1 = Scope 1 Phase 3** (dual-track placement + Role × Realm taxonomy) · **M2 = Scope 3 Phase 1** (core MCP + Instance tier) · **M3 = Scope 1 Phase 4 + Scope 3 Phase 2** (settlement substrate, then Markets vertical tools) · **M4 = Scope 3 Phase 3 + Scope 1 Phase 5** (directory listings + hardening) · **M5 = Scope 3 Phase 4 + Scope 1 Phase 6** (compatibility matrix + the open-repo gate). Reports to James name scopes and their phases only.

**Sources merged:** Scope 1 — `CONSOLIDATED-SCOPE-v3.1.md`, `BUILD-SCOPE-AND-PHASED-SPRINT-v1.0.md`, the Vercel-DB/permissions addendum, the talent commercial-models addendum (all `docs/talent/`). Scope 3 — `SCOPE-3-UZE-INSTANT-MCP-SCOPE-AND-PHASED-SPEC-v0.1.md` as amended by the composite ingestion and the diagnosis outcome (`docs/talent/DIAGNOSIS-COMPOSITE-FEEDBACK-2026-11-18.md`, `DEEPSEEK-RESPONSE-DIAGNOSIS-FIXES-2026-11-18.md`). Where this merge and a source differ, the source governs until James taps the merge.

---

## 1. The merged program, in one paragraph

One platform, two surfaces. **Scope 1 is the system of record**: the permissioned talent platform — discovery (the Dev Library), placement (dual-track), settlement (escrow) — with its human surface, its chronicle, and its developer/talent data layer already built and live. **Scope 3 is the productized access layer over that platform and its sibling verticals**: one MCP endpoint, two tiers, a tier-gated tool catalog, sold through the AI directories. The Dev Library is where humans browse, configure, and sign; the Instant MCP is where agents discover, provision, and call. They share one Event store discipline, one gating pattern, one rail law, one storage doctrine, and one operator. Merging the scopes merges the build order — it does not merge their taps, and it does not pull the separated P2 track into either.

## 2. State of record, per scope

**Scope 1 (P1) — built in part, live in part.**
- Phase 0 (extension/scope): FILED. Phase 1 (reading room / Dev Library): **BUILT, DEPLOYED, DB-BACKED** — live at dev.uzemarkets.com behind the email-allowlist gate; Neon Postgres attached and seeded (5 professionals + owner test persona, 59 repo grants); rehearsal 40 passed / 0 failed; the Resend mailer, webhook receiver, and lifecycle engine are built.
- Outstanding on Scope 1 as filed: the Resend key placement (values held in a paused session; two routes to completion, both James's — see §7), `LIBRARY_MASTER_TOKEN` unset (admin API closed in production), the owner OTP end-to-end test (runs the moment the mailer arms). Phases 2–6 not started; **Phase 2 is the separated P2 track** (§6); Phase 6's gate is closed by James's own design until placement + payment are proven live and he taps it open.

**Scope 3 (P3) — filed, diagnosed, inert.**
- Scope + phased specification v0.1 filed; DeepSeek composite feedback #1 ingested; the diagnosis loop closed with all five discrepancies (X1–X5) fixed or reframed. The catalog stands at **9 base + 9 vertical = 18 tools**; Filebase/Pinata is the operating pinning home with UZE-IPFS as the conditional target state; the directory recommendation is the two-tier structure; the "<30 seconds" figure is withheld pending measurement.
- Outstanding on Scope 3: James's tap and the **seven rulings** (naming; directory priority; publish_redacted placement; premium structure; markup framework; approver timing; IPFS home). Nothing in Scope 3 has been built.

## 3. Why the merge is one program, not two

1. **Scope 3's Markets tier sells access to what Scope 1 operates.** The Talent vertical tools (`submit_assessment`, `score_assessment`, `publish_assessment_outcome`, `sealed_bid_assignment` on talent engagements) are calls into the talent platform's placement and settlement machinery. Without Scope 1's Phase 3/4 substance (dual-track placement, escrow settlement), the Markets tier's talent surface is a catalog without an operation behind it.
2. **Scope 1's settlement phase and Scope 3's settlement tools are the same machinery at two surfaces.** Escrow creation and milestone release exist once — in the platform — and are exposed to humans through the console and to agents through the MCP, per the dual-surface contract: the console is a view over the API, never a parallel path.
3. **The gating pattern is identical.** User pre-authorization limits, enforcement before execution, vertical-side gates, revoke cascade at the boundary — Scope 1's lifecycle/revoke machinery and Scope 3's three-layer gating are one pattern with two instances. Building them once, in one sequence, prevents the drift that two separate sprints would guarantee.
4. **The dependencies are shared.** NEAR AI Cloud (compute + the credits blocker), the storage doctrine (Filebase/Pinata operating; UZE-IPFS conditional), the rail law, the chronicle/Event discipline, and James's gates bind both scopes identically. One phased sprint sequences those dependencies once.

## 4. Shared foundations (stated once, governing both scopes)

- **Chronicle.** Every action — human or agent, executed, refused, or revoked — is a chronicle Event in one discipline. Status is derived, never written. The audit trail is the same store pattern for a developer's lifecycle transition and an agent's tool call.
- **Gating.** Three layers wherever value or access moves: (1) the principal's pre-authorization with explicit limits, (2) enforcement before execution, (3) the vertical's own gates, never bypassed. Revocation cascades atomically at the next boundary. Human gates (the class of the human-`promotedBy` rule; P2's two gates on the separated track) are never delegated to an agent.
- **Dual-surface contract.** Autonomous-first for money and execution (the API is the contract); human-first for judgment (configuration, approval, borderline review). The console is a view over the API.
- **Rail law.** USDC on Solana is the default for everything; cascade USDC Base → USDG Robinhood Chain → Tempo/Stripe CASH only where none of the first three is available, and never inside SigLayer/TradeLayer. x402 meters per-call; NEAR staking buys access windows; the two are distinct products. Settlement of record conforms everywhere in this program.
- **Storage.** Filebase/Pinata is the operating pinning home. UZE-IPFS (real IPFS on NEAR Cloud) is the target state, conditional on the four-point P0 verification (persistent CID-verifiable nodes; retrieved CID = published CID; persistence guarantees; per-GB-pin cost inside the Markets envelope) and on NEAR AI Cloud credits. A bucket is never labeled IPFS. Publication is redaction-by-construction: three-store separation, triangulation mitigation, minimum-anonymity-set checks.
- **Access regimes.** NoGate for base provisioning (identity = agent's email; credential = wallet payment signature). The separated P2 track's KYC/KYB for configuring employers applies on that track. Markets-tier tool access is governed by the §4 gating, not by a second identity regime (Scope 3 open item 5 / ruling set, James's to confirm).
- **Naming.** Product names per Scope 3 §1 (subject to ruling 1). Keys and secrets carry descriptive names with environment (testnet/mainnet; sandbox/production), date, and a reason word for a same-day second key, per James's convention of record.
- **Boundaries.** The DeepSeek information boundary holds (labels only in external material). No correspondence or credentials in any repo. Nothing publishes, sends, spends, or enables a rail without the applicable tap from James.

## 5. The merged phased sprint

Merged phases are labeled **M0–M5** so they never collide with either scope's own phase numbers. Each entry names its source phases, its deliverables, and its exit criteria. Each merged phase starts on its own tap, per the standing cadence.

### M0 — Arming and verification
*Sources: Scope 1 close-out items; Scope 3 Phase 0.*
- Scope 1: Resend key + webhook secret placed (either route, §7) → deploy dispatched → mailer verified armed; owner OTP end-to-end test completed at dev.uzemarkets.com; `LIBRARY_MASTER_TOKEN` placed and the admin API opened.
- Scope 3 P0: NEAR AI Cloud provisioning verified end-to-end (API surface, KVM tiers, **actual spin-up time measured** — the number, whatever it is, replaces the withheld claim); the four-point IPFS verification run (or its failure recorded, making Filebase/Pinata permanent); MCP protocol conformance spike against the Claude reference implementation; the NEAR credits resolution path stated (credits are the shared blocker for live NEAR surfaces).
- **Exit:** the Dev Library sends real mail through its own wire and the owner test passes; Scope 3's factual basis (provisioning, timing, storage, credits) is measured, not asserted.

### M1 — Scope 1 Phase 3: dual-track placement + Role × Realm taxonomy
*Source: Scope 1 Phase 3 (the separated P2 track is Phase 2 — not in this merge, §6).*
- Track A (internal technical, never placed) and Track B (external placement: AUG/OUTSTAFF/PLACE/PROJECT × REMOTE/HYBRID/MIXED/ONSITE) live in the platform, with the commercial models of record (outstaffing — UZE pays talent, bills client; placement — fee of at least one month's salary, client pays the individual) and the confidentiality doctrine enforced by the desk (no identity exposure before signed engagement + deposit).
- The Role × Realm taxonomy (11 Roles × 6 Realms, up to five pairs, PRIMARY→QUINARY) enforced in data and UI; developer lifecycle and roadmap binding carried from the built phases.
- **Exit:** a Track B engagement can be opened, staffed blind through the desk, and tracked end-to-end in the console — settlement itself lands in M3.

### M2 — Scope 3 Phase 1: core MCP + Instance tier
*Source: Scope 3 Phase 1.*
- The endpoint at `mcp.uzemarkets.com`: wallet-bound auth, the **9 base tools** (5 core + 4 settlement), x402 per-call metering, pre-authorization limits with MCP-side enforcement, revoke cascade, every call a chronicle Event. Own-docs/direct-config listing live from this phase.
- **Exit:** an external agent (Claude reference client) provisions, meters, and terminates a UZE Instance against the real endpoint, inside user-set limits, with the full call history in the chronicle.

### M3 — Settlement substrate, then Markets vertical tools
*Sources: Scope 1 Phase 4 (NEAR marketplace + escrow); Scope 3 Phase 2 (Markets tier).*
- First the substrate: NEAR-intent marketplace mechanics and escrow milestone settlement operating in the platform (the same machinery M1's engagements settle through), rails per the rail law.
- Then the Markets tier's vertical tools on top of it: the six trading/SigLayer/Arcium tools (`sealed_bid_assignment`, `open_position`, `close_position`, `sign_attestation`, `open_dispute`, `publish_redacted`) executing strictly inside the verticals' own gates. The three **Talent tools are built against the separated P2 track's interfaces and activate when that track lands** (§6) — they ship dark, not absent.
- **Exit:** a Markets-tier agent completes an escrow-backed engagement settlement and one vertical operation end-to-end, inside limits, with unwind paths demonstrated.

### M4 — Discovery + hardening I
*Sources: Scope 3 Phase 3 (directories); Scope 1 Phase 5 (hardening).*
- Directory listings in the two-tier order (ruling 2): Tier 1 Anthropic → Smithery → Cursor/Windsurf; Tier 2 OpenAI → Perplexity → DeepSeek → Venice → Kimi → Hostinger → community. Uniform listing content; no unmeasured claims (X5 discipline).
- Platform hardening across both surfaces: tenant/agent isolation adversarial pass, limit-enforcement and revoke-cascade testing, redaction/triangulation audit of everything published.
- **Exit:** listings live in Tier 1; the hardening report is filed with evidence, not narrative.

### M5 — Compatibility matrix + the open-repo gate
*Sources: Scope 3 Phase 4; Scope 1 Phase 6.*
- Compatibility matrix executed per client (Claude reference; OpenAI function-call parity; Gemini parameter encoding; popular open-source MCP clients). Compatibility is claimed only for green cells.
- Scope 1 Phase 6 — the open-repo gate — is **James's tap alone**, on its filed conditions: HR placement + payment proven live (M3's exit is the evidence). Nothing in this merge opens it.
- **Exit:** the matrix is published with its evidence; the gate decision is James's, taken on the M3 record.

## 6. The P2 seam (Scope 2 — separated, per James's direction)

The P2 Assessment scope/phased sprint stands **separate** from this merge and is addressed on its own track (James: focus of late this evening into tomorrow's build, alongside the AEInfo track). This merged program touches it at exactly three interface points, and nowhere else:

1. **Assessment records → placement.** M1's placement machinery consumes assessment outcomes keyed to Role × Realm pairs from the P2 track's system of record. Until that track lands, placement runs on the platform's existing signals; the interface is the keyed record, not a shared build.
2. **The three Talent MCP tools.** M3 builds them against the P2 track's published interfaces (assessment state machine, two-gate flow, publisher) and they **activate when the P2 track lands** — the tools' gating inherits P2's two console-only human gates unchanged.
3. **The publisher.** One publication layer serves both programs (Filebase/Pinata operating; UZE-IPFS conditional target). The P2 track owns its redaction spec; this program consumes the publisher as a service.

No merged phase blocks on the separated track except Talent-tool activation in M3, which is designed to ship dark. The P2 track's tap, rulings (5–7 in the consolidated set), and 13-day sprint are its own.

## 7. Rulings and gates carried into the merge

| Item | Governs | State |
|---|---|---|
| Ruling 1 — tier naming | M2 onward (all public surfaces) | James's; DeepSeek recommends as proposed |
| Ruling 2 — directory priority | M4 | James's; two-tier structure recommended |
| Ruling 3 — publish_redacted placement | M3 | James's; Markets-only recommended |
| Ruling 4 — premium structure | M2/M3 metering | James's; per-call + % of notional recommended |
| Ruling 5 — markup framework | M1 (placement pricing) | James's; publish-now/quarterly-fill recommended |
| Ruling 6 — approver of record timing | Separated P2 track (noted here for the M3 seam) | James's; name at Phase 3 entry recommended |
| Ruling 7 — IPFS home | M0 verification; all publication | James's; UZE-IPFS target / Filebase-Pinata operating recommended |
| Resend placement | M0 entry | Two routes open, both James's (live-browser sign-in, or placement from his own sessions) |
| LIBRARY_MASTER_TOKEN | M0 | James-provided value |
| NEAR AI Cloud credits | M0, M3 | Org credits outstanding; resolution path stated in M0 |
| Scope 1 Phase 6 gate | M5 | James's tap alone, on filed conditions |

## 8. Sequencing note — the AEInfo track and tonight's focus

Per James's direction of 2026-11-18: the P2 scope is addressed separately beginning late this evening, and the imminent build focus is the **AEInfo track — completing the mocks of the global football / American soccer development to go live, followed by the other currently supported World.xyz surfaces — under the placeholder brand naming "AEInfo-Prediction UZEmarkets."** This merged program's sprints sequence behind that focus; nothing in this document displaces it, and the merge is filed so the program is ready to run when James turns to it.

## 9. Invariants (restated once for the merged program)

Every transition emits an Event; status is derived, never written. Revocation cascades are atomic at the boundary. Human gates are signed by named humans and never delegated. Redaction is by construction, and publication never carries names, emails, or company names. The talent is never exposed before signed engagement + deposit. Agents act only inside their principal's pre-authorized limits, and James's gates bind every publish, send, spend, and rail enable across both scopes. Filed records govern over summaries of them.

---

*Prepared by SoSem, 2026-11-18. The merge is a planning instrument: on James's tap it becomes the build order for Scopes 1 and 3, each phase starting on its own tap, with Scope 2 (P2) proceeding on its separated track.*

---

## Amendment — DeepSeek audit ingestion (2026-11-18, by addition)

DeepSeek's audit of this merge is filed as received at `docs/merged/DEEPSEEK-AUDIT-MERGED-P1-P3-2026-11-18.md`. SoSem verified the audit against the filed record; its verdict (structurally correct) stands, and the following amendments are **adopted into the merge**, effective on James's tap. Two carry SoSem's qualifications, noted inline.

**A1 — M0 splits into M0-A and M0-B.** §5's M0 is replaced by: **M0-A** (Scope 1 close-out: Resend placement → deploy dispatched → mailer verified armed → owner OTP test → `LIBRARY_MASTER_TOKEN` placed → admin API opened). Unblocked now; ~30 minutes once the values are in hand. The placement act is James's; the dispatch and verification are SoSem's. **M0-B** (Scope 3 P0: provisioning verification + spin-up measurement, four-point IPFS verification, MCP conformance spike, credits path) — blocked on NEAR AI Cloud credits; sequences when credits resolve. M0-A's completion no longer waits on M0-B; the merged sprint begins with M0-A closed and M0-B queued.

**A2 — M2's exit gate proves the gating.** M2's exit is amended to three demonstrations: (1) provision → meter → terminate within limits, full history in the chronicle; (2) a call exceeding the per-call max is **refused before execution**, the refusal recorded as a chronicle Event; (3) revoke cascade fires — session dies, subsequent calls refused at the boundary, the in-flight call completes. Without all three, M2 is not done.

**A3 — M2 ships 7 base tools live, 2 dark.** `create_escrow` and `release_milestone` ship **dark** in M2 (they require M3's settlement substrate) and activate in M3. The other seven base tools are live in M2. The M2 listing carries the line "settlement tools: available M3" — the X5 honesty discipline applies to the catalog itself.

**A4 — Rail verification joins M0-B.** Minimum: (a) Solana RPC access confirmed at the volume M3 requires; (b) a USDC-SPL transfer executes and confirms; (c) the x402 metering path exercised end-to-end on a test transaction; (d) the cascade (Solana → Base → Robinhood USDG → CASH) documented and one leg exercised (Solana → Base recommended). **SoSem's qualification:** verification runs on test rails wherever a test rail exists; any step that would move live value is a spend and keeps James's money gate — it is not authorized by this amendment or by the merge tap. If verification surfaces a rail blocker, a temporary amendment to the rail law is a **ruling for James**, named in advance here.

**A5 — M4 listings claim only what is green at M4.** Listings state: Claude reference implementation (green at M2's exit); "MCP protocol standard compliant" as a protocol statement; "Additional AI compatibility: verified in progress" for everything else. M5 promotes each client to a green listing claim as its matrix cell passes. No listing ever claims unverified compatibility.

**A6 — The Markets adversarial pass is inside M3's exit gate (audit option 1).** Before the six Markets vertical tools publicly activate, M3's exit requires the trading-surface adversarial pass: tenant isolation, limit enforcement, and revoke cascade, specifically against those six tools. M4's hardening then adds the platform-wide pass and directory-driven load testing on top of proven basics.

**Cleanups adopted.** **C2:** engagements opened in M1 continue on invoice through M3; M3's escrow machinery migrates them or leaves them on invoice per the engagement policy set at signing — the policy decision is named here so it is taken at signing, not discovered in M3. **C3:** the two Resend placement routes, stated: *(Route 1)* James completes the GitHub sign-in in the live browser session that holds both values; the session places them as Actions secrets on DEVBUILDSTACK/UZE; the deploy workflow syncs them into Vercel Production; SoSem dispatches and verifies. *(Route 2)* James, from his own signed-in sessions, creates a fresh Resend API key, copies the webhook signing secret from the Resend webhook page, and adds both as Actions secrets (`RESEND_API_KEY`, `RESEND_WEBHOOK_SECRET`) on DEVBUILDSTACK/UZE; SoSem dispatches and verifies. **C4:** duration estimates are DeepSeek's read, recorded as estimates, not commitments: M0-A ~30 min once values are in hand; M0-B 2–3 days once credits resolve; M1 2–3 weeks; M2 1–2 weeks; M3 3–4 weeks; M4 2 weeks; M5 1 week — roughly **10–12 weeks** after M0, with M1 and M2 in parallel. **C5:** **M1 and M2 run in parallel**; M3 is the join point (James's gates sequence their starts). **C6:** agency resale of UZE Compute is **out of scope** for the M0–M5 build sequence — a commercial relationship, not a build item; it is named here so it is not read as dropped. **C7:** M0-A's first act is to confirm Scope 1's state claims against the running system (live gate behavior, seed counts, rehearsal evidence) before the OTP test is treated as meaningful. *(Spot-check run at ingestion, 2026-11-18 ~20:15 ET: GET dev.uzemarkets.com/ = 200; GET /api/catalog = 401 — the deployed gate behaves as filed.)*

**P2 seam amendments adopted.** **S1:** until the separated P2 track lands, **M1's placement is desk-mediated** — the desk (SoSem) makes the staffing call, backed by the built Scope 1 data (repo grant activity, mock view/comment history, professional profile data) as supporting evidence, **not** as a gating signal. When P2 lands, the assessment record assists the desk's call. **S2:** the Talent tools' activation trigger is a demonstrable event: **the first assessment outcome published under P2's two gates** in its own track. "When P2 lands" means that event, everywhere this merge uses the phrase.

**What the tap authorizes, with these amendments (per the audit's recommendation):** M0-A on James's placement act; M0-B on credits; M1 and M2 in parallel; M3 with the adversarial pass in its exit; M4 with honest listings; M5 unchanged. What does **not** happen on the tap: the Phase 6 open-repo gate, any send, any rail enable, any real grant, any spend.
