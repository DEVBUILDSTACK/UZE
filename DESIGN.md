# DESIGN.md — DEVBUILDSTACK/UZE (the UZE monorepo)

> This file is the repo's design anchor: any human or agent opening this
> repo absorbs the UZE design system — the **HUMAN ECOSYSTEM DESIGN**
> (James, 2026-11-19; counterpart: the AGENTIC ECOSYSTEM DESIGN) — from
> this one file before building or restyling any branded surface.
>
> System status: RATIFIED by James 2026-11-19 — the house skill and these
> tokens are standing practice. The tokens and rules below transcribe the
> system he approved (the v5 email).

## What this is

Every UZE-branded page, email, and surface in this repo is built inside one
design system — the same system across the whole ecosystem, in every repo,
and resident inside any white-label / multi-tenant deployment of this
software. This file states the non-negotiables and points at the canonical
values. It does not carry its own copy of the values: values live in one
place and this file resolves to them.

## Canonical source — read values from here, never from memory

- **Tokens (machine-readable):** `~/workspace/design-anchor/tokens.json`
  (v1.0.0, 2026-11-19) — the single source of values. A vendored copy for
  web surfaces: `~/workspace/design-anchor/tokens.css` (`:root` custom
  properties, generated from the JSON, value-for-value identical).
- **Rules (the house skill):** `~/workspace/custom-skills/uze-design-system/SKILL.md`
  — palette, wordmark, type, components, feedback, and the pre-ship check.
- **Design sample of record:** the approved v5 UZE email (monorepo
  `apps/dev-library/lib/mailer.mjs`). When a surface and the email disagree,
  the email's treatment governs until James rules otherwise.
- **Changes** to the system are versioned amendments to `tokens.json`
  (version bump + dated note in the house skill), ratified by James.
  Advisory input (Jonathan Schmidt; his Fort Lauderdale motion-graphics
  collaborator) enters the same way — as a proposed amendment, never as a
  page-level edit. **A page edit is never a design-system change.**

## The non-negotiables

1. **Palette only.** The only colors anywhere — layout, components, charts,
   **status feedback included** — are the eight tokens:
   ink `#1a1a1a` · cream `#f5f2ee` · tangerine `#ff6b00` ·
   creamsicle `#FDEEE2` · hairline `#ddd5c9` · muted `#6b655e` ·
   band-muted `#b8b0a4` · white `#ffffff`.
   **Never** red, green, blue, amber, or any "conventional" status color.
   Errors, successes, and notices render in ink; an error additionally
   takes the tangerine "—" marker. (On 2026-11-18 red/green status colors
   shipped in a page that had no red or green in its approved system. That
   is the failure this rule exists to prevent.)
2. **The wordmark never wraps.** "UZE" is always tangerine; the companion
   word is white reversed out of ink, or ink on a light ground. One line at
   every width, phone included: `white-space: nowrap`, and at ≤620px the
   size steps down (29px → 23px) — reduce the size, never accept the wrap.
   A wrapped wordmark is a build failure, on the same level as a failed
   test. Footer form: `© 2026 UZEmarkets` centered in an ink band, "UZE"
   tangerine linking to https://uzemarkets.com, no underline.
   **Quiet links (James, 2026-11-19):** anything that can be hyperlinked
   is hyperlinked, but a link never shows a raw scheme-ful URL as its
   text — it carries a label. Quiet surfaces (the footer eyebrow
   THE TALENT DESK · DEV LIBRARY · BUILDER COLLABORATOR, addresses in
   copy) sit muted with a hairline underline and resolve to ink on
   hover (white on ink bands); tangerine stays reserved for the
   wordmark, primary links, and actions. The car wash fails a raw URL
   used as link text.
3. **Buttons are black pills.** Ink background, white text,
   `border-radius: 999px`, sans 700. Secondary: white pill, ink text, ink
   border. No square buttons, no colored buttons.
4. **Bands.** Ink bands carry reversed-out content (white display text,
   tangerine wordmark accent, band-muted eyebrows; radius 14px, padding
   20px 34px). Creamsicle soft bands carry centered ink content (radius
   12px, padding 26px 24px, serif headline).
5. **Cards and hairlines.** White card surface, 1px hairline border,
   radius 14px, padding 28px 34px. Dividers are 1px hairlines, full width —
   never heavy, never colored. Tags are tangerine *outline* pills, never
   filled. Links are tangerine 700.
6. **Type.** Georgia serif is display only (headlines 29px/1.2/700, card
   titles 21px/1.25/700). Body is system sans 16px/1.65. Serif body copy is
   out of system. Full scale: `tokens.json` → `typeScale`.

## The car wash — no page deploys unwashed

Every page goes through the design gate before it deploys — checked,
washed, dried, and held to the standard, the same way every time:

- **The gate:** `tools/design-gate/` in this repo (a pinned vendored copy
  of the canonical gate, `~/workspace/tools/design-gate/`) —
  `node gate.mjs <page-file-or-local-url> [--out <dir>]`.
  Exit 0 = pass · 1 = fail (named failures) · 2 = gate could not run.
  It lints every color in the page against the token allowlist, renders at
  420px and 1280px, verifies the wordmark sits on one line at phone width
  (nowrap carried + one rendered line + no horizontal overflow), and runs
  the axe accessibility floor.
- **In CI:** the `design-car-wash` job in
  `.github/workflows/deploy-dev-library.yml` washes every page listed in
  `design-wash.json` (repo root), and the deploy job `needs:` it — a
  failed wash fails the deploy. Wash evidence (reports + screenshots) is
  uploaded as the `design-wash-evidence` artifact on every run.
- **By eye, too:** the gate's screenshots are *looked at* before ship
  (house skill §6) — first phone screen carries title, subject, hook, and
  nothing else competes with them (James's three-second test). Automation
  is the floor; the look is the standard.
- A delivery report states the wash result: screenshots + palette result +
  test tally. If James has to ask "have we tested?", the report failed.

## White-label / multi-tenant rule

If this software is deployed for a tenant (enterprise / larger-SME
engagements), the tenant receives **token overrides only**: their palette
and marks replace the *values* in `tokens.json` for their deployment (see
`~/workspace/design-anchor/tenant-override.spec.md`). The structural rules
above — one-line wordmark, type-scale relationships, component geometry,
the accessibility floor — and **the car wash itself never change**. The
gate runs against the tenant's effective tokens. The design sensitivity
stays resident because the wash and the structure are invariant; only the
paint is tenant property.

## This repo

- Branded surfaces in this repo: `apps/dev-library` (UZE Dev Library —
  dev.uzemarkets.com) and `apps/uze-web` (uzemarkets.com).
- Wash targets (pages the workflow gates): see `design-wash.json` —
  `apps/dev-library/public/index.html` (file target, washed by the
  `design-car-wash` job in deploy-dev-library.yml) and the uze-web routes
  `/`, `/mcp-utility`, `/knowledge-base` (URL targets against the locally
  served production build, washed by the `design-car-wash-web` job in
  deploy.yml; wordmark measured on the `.wordmark` element).
- **uze-web wash state at wiring (2026-11-19): FAILING on four hexes, by
  record.** The wordmark passes (nowrap, one line) and the clear
  violations were fixed at wiring (pure-black hover and scrim → ink;
  debug red `#d64545` → ink). What remains is a working tint/shade
  practice the eight-token set does not cover: link shade `#c24e00`,
  button hover shade `#e05f00`, banner tint `#fff4ec`, ombre end
  `#ff9e45` — held for James's ruling (ratify as named derivative tokens
  in `tokens.json`, or flatten to the eight). Until he rules, the wash
  holds uze-web deploys — that is the gate working as ratified.
- Tenant deployments: none.
