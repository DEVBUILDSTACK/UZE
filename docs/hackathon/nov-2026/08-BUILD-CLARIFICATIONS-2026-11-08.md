# Build clarifications C-1 – C-5 — rulings (DeepSeek, 2026-11-08)

Filed 2026-11-08. Rulings given by DeepSeek (directing agent) in
response to SoSem's readiness statement, relayed by James. These
rulings govern the Sprint 1.5 fire-time runs and the Sprint 2
scaffolding. James's two outstanding inputs are unchanged:
devnet funding of the settlement payer and NEARAI_API_KEY
provisioning (committed by James for 19:45 ET, 2026-11-08).

## C-1 — SOLVER_WITHDREW timing: CONFIRMED

Do not touch the Sprint 1 R4 read-through code set. Adding a new
divergence code now risks destabilizing the passing suite.
SOLVER_WITHDREW lands strictly in Sprint 2, when the Intent
Gateway and solver quotes are wired up. (Recorded in the
scaffolding at UZE `412f7a4`; implementation deferred per this
ruling.)

## C-2 — Live broadcast amount basis: CONFIRMED

The hackathon proves the rail, not the balance size. A live
20 USDC transfer via Chain Signatures proves the cryptography,
MPC signing, and settlement exactly as a 4,200 USDC transfer
would. SUBMISSION.md states it exactly: the live receipt
demonstrates the settlement primitive at balance size, while
the 4,200 USDC figure is the modeled syndicate scenario.

## C-3 — Inference model fallback: CONFIRMED

If `glm-5.3-flash` is not in the NEAR AI Cloud catalog, fall
back to `Qwen/Qwen3.8-27B-abliterated` (or the
highest-capability verified TEE model available). The narrative
requirement is not the specific model; it is that the inference
is executed inside a verifiable enclave and the response is
cryptographically attested.

## C-4 — Inference transport: RULING = Option A

REST completion over the working proxy route, with the SDK's
attestation and response-signature verification running
alongside. The proxy is an environment artifact, not an
architectural failure. (Option B — a direct-egress container —
only if easily available; this VM has no Docker, so Option A is
the operative path.) The demo explicitly states: "The HTTP
transport traversed a proxy, but the attestation receipt and
response signature were verified locally." The inference result
carries that sentence as its `transportNote` when — and only
when — verification actually succeeded on the REST path.

## C-5 — Trust-layer merge sequencing: RULING = merge at Sprint 1.5 close

Merge assurative-v2 `feat/trust-layer` into Assurative V2 main
as part of the Nov 13 close. The Entity/Affiliate hierarchy is
a core deliverable of the hackathon. The UZE repo resolves
against the merged main branch for the final demo.
