# Growth Suite — Overview

**Date:** 2026-10-16 · **Status:** strategy + build sequence

This suite is delivered as part of the **multi-tenant content innovation
offering** (see `AFFILIATE-CONTENT-NETWORK-OVERVIEW.md`): every capability
below is tenant-scoped to the affiliate business — their brand, their
market, their funnel. The content network is the publishing arm; this
suite is the activation arm.

The growth machine that sits alongside the Affiliate Content Network:
client-configured services, paid acquisition, autonomous voice, and the
conversion funnel — all feeding the UZE / UZED.si / Learn2Launch flywheel.

## 1. Client-configured add-on suite

Per-client services, configured to their market:

- **I) Site analysis** — audit of the client's web presence: performance,
  conversion paths, booking flow friction, mobile readiness.
- **II) SEO + GEO** — classic search optimization plus Generative Engine
  Optimization: making the client the answer AI assistants give.
- **III) Prospecting** — identifying and qualifying the client's buyers,
  partners, and sponsors.

**Scraping** — locally or in client-defined markets, targeting Google
Business profiles, websites, online resources, and offline resource lists;
list sequencing services turn raw targets into ordered outreach lists.

## 2. CRM / lead gen / affiliate targeting

- Central CRM: every scraped prospect, every inbound lead, every
  affiliate — one record, full journey.
- Affiliate targeting: match affiliates to offers by vertical, metro,
  and audience.
- In-site ads + sponsoring: paid placements and sponsorship inventory
  across the UZE surfaces (listings, content, event pages).

## 3. Paid advertising

Meta / Facebook / Instagram / Google ads — managed against the same
offer sequences as the outreach tracks, with conversion events flowing
back into the CRM.

## 4. Autonomous voice

- **Autonomous voice prospecting** — AI callers working the sequenced
  prospect lists (KVM2 voice infrastructure).
- **Autonomous voice customer service / support** — inbound handling,
  booking support, issue resolution.
- **AI-to-human transfer** — when the call needs a person, warm transfer
  to a trained call-center human with full context. (KVM2 L3 execution
  layer.)

## 5. Build sequence

In order:

1. **Resend cold-mail outreach with client offer sequences** — the
   foundation. UZEMARKET identity, `uzemarket@uze.fi` sender, sequenced
   offers per client/vertical. Email = cold.
2. **Resend + WhatsApp integrated sequences toward conversion** —
   WhatsApp is warm-only (post-engagement: opened/clicked/replied).
   The two channels run as one sequence toward conversion.
3. **Gamified SocialFi registration flow** — the conversion event:
   20-second social profile creation → handle mints affiliate identity
   (`{handle}.uze.fi` + UZE referral code) → QR share cards → viral loop.
   (Spec: `UZE-SOCIAL-PROFILE-SPEC.md`; backend OTP auth + `/profiles`
   router already in the monorepo.)

## Constraints

- WhatsApp warm-only, Meta Business compliant; mobile capture in-flow =
  WhatsApp opt-in.
- No live sends without James's per-action approval — the machine is
  built first, fired on his tap.
- Consumer copy rules apply to all outreach: no tokens/chains until
  built + approved.
