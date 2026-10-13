# UZE Monorepo

Source of truth for the UZE ecosystem. Target org: **DEVBUILDSTACK**.

## Layout
- `apps/uze-web` — UZE consumer front-end (tickets, stays, dining, experiences)
- `apps/uzed-web` — UZED.si embedded secondary market (resale by UZE)
- `apps/siglayer` — SigLayer treasury + trade layer (vaults, DATs, yield tiers)
- `apps/command-center` — Command & Control Center admin console (incl. W3Treasury → SigLayer)
- `packages/girax` — GIRAx layer (provenance, attestation, attribution, authentication)
- `packages/uzd-token` — UZD multi-chain token (Solana + Robinhood Chain + Base)
- `packages/ui` — shared design system (Solana ombre / Maple institutional)
- `services/voice` — KVM2 Grok voice lead-to-conversion services
- `services/api` — FastAPI/Python backend
- `docs/` — specs (brand/domain, entity/treasury/trading, wallet)

## Stack
Next.js + TailwindCSS + shadcn + Zustand · OTP auth · Resend · Neon Postgres
· FastAPI · Telnyx + LiveKit · Docker/Compose → Hostinger KVM2 → GCP.

## Status
Scaffold only — service implementations land as GitHub access + team contributions arrive.
