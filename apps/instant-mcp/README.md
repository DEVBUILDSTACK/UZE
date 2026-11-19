# UZE Instant MCP — M2 local build (Scope 3 Phase 1: core MCP + Instance tier)

The single MCP endpoint for UZE Instant, built per the merged P1+P3
program's phase **M2** (`docs/merged/P1-P3-MERGED-SCOPE-AND-PHASED-SPRINT-v0.1.md`
§5 + amendments A2/A3) and the Scope 3 specification
(`docs/instant-mcp/SCOPE-3-UZE-INSTANT-MCP-SCOPE-AND-PHASED-SPEC-v0.1.md`).

**This is a local build + proof only.** No public endpoint, no DNS, no
deployment. The production endpoint name is `mcp.uzemarkets.com`; nothing
here binds it.

## What is live

- **MCP server** (current protocol; negotiates 2024-11-05 / 2025-03-26 /
  2025-06-18 / 2025-11-25) on **two transports**:
  - Streamable HTTP — `node server.mjs`, `POST /mcp` (port `PORT`, default 8741)
  - stdio — `node server.mjs --stdio`
- **Wallet-bound auth.** A principal is a Solana wallet (base58 ed25519
  public key). Sign-in: `uze/challenge` → sign the server message with
  the wallet key → `uze/verify`. REST mirrors at `/auth/challenge` and
  `/auth/verify`. Sessions are bearer tokens (`Authorization: Bearer …`
  on HTTP; connection-bound on stdio).
- **7 of the 9 base tools, live:** `provision_instance`,
  `get_credentials`, `terminate_instance`, `get_status`, `list_tiers`,
  `query_balance`, `pay_via_x402`.
- **Three-layer gating** (spec §4): (a) user pre-authorization — a
  principal record with per-call max, per-day max, and an optional
  allowed tool set, set through the admin path (`POST /admin/principals`,
  guarded by `INSTANT_MCP_ADMIN_TOKEN` — the user's re-authenticated
  act); (b) MCP-side enforcement **before execution** — over-limit calls
  are refused and the handler never runs; (c) the tier gate — an
  Instance-tier principal cannot call Markets-tier tools or provision a
  Markets-tier instance.
- **x402-style per-call metering.** Every executed call is metered
  (micro-USDC schedule in `lib/tools.mjs`; `pay_via_x402` meters its
  amount) against the principal's limits and recorded.
- **Chronicle.** Every call — executed, refused, or dark — plus auth,
  lifecycle, and revocation events append to an append-only JSONL store
  (`data/chronicle.jsonl`). Status and daily meter totals are derived
  from the events, never written. Read it via `GET /admin/chronicle`.
- **Revoke cascade.** `POST /admin/revoke` kills all of a principal's
  sessions at once: subsequent calls are refused at the boundary, and a
  call already admitted (in-flight) completes.

## What is dark until M3

- **`create_escrow` and `release_milestone`** (amendment A3): registered
  and discoverable in `tools/list`, labeled "[Available M3]". Every call
  is refused with an `available_m3` response and recorded as a chronicle
  Event. They activate when M3's settlement substrate lands.
- **The 9 Markets-tier vertical tools** (`open_position`,
  `close_position`, `sealed_bid_assignment`, `sign_attestation`,
  `open_dispute`, `publish_redacted`, `submit_assessment`,
  `score_assessment`, `publish_assessment_outcome`): M3 scope. Tonight
  they exist in the catalog so the tier gate refuses them correctly —
  Instance principals get a `tier_gate` refusal; Markets principals get
  the `available_m3` refusal. Settlement tools: available M3.

## Provisioning is a LOCAL MOCK

Real provisioning is NEAR AI Cloud, which is **blocked on org credits
(merged program M0-B)**. No NEAR calls are made and nothing is spent.
`lib/provisioner.mjs` is a clearly labeled local mock that behaves like
the real surface for metering purposes: provision (with a simulated
spin-up delay, `MOCK_PROVISION_MS`, default 500 ms) → active → usage
ticks accrue (250 ms ticks) → terminate with a final usage reading.
Credentials and balances are likewise mock and labeled as such;
`pay_via_x402` records into the mock ledger — **no funds move**, and the
rail named in its receipt (USDC on Solana, per the rail law) is the
intended rail, not a live one.

## Run it

```sh
INSTANT_MCP_ADMIN_TOKEN=<admin-token> node server.mjs          # HTTP on :8741
INSTANT_MCP_ADMIN_TOKEN=<admin-token> node server.mjs --stdio  # stdio transport
node test.mjs                                                  # A2 exit demonstrations
```

State lives in `data/` (override with `INSTANT_MCP_DATA_DIR`); runtime
files there are gitignored. Zero dependencies — Node ≥ 18 built-ins only
(ed25519 via `node:crypto`).

## Exit proof

`test.mjs` drives the server over HTTP and stdio and asserts the three
amendment-A2 demonstrations — (i) within-limits provision → meter →
terminate with the full chronicle present; (ii) an over-limit call
refused before execution with the refusal chronicled; (iii) the revoke
cascade (sessions die, subsequent calls refused, the in-flight call
completes) — plus auth, tier-gate, dark-tool, daily-limit, and
cross-principal isolation coverage.
