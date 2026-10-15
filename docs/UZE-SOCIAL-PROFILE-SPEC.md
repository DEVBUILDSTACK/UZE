# UZE Social Profile — 20-Second Referral Onboarding Spec

**Date:** 2026-10-14. **Status:** DRAFT for team build. **Model:** Robinhood Social (reference screenshots on file).
**Author:** SoSeem, per James.

## Objective

Turn every interested cold-email recipient (UZEMARKET/Resend) and every warm
social/web interaction into a **20-second social feed profile creation**.
Creating the profile IS the referral/business offer engagement — not a form
that leads to an offer, but the offer itself.

## Entry points

| Source | CTA |
|---|---|
| UZEMARKET cold email | "Create your UZE profile in 20 seconds" (not "sign up") |
| Warm socials / web portals | Same CTA, deep-linked |
| QR share card (scan) | Lands on the profile, then "create yours" |

## The 20-second flow (3 screens, no wallet, no KYC)

1. **Handle** — pick a username (uniqueness checked inline). This becomes
   `{handle}.uze.fi` and the UZE referral code.
2. **Avatar + bio** — photo (or generated avatar), 120-char bio, interest
   tags ("Goes to F1", "Books VIP tables", "Follows [artist]").
3. **QR share card** — profile rendered as a scannable card with Share /
   Copy-link. The user leaves holding a viral object.

**Deferred past the 20 seconds:** wallet linking, payout setup, KYC/KYB.
Nothing that needs a decision lives in onboarding.

## What one creation mints

- Feed identity (username, avatar, bio, interest tags)
- Affiliate identity: `{handle}.uze.fi` blog (provisioned behind the scenes
  per the C3 affiliate blog builder spec)
- UZE referral code (auto-issued, encoded in the QR card + link)
- Referral attribution chain (scanner → creator) feeding UZD payouts

## Feed mechanics (stolen from the reference)

- **Verified activity as content.** Their "verified trades, P&L" → our
  "verified tickets, events attended." The profile is a feed identity, not a form.
- **Stats bar as status.** Their 1D/1Y P&L + profit rate → our events
  attended, referrals driven, UZD earned. Status drives sharing.
- **Interest-tagged discovery.** "Explore profiles" with "Talks about X"
  rows → ours: vertical/interest rows with Follow buttons. Topic graph from day one.
- **Authority card.** Bio + stats + content = the pitch. Top creators and
  affiliates are discoverable by proof, not claims.
- **Empty-state nudge.** New user with no follows lands on "Explore
  profiles →" — pushed into the graph immediately, never a dead end.

## QR share card — the viral object

Every profile renders as a shareable QR card (avatar, handle, brand mark)
with Share / Copy-link. Scan → view profile → "create yours" → attribution
recorded to the scanner's referrer. This is the UZE-code flywheel made
scannable: the more profiles shared, the more events pay for distribution,
the more affiliates earn UZD.

## Referral attribution → UZD

- QR scan or referral link → new profile creation records `referred_by`.
- Attribution flows into the affiliate leaderboard and UZD payout engine
  (per the affiliate blog builder spec and UZD fair-launch plan).
- Anti-gaming: one profile per verified contact (email or phone); payout
  tiers, not per-head bounties.

## Non-goals (consumer copy discipline holds)

- No tokens, chains, or "super-intelligence" in consumer surfaces.
- No wallet, chain, or payout language inside the 20-second flow.

## Open questions for James

1. Referral reward shape: flat UZD per qualified referral, tiered, or rev-share only?
2. Handle policy: first-come usernames, or reserved handles for artists/venues?
3. Profile moderation: community guidelines enforcement — automated, human, or both at launch?
