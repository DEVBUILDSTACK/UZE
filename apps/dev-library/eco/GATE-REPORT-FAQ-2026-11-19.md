# Design Gate Report — the two FAQ levels (macro + micro)

Date: 2026-11-19 · Gate: repo-vendored `tools/design-gate/gate.mjs` v0.2
Change washed: the Buildr Team subdomain joins both levels of the FAQ
taxonomy — (1) a new topic, "The two addresses — this library & UZE
Buildr Team", in the macro **UZE Dev Partner FAQ** on the Dev Library
page (`library-index.html`); (2) a new post-OTP page inside this app,
**"How Buildr Team works — step by step"** at `/faq`, reached from the
signed-in nav ("How it works") and from the home "How this site works"
card. Method as in GATE-REPORT-2026-11-19.md: the eco pages were
rendered from the running app (temp data dir, host override, real OTP
sign-in as a full-access contributor) to local files and washed;
screenshots were looked at, not just produced.

| Page | Palette | Wordmark (420px) | Axe (420px) | Verdict |
|---|---|---|---|---|
| Dev Library page (macro FAQ, changed) | PASS — 8 hexes, all tokens | PASS — "UZE Dev Library", 1.00 line, nowrap | 0 violations | **PASS** (exit 0) |
| Buildr Team — micro FAQ `/faq` (new) | PASS — 8 hexes, all tokens | PASS — "UZE Buildr Team", 1.00 line, nowrap | 0 violations | **PASS** (exit 0) |
| Buildr Team — home, signed in (nav changed) | PASS — 8 hexes, all tokens | PASS — 1.00 line, nowrap | 0 violations | **PASS** (exit 0) |
| Buildr Team — Ecosystem (unchanged, control) | PASS — 8 hexes, all tokens | PASS — 1.00 line, nowrap | 0 violations | **PASS** (exit 0) |
| Buildr Team — sign-in door (unchanged, control) | PASS — 8 hexes, all tokens | PASS — 1.00 line, nowrap | 0 violations | **PASS** (exit 0) |

## House skill §6 pre-ship check — line by line, both FAQ surfaces

1. **Render at 420px and 1280px, full-page screenshots.** Done for all
   five targets above (gate `--out` evidence: report + both renders
   per page).
2. **Look at both screenshots.** The 420px and 1280px renders of the
   micro FAQ and the 420px render of the Dev Library page were
   inspected directly. The micro FAQ reads in order, steps 1–9, with
   the pillars named in step 5; the macro topic sits in the topic
   list between "Access changes & resets" and "Contact — the desk".
3. **Wordmark check.** Gate-measured one line at 420px on both
   surfaces ("UZE Dev Library" 27.6px = 1.00 line; "UZE Buildr Team"
   26.0px = 1.00 line), `white-space: nowrap` present, UZE in
   tangerine, companion reversed out of ink. No wrap.
4. **Palette check.** Gate palette lint on every washed page: 8
   distinct hex values, all house tokens (ink, cream, tangerine,
   creamsicle, hairline, muted, band-muted, white). The new copy adds
   no feedback elements and no hues; the one inline style added (the
   home card's FAQ link) uses `var(--ink)`, no hex.
5. **Three-second test.** Micro FAQ first phone screen: the wordmark
   band, the nav, and the card title "How Buildr Team works — step
   by step" with its one-line hook ("Every screen in the order you
   meet it, with the exact buttons named. Nine short steps.") —
   nothing else competes. The macro surface's first screen is
   unchanged (wordmark band, sign-in card); the FAQ section itself
   still opens with its creamsicle title band naming the FAQ and who
   it is for. No version numbers, word counts, runtimes, or
   production notes appear anywhere in the new copy.
6. **Component pass.** The macro topic uses the section's existing
   `details.faq` pattern — hairline top border, Georgia serif
   summary, same Q&A rhythm as the other nine topics. The micro page
   uses the app's existing card, serif step heads, and ink doc links;
   the new nav pill follows the existing sections pattern including
   `aria-current="page"`; no new component was introduced.
7. **Accessibility floor.** Axe at 420px: **0 violations** on all
   five washed targets.
8. **Regression guard.** New assertions in both suites: `test.mjs` —
   the macro topic list extended to ten and a per-address assertion
   (buildr-eco.uzemarkets.com, UZE Buildr Team, both sign-in labels,
   the other-surface button, the four org names); the standing
   no-"reading room" assertion covers the new topic. `eco/test.mjs` —
   unsigned `/faq` redirects to the door; the signed-in page renders
   with the step labels ("Email me a sign-in code", "Team overview —
   completed", "Not your section", desk@); the pillars are named as
   pillars and linked to `/surfaces/human` and `/surfaces/agentic`;
   no internal naming; the home carries the `/faq` door. Tallies:
   Dev Library suite **147 passed / 0 failed**; eco suite
   **71 passed / 0 failed**.

Notes:
- The FAQ copy is written from the rendered interface only — every
  step names a control that exists with that exact label ("Email me
  a sign-in code", "One-time code", "Team overview — completed",
  "Your other surface", "Not your section", "Sign out").
- Step 5 names the pillars as pillars and links to the surface pages
  where the pillar addenda live; the FAQ does not summarize them.
