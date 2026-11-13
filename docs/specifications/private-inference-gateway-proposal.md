# Private Inference Gateway — PROPOSAL

**Status: 🔴 PROPOSAL — not built, not scheduled.** Filed
2026-11-13 on the owner's tap. The product facts below were
verified live the same day against primary sources; the
UZEmarkets mapping is design work. Nothing here describes a
running integration.

## What Trace Commons / NEAR AI Gateway actually is

Verified 2026-11-13 from NEAR's own blog (near.ai,
"Introducing NEAR AI Gateway", published 2026-11-11) and
the product's data policy (gateway.near.ai/your-data/, read
verbatim):

- A **desktop app** (Near.ai.app, by the Trace Commons
  project) for macOS — also Windows and Linux — that
  connects local coding tools (Claude Code, Codex,
  OpenCode) to NEAR AI's private and incognito models, and
  lets the user inspect the trace data from their sessions
  on their own machine.
- **Data policy (verified verbatim):** the app reads only
  folders the user chooses to watch; traces are redacted on
  the local computer and the unredacted trace never leaves
  it; per-folder consent is Ask each time / Automatic /
  Never (automatic uploads older first; a trace must be
  unchanged for 24 hours); signing in authorizes no sharing;
  data uses are tiered — *debugging and evaluation* always
  on, *benchmark generation*, *ranking-model training* and
  *model training* optional; an optional **witness** service
  redacts traces inside an enclave (sent to it unredacted;
  setting one up pauses automatic sharing until re-approved).
- **Credits:** NEAR's announcement says contributed data
  can earn NEAR AI Cloud credits. Trace Commons' own latest
  release notes state contributing does **not yet** earn
  credit and pricing is unchanged. Recorded as: announced,
  not yet live. No UZEmarkets surface may present a credit
  balance, earned or estimated.
- Distribution is a notarized production bundle; the update
  feed's latest item at filing is 1.0.7 (minimum macOS
  14.0). Install governance: never bypass Gatekeeper, never
  alter or re-sign the notarized app; installation is the
  owner's own act on his own machine.

## The category correction

The Gateway is a **client-side desktop application for
coding agents**. UZEmarkets inference is server-side:
`services/compose/src/inference.py` calls NEAR AI Cloud
directly (`cloud-api.near.ai`), through the official SDK
path whose gateway and model attestation is verified before
sending, with E2EE available. There is no server-side
Gateway to route a backend through, and no provider-tier
interface in the code to extend — an earlier relayed design
named an `IInferenceProvider` interface that was never
built. The desktop app therefore enters our architecture
as a *pattern and a future client option*, not as routing
infrastructure.

## What UZEmarkets would adopt (the proposal)

1. **Tiered data-sharing consent, per affiliate.** The
   policy's four tiers are the template for a consent object
   on the affiliate onboarding record (the AffiliateProfile
   module — there is no Entity settings object): debugging &
   evaluation always on; benchmark generation, ranking-model
   training, and model training each an explicit opt-in,
   the last two contractual. Consent state would be recorded
   through the mock opt-in endpoint's successor, never
   inferred from sign-in.
2. **Local redaction before inference.** A financial
   redaction pass — tenant names, addresses, account
   numbers, employee PII, client entity names — applied
   before a T-12, rent roll, or P&L reaches the inference
   layer, with the unredacted original never leaving the
   client's environment. **Not built today:** the existing
   `sanitize.py` is juror-path invisible-Unicode hygiene
   (prompt-injection defence), not PII redaction, and this
   proposal must not be read as claiming otherwise.
3. **Witness mode for high-compliance clients.** Enclave
   redaction as the top privacy tier, mapped onto the
   attested-inference routing already on record (NEAR AI
   Cloud TEE attestation; Arcium where the recorded routing
   rule sends confidential compute). A priced tier is a
   commercial decision for the owner, not made here.
4. **Private AI Mode as an honest setting.** The /treasury
   toggle shipped with this filing reflects the routing
   that exists — attestation-verified NEAR AI — and shows
   the true account state (balance $0.00; live calls return
   HTTP 402 until credits land). When a real gateway
   integration is ever built, the toggle's meaning can be
   extended; its copy may not run ahead of the code.

## What this proposal is not

Not an integration, not a credit economy, and not a claim
of "absolute data sovereignty." The claims UZEmarkets can
make today are narrower and provable: inference code that
verifies attestation before sending, client financials
that are never committed to any repository, and an honest
402 where credits are absent.
