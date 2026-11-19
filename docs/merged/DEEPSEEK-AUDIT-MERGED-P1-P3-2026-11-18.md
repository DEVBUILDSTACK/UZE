# DeepSeek Audit — Merged P1 + P3 v0.1

**Filed as received.** Author: DeepSeek (off the standing arrangement), relayed by James 2026-11-18. Audit of `docs/merged/P1-P3-MERGED-SCOPE-AND-PHASED-SPRINT-v0.1.md`. SoSem's verification and the adopted amendments are recorded in the amendment section appended to the merged document.

---

Audit — Merged P1 + P3 v0.1

Verdict. The merge is structurally correct. One platform, two surfaces — Scope 1 as system of record, Scope 3 as access layer — with one chronicle, one gating pattern, one rail law, one storage doctrine. That is the right architecture and the merge gets it right. The P2 seam is drawn correctly: three interface points, three Talent tools ship dark, shared publisher, no blocking.

Six material amendments before tap. Each is an execution-level gap the merge has but doesn't name. None is structural; all bite if the tap runs as written. Below, numbered, ordered by impact on the critical path. Then minor cleanups, the P2 seam read, and my recommendation.

---

Material amendments

A1 — Split M0 into M0-A and M0-B

As written, M0 bundles Scope 1's close-out (Resend, master token, owner OTP) with Scope 3's P0 (provisioning verification, IPFS, MCP spike, credits). The first is unblocked and short; the second is contingent on NEAR AI Cloud credits with no timeline. M0 as written cannot complete until the credits resolve, which delays the entire merged sprint behind a dependency that isn't on a clock.

Split:

Phase Contents Owner Unblocked?
M0-A Resend key + webhook secret placed → deploy dispatched → mailer armed → owner OTP test → LIBRARY_MASTER_TOKEN placed → admin API opened James Yes — 30 min of work once values are in hand
M0-B NEAR AI Cloud provisioning verified end-to-end; actual spin-up time measured; four-point IPFS verification; MCP protocol conformance spike vs. Claude reference; credits path stated SoSem + James No — blocked on credits

M0-A can close tonight in parallel with the AEInfo focus without displacing it. M0-B sequences when credits resolve. The merged sprint then begins with M0-A complete and M0-B queued behind credits — the critical path stays open.

A2 — M2's exit gate proves no gating

M2's exit as written: "an external agent provisions, meters, and terminates a UZE Instance against the real endpoint, inside user-set limits, with the full call history in the chronicle."

The gating is the trust boundary. If M2's exit doesn't test that a call exceeding pre-authorization limits is refused before execution, the gating isn't proven. M3 then adds money-moving Markets tools on top of unproven gating. That is the order wrong.

Amended M2 exit gate — three demonstrations, not one:

1. Provision → meter → terminate within limits (as written).
2. Call exceeding per-call max refused before execution; refusal recorded as a chronicle Event.
3. Revoke cascade fires: session dies, subsequent calls refused at boundary, in-flight call completes.

Without all three, M2 is not done.

A3 — M2 needs "ship dark" explicit for the base toolset

The merge names 9 base tools but M2's exit only demonstrates 4 of them (provision, meter, terminate, status). The other 5:

· get_credentials, list_tiers — trivial; live in M2.
· query_balance, pay_via_x402 — read-only and metering; live in M2.
· create_escrow, release_milestone — require the settlement substrate, which the merge puts in M3.

So M2 ships 7 tools live, 2 dark (create_escrow, release_milestone). The merge doesn't say this. An external agent browsing the M2 listing sees 9 tools and expects 9 to work.

Amendment to M2: state which base tools ship dark in M2 vs. M3. My read: create_escrow and release_milestone dark until M3; the other 7 live. The M2 listing carries a "settlement tools: available M3" line so the honesty discipline (X5) applies to the catalog, not only to claims about timing.

A4 — Rail verification missing from M0-B

M0-B verifies IPFS, MCP protocol conformance, and provisioning. It does not verify the rail law of record — USDC Solana as default, cascade path. First rail exercise is M3's escrow. If USDC Solana has an issue (RPC access, settlement timing, token program edge cases), the first discovery happens when money tries to move.

Amendment to M0-B: add rail verification. Minimum: (a) Solana RPC access confirmed at the volume M3 will require; (b) USDC-SPL transfer executes and confirms; (c) x402 metering path exercised end-to-end on a test transaction; (d) the cascade path (Solana → Base → Robinhood USDG → CASH) documented and one leg of the cascade exercised (recommended: USDC Solana → USDC Base, as the simplest bridge).

Without this, M3's settlement phase discovers rail issues in production. With it, they're caught in M0-B while nothing is at stake.

A5 — Listings versus compatibility matrix sequencing violates the honesty discipline

M4 ships directory listings. M5 ships the compatibility matrix. A listing that says "works with any MCP-compatible agent" is a claim. Per the X5 discipline (no unmeasured claims), the claim needs evidence — but the evidence lands a phase later.

Amendment to M4: the listings carry only claims that are green at M4:

· Claude reference implementation — green (M2's exit proved it end-to-end).
· MCP protocol standard compliant — statement of protocol, not a compatibility claim.
· "Additional AI compatibility: verified in progress" — honest indicator for the states between M4 and M5.

Then M5 promotes each additional AI to a green listing as its cell passes. Listings are honest from day one and stay honest through the matrix expansion.

A6 — Markets tier ships to production without an adversarial pass

M3 ships the Markets vertical tools (money-moving) with no adversarial pass. M4 does hardening — one phase later, on a surface that has been publicly reachable for the length of M3+M4. This is the wrong order.

Two options, either acceptable; merge should pick one:

1. Move the trading-surface adversarial pass into M3's exit gate (my recommendation): tenant isolation, limit-enforcement, revoke-cascade specifically for the six Markets tools, before they publicly activate. M4's hardening then adds the platform-wide pass and the directory-driven load testing on top of already-proven basics.
2. M3 ships Markets tools dark (like the Talent tools), with activation gated on M4's hardening pass. Honest about the sequencing but adds a phase to first trading revenue.

My read: option 1. The Markets tools are the reason the premium tier exists. Gating their production launch on the adversarial pass, inside M3, is the discipline the rest of the platform already holds.

---

Minor cleanups

C1 — P2 / "Phase 2" renumbering. The merge correctly relabels M0–M5 to avoid collision. But "Phase 2" now means Scope 2 / Assessment in this merge's mapping, whereas in the original directive v3.1 it meant the assessment layer built after Phase 1. Any document still saying "Phase 2" needs a mapping check. Worth a standing note in the merge's front matter: "Phase N references from documents prior to 2026-11-18 mean the directive v3.1 phase, not this merge's phase."

C2 — M1 engagements surviving into M3. M1's exit says placement runs on "the platform's existing signals" and settlement lands in M3. If M1 opens engagements on invoice/manual settlement and M3 introduces escrow, what happens to M1's engagements? Migrated? Stayed on invoice? The merge doesn't say. Amendment: M1's exit adds "engagements opened in M1 continue on invoice through M3; M3's escrow machinery migrates them or leaves them on invoice per engagement policy set at signing." Migration policy is a decision — but the merge should name that the decision exists, not discover it in M3.

C3 — Resend placement routes. §7 references "two routes open, both James's (live-browser sign-in, or placement from his own sessions)." The merge doesn't state what the routes are. If M0-A runs tonight, James needs them stated — one line each, or a link to the memo where they were.

C4 — Total duration estimate. The merge has no duration estimate. My rough read after A1's split:

Phase Duration (after unblocking)
M0-A 30 min, tonight if values are in hand
M0-B 2–3 days, once credits resolve
M1 2–3 weeks
M2 1–2 weeks (parallel to M1 possible; see below)
M3 3–4 weeks
M4 2 weeks
M5 1 week

~10–12 weeks after M0 completes, with M1 and M2 running in parallel for most of their duration. Worth stating in the merge so James sees the critical path. Without it, "the merged program sequences behind AEInfo" has no end date.

C5 — M1 and M2 could run in parallel. The merge orders M1 before M2. My read: they don't depend on each other. M1 is dual-track placement (Scope 1 Phase 3). M2 is core MCP + Instance tier (Scope 3 Phase 1). Neither consumes the other's output. Serializing them costs 1–2 weeks that parallelization reclaims. Amendment: M1 and M2 can run in parallel; M3 (which needs both) is the join point.

C6 — Agency resale. The productization mentioned agency resale of UZE Compute (the reseller pattern, one layer up). The merge doesn't mention it. Disposition needed: in scope, deferred to a post-M5 phase, or out of scope entirely. My read: out of scope for now — it's a commercial relationship, not a build item, and it doesn't affect the M0–M5 sequence. But the merge should say so explicitly rather than leave the reader wondering if it was dropped.

C7 — Verification dependency on Scope 1's state claims. The merge states Scope 1 is "BUILT, DEPLOYED, DB-BACKED... 5 professionals + owner test persona, 59 repo grants; rehearsal 40 passed / 0 failed." I can't verify these from this message. If they're accurate, M0-A is 30 minutes. If any is overstated, M0-A needs its own audit before the OTP test is meaningful. Worth naming as a dependency: M0-A's first act is to confirm the state claims against the running system, not to trust the summary.

---

The P2 seam — my read

The seam is drawn correctly. Three interface points, no shared build, tools ship dark. Two amendments:

S1 — "Placement runs on existing signals" needs a name. M1's exit says placement runs on "the platform's existing signals" pending P2. What are those signals? From Scope 1 Phase 1's built state: repo grant activity, mock view/comment history, professional profile data. Are these sufficient to staff a Track B engagement blind, or does M1 demonstrate placement without any assessment signal (i.e., placement is a desk-mediated process that doesn't require signals at all)? The distinction matters — if M1's placement is desk-mediated (SoSem makes the call), that's demonstrable and honest. If it requires signals and the signals don't exist, M1's exit gate has a hidden dependency on P2.

Recommendation: state that M1's placement is desk-mediated until P2 lands — the desk (SoSem) makes the staffing call, backed by the built Scope 1 data as supporting evidence, not as gating signal. Then when P2 lands, the desk's call is assisted by the assessment record. That's how a real recruiting desk works today, and it's honest about what's under construction.

S2 — Talent tool activation gate needs a stated trigger. M3's Talent tools ship dark, activate when P2 lands. What's the specific trigger? P2's tap? P2's Phase 3 entry? P2's publisher proving out? The merge says "activate when that track lands" — but "lands" is vague for a phase-gated system. Recommendation: the trigger is P2's two-gate flow proving end-to-end in its own track — i.e., the first assessment outcome published under P2's gates. That's a demonstrable event, not a calendar date.

---

Rulings — no changes to my prior read

The seven rulings carry from the prior response. My recommendations stand: naming as proposed; two-tier directory priority; publish_redacted Markets-tier only; per-call + % of notional; publish-now markup framework; approver at Phase 3 entry; UZE-IPFS as target / Filebase-Pinata as operating.

One addition per the diagnosis of A4 above: the rail verification in M0-B is a James-decision-adjacent item — if the USDC Solana rail has a verified issue during M0-B, the rail law of record may need a temporary amendment. Worth naming as a possible ruling if A4 turns up a blocker.

---

Recommendation on tap

Tap the merge, subject to amendments A1–A6. None of the six is structural — each is an execution discipline the merge has but doesn't name. With them named, the tap authorizes:

1. M0-A tonight if James has the Resend values and the token in hand (30 minutes, doesn't displace AEInfo focus).
2. M0-B on credits resolution.
3. M1 and M2 in parallel (per C5).
4. M3 with the adversarial pass folded into its exit gate (per A6).
5. M4's listings honest about compatibility from day one (per A5).
6. M5 unchanged — the gate is James's alone.

What does not happen on the tap: Phase 6 open-repo gate, any send, any rail enable, any real grant, any spend. Those keep their own gates, unchanged.

If James prefers the merge as filed — without amendments — the sequencing works but the critical path is longer (M0 can't complete until credits), the gating isn't proven before money moves (M2 → M3), and the listings claim compatibility before the matrix exists (M4 → M5). None of those is fatal. All of them are the difference between a merge that ships on the discipline the platform has been holding and a merge that ships on schedule by relaxing it.

My read: hold the discipline, adopt the six amendments, tap.

— DeepSeek, off the standing arrangement.
