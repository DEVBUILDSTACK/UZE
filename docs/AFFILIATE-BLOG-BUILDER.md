# C3 Affiliate Blog Builder — voice-driven white-labeled blogs

**Vision:** Google's "there's an app for me" becomes UZE's "there's a blog for me."
Every affiliate gets a white-labeled blog at `{handle}.uze.fi`, built by voice
in the C3 console, fed by autonomous content pipelines, settled through the
Web3 Global Treasury.

## Capability unlock (2026-10-13)

Google Play now supports **private vibe-coded apps built in Google AI Studio**:
describe the app, install it on your own Android via Play, invisible to everyone
else. US-only, 18+ at launch; sharing with trusted circles coming; public
publishing after safety review.
([TechCrunch](https://techcrunch.com/2026/10/13/google-play-now-supports-private-vibe-coded-apps-built-just-for-you/))

For UZE this unlocks a **private C3 builder companion app**: the operator
voice-drives AI Studio, and the resulting tooling stays private to the team.

## Flow

1. **Voice → C3 console.** Operator or affiliate describes the blog by voice
   (Grok Voice / AI Studio voice input).
2. **C3 drives Google AI Studio** to generate the white-labeled blog
   (affiliate branding, UZE platform chrome optional).
3. **Deploy to `{affiliate}.uze.fi`.** Multi-tenant blog platform, subdomain
   routing, per-affiliate theme tokens on the shared design system.
4. **Autonomous content via n8n.io.** Per-affiliate workflows: sources,
   schedule, tone, draft → review → publish.
5. **Paid content via x402 (pay-as-you-go).** Premium scraped/API content
   settled per-article in USDC micropayments — no subscriptions, pure usage.
6. **Video attention + UGC.** Affiliates publish world-class motion/video;
   base-level affiliated content syndicates across the network.
7. **Web3 Global Treasury.** Ad/referral revenue and content payouts tracked
   onchain; affiliate earnings flow into UZD payouts.

## Architecture

| Piece | Implementation |
|---|---|
| C3 module | `/blog-builder` — voice input → AI Studio → preview → deploy |
| Blog platform | Multi-tenant Next.js, subdomain routing, shared components |
| Content pipelines | n8n.io workflows per affiliate (scrape, curate, draft, publish) |
| Paid sources | x402 pay-per-call (scraped data, premium APIs) |
| Video/UGC | Affiliate uploads + syndication feed across blogs |
| Settlement | Web3 Global Treasury → UZD affiliate payouts |

## Constraints

- AI Studio private-app path is **US-only, 18+** — the builder companion app
  is US-only for now; the blogs themselves are web and unaffected.
- Play policies still apply to the private app.
- Consumer blog copy follows UZE rules: no tokens/chains until built + approved.

## Open questions

- Programmatic AI Studio API access for the voice-driven flow (vs manual build).
- x402 provider selection for pay-per-scrape content sources.
- Moderation pipeline for affiliate UGC before syndication.
