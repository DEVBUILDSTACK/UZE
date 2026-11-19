# Design Gate Report — UZE Buildr Team (eco contributor surface)

Date: 2026-11-19 · Gate: `~/workspace/tools/design-gate/gate.mjs` v0.2
Method: the eco pages were rendered from the running app (temp data
dir, host override) to local files and washed — palette lint against
the eight tokens, 420px + 1280px renders, wordmark one-line check,
axe floor. Screenshots were looked at, not just produced.

| Page | File | Palette | Wordmark | Axe (420px) | Verdict |
|---|---|---|---|---|---|
| Home, signed out (the door) | home-signed-out.html | PASS | PASS — one line | 0 violations | **PASS** (exit 0) |
| Home, signed in (full-access contributor) | home-signed-in.html | PASS | PASS — one line | 0 violations | **PASS** (exit 0) |
| Ecosystem (overview + diagrams + programmatic band) | ecosystem.html | PASS | PASS — one line | 0 violations | **PASS** (exit 0) |

Notes:
- Two floor findings from the first wash were fixed before this
  report: page content now sits inside a `<main>` landmark, and the
  generated code/diagram blocks are keyboard-focusable
  (`tabindex="0"` in `eco/build-content.mjs`). The re-wash is clean.
- Generated content fragments are palette-sanitized by the converter:
  the source documents discuss off-palette hexes (they document wash
  failures); every non-token hex is replaced with ink in the served
  fragments. Verified: the only hexes present in `eco/content/*.html`
  are the eight tokens.
- The Mermaid diagrams render client-side from the CDN; in the
  offline gate render they appear as their readable code blocks —
  the designed graceful fallback (the code is also the
  machine-readable seed, shown in the collapsible "Diagram code"
  block under each diagram).
- The programmatic band sits in creamsicle beneath the two-surface
  content, framed as the underpinning of both surfaces — not a
  third surface.
