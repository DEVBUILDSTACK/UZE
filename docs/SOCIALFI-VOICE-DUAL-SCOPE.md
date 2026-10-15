# Dual-Track Scope: SocialFi Flow + KVM2 Tri-Level Agentic Voice

**Date:** 2026-10-14. **Status:** SCOPED per James. **Author:** SoSeem.

Two tracks, built in parallel. Track A is code (backend done, frontend
scaffolded). Track B is spec-first (KVM2 provisioned, then built).

---

## Track A — SocialFi onboarding flow (BUILD)

**Goal:** the low-friction introduction to UZE as a SocialFi app —
email → OTP → 20-second profile → referral identity.

### Built (2026-10-14, pushed to DEVBUILDSTACK/UZE)

| Piece | Location | Status |
|---|---|---|
| `POST /auth/otp/request` | `services/api/src/otp.py` + `routers/auth.py` | ✅ Pushed (`dbcd1d3`) |
| `POST /auth/otp/verify` (JWT, auto-create) | same | ✅ Pushed |
| `/profiles` router (check/create/public) | `services/api/src/routers/profiles.py` | ✅ Pushed |
| Prisma User: handle/bio/avatarUrl/interests/referralCode/referredBy | `prisma/schema.prisma` | ✅ Pushed |
| Resend config (`UZEMARKET` sender) | `src/config.py` | ✅ Pushed |
| Onboarding flow scaffold (5 pages) | `apps/uze-web/src/app/onboard/` | ✅ Pushed (scaffold) |
| Flow spec | `docs/UZE-SOCIAL-PROFILE-SPEC.md` | ✅ Pushed |

### Remaining for the team

- [ ] `prisma generate` + migration for the new User fields (needs Neon)
- [ ] Resend domain verification (SPF/DKIM/DMARC) + `RESEND_*` secrets
- [ ] Flesh out the onboard pages (styling per the Solana-ombre / Maple
      dual-theme system, QR rendering lib, avatar upload)
- [ ] `{handle}.uze.fi` provisioning hook on profile creation (C3 blog builder)
- [ ] Airdrop waitlist endpoint + GIRAx Treasury Plunder game flow (Plane 2)
- [ ] Intl mobile capture on the profile step (unlocks WhatsApp opt-in)

### Non-goals

No wallet, no KYC, no tokens/chains language inside the 20-second flow.

---

## Track B — KVM2 tri-level agentic voice (SPEC → BUILD)

**Goal:** voice concierge on the Hostinger KVM2 comms VPS, fronted by a
hospitality entry team and routed to specialist agent desks.

Spec: `docs/KVM2-AGENTIC-VOICE-SPEC.md`. Build starts after KVM2 SSH access
lands (Phase 0 of the KVM2 plan) and the SocialFi backend is deployed.

### Levels (per James)

- **L1 Entry:** Hospitality team pool — all markets, all languages, first voice
- **L2 Specialist desks:** GIRA, GIRAx, ONE, SoSim, SoSim Sisters (see spec)
- **L3 Execution:** booking / settlement handoff to backend + x402

---

## How the tracks connect

The SocialFi flow acquires the user (profile + mobile). The voice layer
serves them: GIRA assists across the marketplace, SoSim books the talent,
ONE brokers the assets. The mobile captured in Track A is the identifier
the voice layer calls back on (WhatsApp via Meta Business).
