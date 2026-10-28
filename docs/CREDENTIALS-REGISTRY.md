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

## Change log (append-only)

| Date | Event |
|---|---|
| 2026-10-28 | DetectifAI designated as the framework's voice-verification provider (framework spec §8, DRAFT v0.11); account + API key provisioning pending James's go. |
| 2026-10-14 | Registry created from SECRETS-TRIAGE.md pattern, per James. Covers deploy, comms, data, voice, treasury, payouts/payroll, WaaS, DeFi, x402, domains/hosting. Financial sections added per James 2026-10-14. Most entries ⬜ uncharted — team fills owners/vault placement as each is confirmed. |
