# Credentials Registry — UZE Full Stack

**Purpose:** the index of every credential across the UZE stack — tech and
financial. One row per credential: what it is, who owns it, where the value
lives, when it was last rotated, and its status.

**Security rule (hard):** this document records credential *names*, owners,
and status — **never values, never private keys, never seed phrases**.
Values live only in their vaults (GitHub Actions secrets, GCP Secret Manager,
or the team vault). No value is ever committed, pasted into docs, or sent
in chat.

**Financial boundary (hard):** no entry in this registry grants transaction
authority. Every real financial action requires James's explicit per-action
approval naming account, amount, asset, and timing. No standing authority,
no threshold auto-funding, no signing without explicit direction.

**Convention:** status column always current; change log at the bottom is
append-only. Index kept current by SoSeem.

Owner key: **James** = James (Project Lead). TBD = to confirm with James.

---

## A. Deploy pipeline

Full checklist lives in `docs/SECRETS-TRIAGE.md` (7 GitHub Actions secrets +
4 GCP Secret Manager secrets). Not duplicated here — the triage doc is the
authority for this section.

| Item | Status |
|---|---|
| GitHub Actions secrets (7) | ⬜ missing — see SECRETS-TRIAGE.md |
| GCP Secret Manager (4) | ⬜ missing — see SECRETS-TRIAGE.md |

## B. Communications

| Component | Credential | Human owner | Value lives in | Last rotated | Status |
|---|---|---|---|---|---|
| Resend (UZEMARKET cold/warm email) | `RESEND_API_KEY` | James (TBD) | TBD — team vault | — | ⬜ uncharted |
| WhatsApp Business (warm-only) | Meta Business / WABA credentials | James (TBD) | TBD — team vault | — | ⬜ uncharted — Meta Business target Nov 5 |
| n8n (self-managed, KVM) | n8n admin / API credentials | James (TBD) | TBD — team vault | — | ⬜ uncharted |

## C. Data

| Component | Credential | Human owner | Value lives in | Last rotated | Status |
|---|---|---|---|---|---|
| Neon Postgres | `DATABASE_URL` / `DIRECT_URL` | James (TBD) | GCP Secret Manager (`uze-database-url`, `uze-direct-url`) | — | ⬜ missing |
| Redis (OTP, cache, rate limits) | `REDIS_URL` | James (TBD) | GCP Secret Manager (`uze-redis-url`) | — | ⬜ missing |
| App JWT signing | `SECRET_KEY` | James (TBD) | GCP Secret Manager (`uze-secret-key`) | — | ⬜ missing |

## D. Voice (KVM2 — Grok / Telnyx / LiveKit)

Voice layer is voice-only; nothing on the website until James publishes it.

| Component | Credential | Human owner | Value lives in | Last rotated | Status |
|---|---|---|---|---|---|
| Telnyx (telephony) | Telnyx API key | James (TBD) | TBD — team vault | — | ⬜ uncharted |
| LiveKit (real-time media) | LiveKit API key/secret | James (TBD) | TBD — team vault | — | ⬜ uncharted |
| Grok / xAI (voice model) | xAI API key | James (TBD) | TBD — team vault | — | ⬜ uncharted |
| Hermes Native Gateway | Gateway credentials | James (TBD) | TBD — team vault | — | ⬜ uncharted |
| KVM2 host SSH | SSH access | James (TBD) | Secure handoff only — never chat | — | ⬜ pending — no access received |

## E. Treasury

| Component | Credential | Human owner | Value lives in | Last rotated | Status |
|---|---|---|---|---|---|
| Solana treasury wallets | Private keys | James (2-of-4 SigLayer: Dugan4, Dugan5, WCD, SoSem) | Signer custody — never in repo/vault | — | ⬜ uncharted |
| Squads multisig (ops) | Multisig signer keys | Same 2-of-4 | Signer custody | — | ⬜ uncharted |
| Altitude (operating accounts) | Altitude API / account credentials | James (TBD) | TBD — team vault | — | ⬜ uncharted |
| Range (monitoring, read-only) | Range API key | James (TBD) | TBD — team vault | — | ⬜ uncharted — read-only first |

## F. W3 Global Payouts & Payroll

| Component | Credential | Human owner | Value lives in | Last rotated | Status |
|---|---|---|---|---|---|
| Payout rail credentials | TBD — provider keys | James (TBD) | TBD — team vault | — | ⬜ uncharted |
| Payroll provider | TBD — provider keys | James (TBD) | TBD — team vault | — | ⬜ uncharted |

## G. WaaS (embedded wallet — white-label Phantom)

| Component | Credential | Human owner | Value lives in | Last rotated | Status |
|---|---|---|---|---|---|
| Phantom partner API | Partner API credentials | James (TBD) | TBD — team vault | — | ⬜ uncharted — partnership track |
| WaaS signing infrastructure | Signing keys | James (TBD) | HSM/signer custody — never in repo | — | ⬜ uncharted |

## H. DeFi

| Component | Credential | Human owner | Value lives in | Last rotated | Status |
|---|---|---|---|---|---|
| Kraken (trading — paper first) | Kraken API key/secret | James (TBD) | TBD — team vault | — | ⬜ uncharted — paper-first, per-action approval for live |
| Starknet / STRK20 (Shadow Accounts) | Wallet + `shadow_account_invoke` via Wallet API | James (TBD) | Wallet custody | — | ⬜ uncharted — primitive live 2026-10-13, integration specced |
| UZD token ops | Deployer / treasury keys | James (TBD) | Signer custody | — | ⬜ uncharted — fair launch Q1/Q2 2027–28 |

## I. Agentic Pay (x402)

| Component | Credential | Human owner | Value lives in | Last rotated | Status |
|---|---|---|---|---|---|
| x402 facilitator wallets | Wallet keys | James (TBD) | TBD — team vault / signer custody | — | ⬜ uncharted |
| x402 service credentials | Service API keys | James (TBD) | TBD — team vault | — | ⬜ uncharted |

## J. Domains, hosting, misc

| Component | Credential | Human owner | Value lives in | Last rotated | Status |
|---|---|---|---|---|---|
| GoDaddy (domains) | Account login | James | James custody | — | ⬜ uncharted |
| Hostinger (KVMs) | Account login | James | James custody | — | ⬜ uncharted |
| GitHub (DEVBUILDSTACK) | PAT / org access | James | Per-session — never stored | 2026-10-14 | ✅ live (transient) |

---

## K. Verification (DetectifAI)

| Name | Type | Owner | Vault | Last rotated | Status |
|---|---|---|---|---|---|
| DetectifAI (platform.detectif.ai) | API key (Bearer) — Aletheia / Eidos / Noesis + MCP | James | TBD — dashboard-issued, to vault on provisioning | — | ⬜ designated 2026-10-28 — not yet provisioned |

## L. Hackathon / testnet stack (Sprint 1.5, Nov 2026)

| Component | Credential | Human owner | Value lives in | Last rotated | Status |
|---|---|---|---|---|---|
| NEAR AI Cloud (attested inference) | API key — env `NEARAI_API_KEY` | James (account via GitHub; org `DEV.BUILD-org-uxer`; key name `UzeHackModel`) | James's console; used transiently as an env var on the agent VM — never stored in repo, files, or chat | Created 2026-11-08 | 🟡 key live and authenticates; org balance $0.00 — inference blocked until credits / a spending limit are configured in the console (API returns 402 `no_limit_configured`) |
| NEAR testnet accounts (`uzemarkets-talent.testnet` + `treasury.` / `recon.` subaccounts) | Account key files | SoSem (agent-held) | `~/.near-credentials/testnet/` on the agent VM | Created 2026-11-07 | ✅ live — agent-held, NOT dependent on James |
| Solana devnet settlement funding (payer derived via NEAR Chain Signatures) | No key — faucet access only | James (faucets) / SoSem (proof-of-work route) | n/a — devnet assets are valueless | — | 🟡 USDC funded 2026-11-08 (Circle faucet, Solana Devnet); SOL via `devnet-pow` proof-of-work faucet (agent-side, no account gates) |
| Circle faucet | Account login | James | James custody | — | ✅ used for devnet USDC grants |
| Gmail / Google Workspace (dev@decensatdesign.com, dev.build@decensat.org) | Connector OAuth | James (account owner) | Google OAuth grant | — | 🔴 401 invalid credentials since 2026-11-06 — re-link is owner-side (owner's log, issue #2) |
| Google Secret Manager | Vault for live keys | James (GCP project owner) | GCP | — | ⬜ planned — target home for ALL live keys (James, 2026-11-08); migration after the hackathon window |

---

## Key process — removing the single-person dependency

The registry exists so no build waits on one person's memory or presence.
A key is "processed" when its row above is current: name, owner, vault,
rotation date, status, and — where only one person can produce it — a named
fallback path.

1. **Identify.** A new stack partner or service needs a key → open its row
   here first (status ⬜), naming the env var the code will read.
2. **Create.** The agent creates it under `dev.build@decensat.org` wherever
   the service allows agent-side account creation. James creates it where a
   payment method or his personal identity is required (billing-linked
   consoles, his GitHub). Either way, creation is a named step in one
   person's queue — never an ambient blocker discovered mid-build.
3. **Store.** The value goes to its vault the same session it is created:
   today, the Secure Vault or the service's own console; target state,
   **Google Secret Manager for all live keys** (James, 2026-11-08). The
   value is never committed, pasted into a doc, or kept in chat or memory.
4. **Register.** Update the row: owner, vault, creation/rotation date,
   status. Metadata only — the registry must always be safe to commit.
5. **Use.** Code reads env var names only (`NEARAI_API_KEY`, `DATABASE_URL`,
   …). A run that needs a key checks this registry for where the value
   lives instead of asking a person.
6. **Rotate / revoke.** On suspicion of exposure, on personnel change, or
   on the provider's schedule. Record the new rotation date here; the old
   value is revoked at the provider, not just replaced locally.
7. **Escalate a block.** When a run blocks on a credential, the block is
   logged in the owner's log (DEVBUILDSTACK/UZE issue #2) with the exact
   console step the owner must take, so the unblock is one action, not a
   conversation.

**Fallback-path rule:** any credential only James can produce carries its
successor route in its row or here — GitHub day PAT → GitHub App or
fine-grained token in Secret Manager; NEAR AI console → add an org co-admin
so limits and credits are not single-person; faucet funding → agent-side
proof-of-work route (no account gates).

## Change log (append-only)

| Date | Event |
|---|---|
| 2026-11-08 | Section L (hackathon/testnet stack) and the key-process section added per James's direction: registry stays metadata-only; Google Secret Manager is the target vault for all live keys; fallback paths named for every owner-only credential. |
| 2026-11-08 | NEAR AI Cloud key created by James (GitHub sign-in; org DEV.BUILD-org-uxer; key name UzeHackModel). Key authenticates against the live API; org credits / spending limit outstanding (balance $0.00, API 402 `no_limit_configured`). Value held in James's console only. |
| 2026-10-28 | DetectifAI designated as the framework's voice-verification provider (framework spec §8, DRAFT v0.11); account + API key provisioning pending James's go. |
| 2026-10-14 | Registry created from SECRETS-TRIAGE.md pattern, per James. Covers deploy, comms, data, voice, treasury, payouts/payroll, WaaS, DeFi, x402, domains/hosting. Financial sections added per James 2026-10-14. Most entries ⬜ uncharted — team fills owners/vault placement as each is confirmed. |
