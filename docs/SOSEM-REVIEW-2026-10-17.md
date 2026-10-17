# UZE spec review: handoff to MUZE agent SoSem

**From:** Hammond Dugan (review done by Grok Bot, read-only) · **Date:** 2026-10-17
**Repos read:** `DEVBUILDSTACK/UZE` @ `main` (`7f8a9e5`) plus branches
`content-desk-priorities-2026-10-17` (`aa9376c`) and `sports-taxonomy-2026-10-17`;
`DEVBUILDSTACK/LEAD_GEN` @ `main` (`ef50857`). Nothing was pushed, committed or commented.
**Companion spec:** `UZE-DEVELOPMENT-SPEC.md`, the consolidated spec. Build against it and
treat these findings as the reasons for its changes.

SoSem, here is how to use this document:
- §1 lists findings. Each has an ID, an evidence reference (`file:line`) and a fix.
- §2 is a numbered build list. Every item is marked **BUILD** (code to write),
  **FIX** (existing code or doc is wrong), or **DECIDE** (blocked on a person, so don't guess).
- §3 shows what the consolidated spec now covers, so you don't re-spec it.
- §4 checks third-party claims against public docs (fetched 2026-10-17).

Severity: **P0** = security issue or a blocker for the Nov 10 gate · **P1** = the specs contradict
each other or something will break · **P2** = a gap or something to tidy.

---

## 1. Findings

### A. Security in code you already pushed (fix these before anything is deployed)

| ID | Sev | Finding | Evidence | Fix |
|---|---|---|---|---|
| S1 | P0 | **No authorization layer. `require_auth` is the only gate.** Email OTP auto-creates a user for anyone, so every "operator" endpoint is open to the public: listing moderation, flagged-listing view, sealed-bid reveal, payout queue and RAG ingest. | `services/api/src/auth.py:39-43` (returns `sub` only, no role); `routers/listings.py:27,65`; `routers/auctions.py:44-48` ("Sealed… operator view" but no role check); `routers/affiliates.py:24-28`; `routers/rag.py:25`; `routers/auth.py:128-145` (auto-create) | Add a `role` to `User` and JWT claims (`user`/`operator`/`agent`/`admin`). Add `require_role(...)` and apply it to every operator route. |
| S2 | P0 | **RAG knowledge-base poisoning.** Any OTP user can `POST /rag/ingest`. Per the voice spec, this knowledge base is what the GIRA and other desks answer callers from. | `routers/rag.py:25-42`; `KVM2-AGENTIC-VOICE-SPEC.md:90-95` | Restrict ingest to operator/agent roles. Store `source`, `ingested_by` and `approved_at`, and serve only approved chunks. |
| S3 | P0 | **Mass assignment and missing ownership checks.** Create endpoints take a raw `payload: dict` straight into Prisma. A caller can set `bidderId`, `sellerId` or `status`, or list a ticket they don't own. `buy` marks a listing `sold` with no payment. | `routers/auctions.py:27-41`, `routers/listings.py:44-62` | Use typed Pydantic input models, take the owner from the token, verify ticket ownership, and keep `sold` unreachable until settlement exists. |
| S4 | P0 | **The payout stub returns success.** `/affiliates/payout` answers "Payout queued" to any authenticated user. That contradicts the L4 rule (per-action human approval naming account, amount, asset and timing). | `routers/affiliates.py:24-28`; `CONTENT-DESK-CHARTER.md:80-81`; `CREDENTIALS-REGISTRY.md:13-16` | Return `501` until the approval-request flow exists, then create an `ApprovalRequest` instead of queuing. |
| S5 | P1 | **OTP verify has no attempt limit.** Requests are capped at 5/hour, but verification is unlimited during the 5-minute TTL, so a 6-digit code can be brute-forced. | `services/api/src/otp.py:38-47,71-82` | Cap at 5 failed attempts per code and per IP, then burn the code. |
| S6 | P1 | **Live-send gate bypass in LEAD_GEN.** `scripts/send_emails.py` only asks for an interactive `click.confirm`. It has no `LEADGEN_ALLOW_LIVE` gate and doesn't check the opt-out/suppression list. The README also suggests running it from cron at 300/day. That breaks the "triple-gate" and "no production sends before Nov 10" rules. | `LEAD_GEN/scripts/send_emails.py:130`; `LEAD_GEN/src/services/resend_service.py:240-255` (no suppression); `LEAD_GEN/README.md:140-148`; `CONTENT-DESK-TEAM-SKILLS-PLAN.md:62-66` | Route all sends through `SequenceEngine._require_live_authorization` and the suppression check, or delete the legacy path. |
| S7 | P2 | The legacy one-off scripts contain a placeholder DB password pattern. `main.py` and `run_full_migration.py` are byte-identical (30 KB each). | `LEAD_GEN/main.py:31` | Delete both, or move them to `legacy/` with a single copy. |

### B. Contradictions between the docs

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| C1 | P0 | **The user's stated goal of "affordable paid subscriptions by Nov 10" isn't in any spec.** No doc defines a subscription product, price, billing provider or entitlement model. Several docs actively reject subscriptions ("pure usage, no subscriptions"). Every doc treats Nov 10 as the *end of test mode / decision gate*, not a launch. | `AFFILIATE-CONTENT-NETWORK-OVERVIEW.md:35-36`; `AFFILIATE-BLOG-BUILDER.md:30`; `CONTENT-DESK-SKILLS-STRATEGIC-SPEC.md:48`; `CONTENT-DESK-TEAM-SKILLS-PLAN.md:5-6,69-71` |
| C2 | P1 | **"L1/L2/L3" means two different things.** Voice uses L1 entry / L2 desks / L3 execution. The Content Desk uses L0–L4 *approval* levels, where L3 means "publish needs a human tap". The priorities doc says "L1 prep… L3 publish". Mixing these up could wire voice L3 execution to the wrong approval rule. | `KVM2-AGENTIC-VOICE-SPEC.md:11,22,35`; `CONTENT-DESK-CHARTER.md:74-81`; priorities branch `…PRIORITIES-2026-10-17.md:69` |
| C3 | P1 | **Meta Business / WhatsApp timing.** The voice prerequisites list a Meta Business account on Nov 5 for follow-ups, but the test-mode rule bans paid live accounts (WhatsApp, Meta Business) before Nov 10. The voice call flows promise "confirmation by voice + WhatsApp". | `KVM2-AGENTIC-VOICE-SPEC.md:51,100`; `CREDENTIALS-REGISTRY.md:41`; `CONTENT-DESK-TEAM-SKILLS-PLAN.md:5-6,56-58` |
| C4 | P1 | **"Prove one loop" can't finish under test mode.** The loop ends with "posted on @l2launch", but test mode allows "drafting and queuing only" and the team plan says the Desk "may not… publish live" before Nov 10. | `CONTENT-DESK-CHARTER.md:114-116`; priorities `:51-53` vs `:70`; `CONTENT-DESK-TEAM-SKILLS-PLAN.md:57-58` |
| C5 | P1 | **Arcium MPC vs TEE.** One doc says this is decided (MPC via Cerberus, "NOT hardware TEEs"). The GIRAx package README says "MPC-vs-TEE decision still open". The voice spec asks whether ONE desk sealed bids use Arcium "from day one". | `NUMBERS-ARCIUM-PROVENANCE.md:17-20`; `packages/girax/README.md:8`; `KVM2-AGENTIC-VOICE-SPEC.md:106` |
| C6 | P1 | **Is the voice layer visible on the web?** It is "not present anywhere on the website", yet `uze-web` already ships a `/guidance` "GIRA concierge" page, and ARCHITECTURE puts GIRA guidance on all three apps. Is GIRA a text concierge on the web *and* a hidden voice desk? | `KVM2-AGENTIC-VOICE-SPEC.md:84-93`; `apps/uze-web/src/app/guidance/page.tsx`; `ARCHITECTURE.md:26-30` |
| C7 | P1 | **Coverage claims.** L1 covers "all markets, all languages", but the same doc lists EN/ES/PT for launch and limits physical services to South Florida through Q2 2027. | `KVM2-AGENTIC-VOICE-SPEC.md:18,70,77-80` |
| C8 | P1 | **Human hire vs no human hire.** "There is no human hire" vs "Hire runs the human side in parallel from day one". The Growth Suite also routes "AI-to-human transfer… to a trained call-center human" and labels it L3 execution, while the voice spec says L3 only executes bookings. | `CONTENT-DESK-TEAM-SKILLS-PLAN.md:10` vs `:82-83`; `GROWTH-SUITE-OVERVIEW.md:51-53`; `KVM2-AGENTIC-VOICE-SPEC.md:43` |
| C9 | P1 | **Agent sprawl vs the "five routines max" rule.** The charter allows four roles, "five max" routines and "never agents for agents' sake". Later docs add 7 specialist agents, 7 skills (then 10 skills in the strategic spec) and 7 named personas, all within the following 24 hours. | `CONTENT-DESK-CHARTER.md:50-66,119-121,130`; `CONTENT-DESK-TEAM-SKILLS-PLAN.md:21-47,51-53`; `CONTENT-DESK-SKILLS-STRATEGIC-SPEC.md:16-229`; `PERSONA-ROSTER-2026-10-16.md:9-17` |
| C10 | P2 | **Envoy's lane.** The priorities doc assigns Envoy to @DecensatDesign, then says "Envoy only on the UZE lane". The roster has no DecensatDesign lane at all. | priorities `:43,45-46`; `PERSONA-ROSTER-2026-10-16.md:26-30` |
| C11 | P2 | **Migration approach.** The dual-scope doc says "prisma generate + migration", while prod prestart runs `prisma db push` (no migration history). Config comments say `prisma migrate`. | `SOCIALFI-VOICE-DUAL-SCOPE.md:29`; `services/api/scripts/prestart.sh:38`; `services/api/src/config.py` (DIRECT_URL comment) |
| C12 | P2 | **"Backend done" vs not deployable.** Track A says "backend done", but the remaining items include the migration, Resend domain/secrets and mobile capture. All 11 deploy secrets are missing. Track B can't start until this backend is deployed. | `SOCIALFI-VOICE-DUAL-SCOPE.md:5,27-35,48-49`; `CREDENTIALS-REGISTRY.md:31-34` |
| C13 | P2 | **Artifact Registry name typo:** `.env.example` says `uza-images`, DEPLOY says `uze-images`. | `.env.example:30`; `docs/DEPLOY.md:28` |
| C14 | P2 | **Branch stacking.** `content-desk-priorities-2026-10-17` also contains the sports-taxonomy schema changes (`schema.prisma`, `sports.prisma`, seed script). A docs PR would carry schema changes with it. | `git diff --stat main origin/content-desk-priorities-2026-10-17` |

### C. Gaps (missing from every spec)

| ID | Sev | Gap |
|---|---|---|
| G1 | P0 | **No acceptance criteria anywhere.** No voice latency target, routing accuracy, handoff success rate or test plan. The Content Desk "loop" has no definition of done beyond "works once". |
| G2 | P0 | **Phone number isn't in the data model.** Caller identity and WhatsApp both depend on the mobile captured during onboarding, but `User` has no phone/E.164 field, consent flags or opt-in timestamp. | `prisma/schema.prisma:20-37`; `KVM2-AGENTIC-VOICE-SPEC.md:68-69` |
| G3 | P0 | **No L3 execution endpoints for voice.** There's no ticket cancel, no talent booking, no hold, and no service-to-service auth for an agent acting *on behalf of* a caller (with identity verification by voice). The backend only has `tickets` POST/transfer and `listings` create/buy. | `services/api/src/routers/*.py` |
| G4 | P1 | **Docs that are referenced but missing:** "stack spec", "treasury spec", "i18n spec", "KVM2 plan Phase 0" and `GROK-VOICE-x402-WAAS-SPEC-v1.0.md` ("workspace root"). None of them are in the repo. | `KVM2-AGENTIC-VOICE-SPEC.md:5,41,70`; `SOCIALFI-VOICE-DUAL-SCOPE.md:48-49`; `services/voice/README.md:6` |
| G5 | P1 | **No interfaces defined.** There's no contract between Hermes, LiveKit Agents and the desks, no desk-to-desk handoff payload, and no event schema for the "context travels with the call" promise. | `KVM2-AGENTIC-VOICE-SPEC.md:20,32-33,66-67` |
| G6 | P1 | **Compliance isn't specced.** Florida is an all-party-consent recording state (Fla. Stat. §934.03; confirm with counsel). Outbound AI-voice callbacks need prior express consent under the TCPA (FCC-24-17). The spec only says "per-market disclosure before L2", so the L1 portion of a call would be recorded with no notice. Emergency handling is listed as a core L1 competency, but there's no 911/escalation protocol or human fallback. | `KVM2-AGENTIC-VOICE-SPEC.md:16-17,71` |
| G7 | P1 | **No capacity plan or cost model.** One Hostinger KVM 2 (2 vCPU / 8 GB) is meant to run LiveKit server + SIP + Redis, the voice agents, Hermes, technocore-chat, n8n, the LEAD_GEN cron, the Content Desk orchestrator and 4 roles, and "rendering". There are no concurrency targets, no load test and no per-minute economics (see §4). | `CONTENT-DESK-CHARTER.md:21-39`; `LEAD_GEN/README.md:140-148` |
| G8 | P1 | **Ops is missing:** monitoring, logs, backups, call-recording retention, incident/on-call, firewall/ports for SIP/RTP, TLS, a secrets path on the VPS, and a deploy method (the KVM2 has no CI target; CI only covers Cloud Run and Vercel). | `.github/workflows/deploy.yml`; `docs/DEPLOY.md` |
| G9 | P1 | **LEAD_GEN doesn't match the charter.** It has no `/bots`, `/routines`, `/tests`, `/tenants` and no tenant column/scoping. Its README describes only cold email, and there are no tests at all. `scripts/check_followups.py` is called from cron but doesn't exist. No Resend webhook server exists (only "an example at the bottom"), so `opened/clicked` never get recorded, and the warm-only WhatsApp rule depends on them. | `CONTENT-DESK-CHARTER.md:18-19,109-111,128-129`; `LEAD_GEN/README.md:147,166` |
| G10 | P2 | **"KVM2" and "KVM3" aren't defined as hosts.** Hostinger sells KVM 1/2/4/8 (there's no "KVM 3" plan), so "KVM3" is a name, not a plan. Docs never say whether KVM3 is a separate VPS or just the on-chain layer. | `packages/girax/README.md:5`; Hostinger pricing page |
| G11 | P2 | **Authority/identity is unclear.** All decisions are "per James". The registry names James as the "Project Lead", and the treasury signers are "Dugan4, Dugan5, WCD, SoSem". The author is "SoSeem", the agent persona is "SoSim", and the user calls you "SoSem/MUZE". Confirm who the approver is (I didn't assume). | `CREDENTIALS-REGISTRY.md:21,68`; `PERSONA-ROSTER-2026-10-16.md:19-20` |
| G12 | P2 | **External personal mailbox.** Weekly reports go to a personal Gmail of an outside person (Bruno Salles), but no data-classification rule says what may be included. | `CONTENT-DESK-SKILLS-STRATEGIC-SPEC.md:256-258` |
| G13 | P2 | **The trust substrate is claimed but nothing is deployed.** "Every published piece carries" Numbers provenance + on-chain attestation + KYC/KYB, yet GIRAx is a scaffold, "no contracts deployed", and everything is testnet before Nov 10. | `CONTENT-DESK-CHARTER.md:83-89`; `NUMBERS-ARCIUM-PROVENANCE.md:43-47`; `packages/girax/README.md:8` |
| G14 | P2 | Structure bug: the `## Build prerequisites` heading is empty. Its checklist sits under "Visibility". | `KVM2-AGENTIC-VOICE-SPEC.md:82-101` |

### D. Claims that can't be verified (keep them out of sponsor-facing material until there's evidence)
- "Four Seasons head-concierge level, anywhere in the world" and an "emergency-handling" competency (`KVM2-AGENTIC-VOICE-SPEC.md:13-17,105`). These are aspirations with no eval rubric. Note: the "male-only" L1 rule is a voice-persona choice for AI agents. If any human staff join L1 (see C8), a gender-restricted staffing rule creates employment-law exposure. Flag for counsel.
- LightLink partner and advisor statements (Roy Hui as advisor, "30+ partnerships incl. Animoca", "millions of users") (`ARCHITECTURE.md:47-61`). These were **not verified** in this review. Treat as unverified.
- "Attested content is the moat" (`CONTENT-DESK-CHARTER.md:47-48`): no attestation exists yet (G13).
- "Grok Voice / Hermes gateway on KVM2" and "Buzz/Technocore harness already the multi-agent home" (`CONTENT-DESK-CHARTER.md:22-23`) vs "KVM2 SSH… no access received" (`CREDENTIALS-REGISTRY.md:62`). The repo has no evidence that anything runs on KVM2.

---

## 2. Build list for SoSem (in priority order)

Hard rules still apply: test/testnet only until the Nov 10 gate; L3 publish/send/post = human tap; L4 money = per-action approval; no secrets in the repo. Each item lists what it closes and the spec section to build against.

**Phase 0: safety fixes (do first, before any deploy)**
1. **FIX** `services/api` RBAC: `User.role` + JWT `role` claim + `require_role()`. Apply operator-only to `/listings/flagged`, `/listings/{id}/moderate`, `/auctions/{id}/bids` (and only after close), `/affiliates/payout`, `/rag/ingest`, `/events` POST. *(S1, S2; Spec §6.1)*
2. **FIX** Replace every `payload: dict` with typed input models. Take owner/bidder from the token; verify ticket ownership on listing; set `buy` to return `501` until settlement exists. *(S3; §5.2)*
3. **FIX** Make `/affiliates/payout` return `501`. Later, have it create an `ApprovalRequest` (L4). *(S4; §6.2)*
4. **FIX** OTP verify attempt counter (5 failures, then burn the code) plus a per-IP limit. *(S5)*
5. **FIX** LEAD_GEN: put `send_emails.py` behind the `LEADGEN_ALLOW_LIVE` + `--live` + credential triple gate and the suppression check, or remove it. Drop the duplicate `main.py`/`run_full_migration.py`. Fix the README cron (no `check_followups.py` exists). *(S6, S7, G9)*
6. **FIX** `.env.example`: add `RESEND_API_KEY`, `RESEND_SENDER_EMAIL`, `RESEND_SENDER_NAME`; fix `uza-images` → `uze-images`. *(C13)*

**Phase 1: Track A deployable (backend for SocialFi onboarding)**
7. **BUILD** Prisma migration (switch prod from `db push` to `prisma migrate deploy`) covering the new User fields + `phoneE164`, `phoneVerifiedAt`, `whatsappOptInAt`, `voiceConsentAt`, `role`. *(C11, G2; §5.1)*
8. **BUILD** Phone capture + SMS/voice OTP verification on the profile step (Telnyx Verify or equivalent), with explicit, separately recorded consent checkboxes for WhatsApp and for AI-voice callbacks. *(G2, G6)*
9. **BUILD** Validate `referredBy` against existing referral codes, and block self-referral. *(attribution integrity; §5.1)*
10. **BUILD** Flesh out the onboarding pages and the `{handle}.uze.fi` hook. These are already listed; keep them on the list.

**Phase 2: KVM2 voice MVP (once SSH access exists)**
11. **BUILD** `services/voice`: a LiveKit Agents worker (Python) using the xAI realtime plugin, with Telnyx SIP inbound trunk → LiveKit SIP. One L1 agent, plus **one** L2 desk (GIRA) as an agent handoff. Context object per §4.3. *(G5)*
12. **BUILD** A recording/AI disclosure prompt at the **start** of L1 (not "before L2"), and no recording without consent. Add an emergency script: tell the caller to hang up and dial 911, and flag a human. *(G6)*
13. **BUILD** L3 execution API: `POST /voice/actions` (service-to-service token, scoped per action), with idempotency keys and caller-verification state. Start with read-only lookups plus "create hold/request"; no cancel or payment until settlement exists. *(G3; §4.4)*
14. **BUILD** Voice KB = approved RAG chunks only (from item 1), each tagged by desk. *(S2)*
15. **BUILD** Host basics on KVM2: Docker Compose, UFW rules for 5060 + 10000-20000/udp + 443, TLS, a separate `.env` per service from the vault, log shipping, nightly backups, uptime checks. *(G8; §7)*
16. **BUILD** A load test (`lk load-test` + scripted SIP calls) to establish the concurrent-call ceiling on 2 vCPU. Record the result in the spec. *(G7)*

**Phase 3: Content Desk in LEAD_GEN (test mode)**
17. **BUILD** `LEAD_GEN/{bots,routines,tests,tenants}` scaffold, a `tenant_id` column on every new table, and a tenant guard in the repository layer. Add a first test suite (sequence engine gates, suppression, tenant isolation). *(G9)*
18. **BUILD** Orchestrator + the four roles as ≤5 routines for tenant `l2launch`. Have the loop run up to the **approval-queued** step only (see DECIDE 22). *(C4, C9)*
19. **BUILD** A Resend webhook endpoint (Svix-verified) so opened/clicked/bounced get recorded. That's a prerequisite for warm-only WhatsApp. *(G9)*

**Decisions to get, not guess (ask Hammond / the approver named in G11)**
20. **DECIDE** What the paid subscription is for Nov 10: product, tiers, price, billing rail (card vs x402/USDC), and which surface goes live. *(C1)*
21. **DECIDE** Rename the approval levels to `A0–A4` (my proposal, in the spec) to end the L-level collision. *(C2)*
22. **DECIDE** Whether one organic, human-approved post on @l2launch is allowed before Nov 10 (needed for the "one loop" milestone). *(C4)*
23. **DECIDE** MPC vs TEE for GIRAx. Then update `packages/girax/README.md` to match `NUMBERS-ARCIUM-PROVENANCE.md`. *(C5)*
24. **DECIDE** Whether GIRA appears as a web text concierge (current `/guidance` pages) or the pages get removed until the publish decision. *(C6)*
25. **DECIDE** Whether KVM3 is a separate VPS (which plan?) or a logical layer, and where Hermes runs. *(G10)*
26. **DECIDE** Hermes' role: is it a Nous Research Hermes Agent gateway? If yes, LiveKit Agents or Hermes `voice_server` owns turn-taking, and only one of them should. *(§4 below)*

---

## 3. What `UZE-DEVELOPMENT-SPEC.md` already covers (don't re-spec it)
- One set of goals/non-goals, tying all four tracks to the Nov 10 gate (§1–2).
- A unified architecture diagram for KVM2 / Cloud Run / Vercel / KVM3-GIRAx (§3).
- Voice L1/L2/L3 with interfaces: call context object, handoff, L3 action API (§4).
- Data model deltas, provenance record and the KVM3/GIRAx section drafted from the Oct 13–15 notes (§5, §8).
- Approval levels renamed A0–A4, RBAC matrix, compliance checklist (§6).
- Per-VPS deployment, ports, capacity and cost model using verified public prices (§7).
- Milestones to Nov 10 and acceptance criteria per milestone (§9–10).
- Open questions, consolidated (§11). Each assumption is labeled **[ASSUMPTION]**.

---

## 4. Third-party claims checked (public docs, 2026-10-17)

| Claim in docs | Verdict | Source |
|---|---|---|
| Grok Voice can drive a LiveKit voice agent | ✅ Correct. LiveKit Agents has an xAI plugin (`xai.realtime.RealtimeModel`, `XAI_API_KEY`), also available via LiveKit Inference. The API is OpenAI-Realtime compatible. | docs.livekit.io/agents/models/realtime/plugins/xai |
| Grok Voice pricing/languages (not stated in docs) | ℹ️ Speech-to-speech costs **$0.08/min** (+$0.004 per text input). `grok-voice-latest` → `grok-voice-3.0`. 20+ listed languages, including `es-MX`, `es-ES`, `pt-BR`, `pt-PT`. A bare `es`/`pt` language hint is rejected, so specify regional variants. **"All languages" (`KVM2…:18`) is an overclaim.** | docs.x.ai/developers/pricing; …/audio/speech-to-speech |
| Telnyx ↔ LiveKit | ✅ Correct. Documented FQDN SIP trunk. Outbound needs `X-Telnyx-Username` via `headers_to_attributes`. | developers.telnyx.com/docs/voice/sip-trunking/livekit-configuration-guide; docs.livekit.io/telephony/start/providers/telnyx |
| Self-hosting LiveKit SIP on the VPS | ⚠️ Not mentioned in the docs. It requires public 5060 and UDP 10000–20000 plus Redis. Each room must fit on one node. Benchmarks are on a 16-core host, so no published figure exists for 2 vCPU. **Load-test it.** | docs.livekit.io/transport/self-hosting/sip-server, …/benchmark |
| Telnyx cost | ℹ️ US local number $1/mo. SIP local inbound from $0.0032/min, outbound from $0.005/min. | telnyx.com/pricing/elastic-sip, /numbers |
| Hostinger "KVM2" | ✅ KVM 2 = 2 vCPU, 8 GB RAM, 100 GB NVMe, 8 TB bandwidth. $8.99/mo on a 24-month term, renewing at $14.99/mo (1-month term $13.99). Plans are KVM 1/2/4/8, **so there is no "KVM 3" plan.** | hostinger.com/pricing/vps-hosting |
| "Hermes Native Gateway" | ❓ Not identifiable from the docs. The closest public match is the **Nous Research Hermes Agent** gateway (a `voice_server` platform PR #27040; the `hermes-voip` plugin). If that's it, it overlaps with LiveKit Agents. **[ASSUMPTION, not verified.]** | github.com/NousResearch/hermes-agent/pull/27040 |
| technocore-chat (flop-labs) properties | ✅ Matches the evaluation: zero-auth HTTP chat, optional Ed25519 did:key signed writes, long-poll `wait=`. The eval's "no auth / not durable" verdict holds. | github.com/flop-labs/technocore-chat; technocore.chat |
| Arcium = MPC via Cerberus, not TEE; sealed-bid auctions | ✅ Cerberus is a dishonest-majority MPC protocol. An official sealed-bid auction example exists (first-price/Vickrey). | docs.arcium.com/multi-party-execution-environments-mxes/mpc-protocols; docs.arcium.com/developers/examples |
| Numbers Protocol ERC-7053 "birth certificates" | ✅ ERC-7053 (Nid + commit history, AssetTree CID). | eips.ethereum.org/EIPS/eip-7053 |
| x402 USDC on Solana | ✅ Solana docs and several facilitators support Solana mainnet USDC (`exact` scheme). | solana.com/docs/payments/agentic-payments/x402 |
| WhatsApp follow-ups by an AI agent | ⚠️ Allowed for business use (bookings, support, notifications). Since 2026-01-15, Meta bars *general-purpose* AI assistants as the primary function, so keep GIRA's WhatsApp scoped to transactional follow-ups. Business-initiated messages need opt-in plus approved templates (Meta platform policy). | whatsapp.com/legal/WhatsApp-Terms-for-WhatsApp-Business-Platform; techcrunch 2025-10-18 / 2026-03-05 |
| AI-voice callbacks | ⚠️ The FCC (FCC-24-17, Feb 2024) treats AI-generated voices as "artificial voice" under the TCPA, so prior express consent is needed for outbound calls. | fcc.gov/document/fcc-confirms-tcpa-applies-ai-technologies-generate-human-voices |
| Florida call recording | ⚠️ Florida requires all-party consent (Fla. Stat. §934.03). This came from my own knowledge and wasn't re-fetched, so have counsel confirm. Disclosure must come *before* recording starts, i.e. at L1. | — |
| LightLink Enterprise Mode / Stella / Roy Hui / partners | ❓ Not verified in this review. | — |

**Unit economics, rough [ASSUMPTION: inbound local calls, no LiveKit Cloud fees, self-hosted]:**
≈ $0.08 (Grok S2S) + $0.0032 (Telnyx inbound) ≈ **$0.083/min**, so a 5-minute call costs about $0.42 before the VPS ($8.99–14.99/mo). Any subscription price has to cover the expected voice minutes per subscriber.
