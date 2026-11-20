# Design gate report

- Target: /home/hatch/workspace/uze-gira/monorepo/apps/uze-web/public/pod/2026-11-14.html
- When: 2026-11-20T14:32:37.752Z
- Chrome: /home/hatch/.cache/puppeteer/chrome/linux-157.0.8103.50/chrome-linux64/chrome
- Verdict: FAIL
- Failures:
  - palette violation: #555555 (as #555) ×2 — not a house token
  - palette violation: #ddd3c8 (as #ddd3c8) ×2 — not a house token
  - palette violation: #fbf9f6 (as #fbf9f6) ×1 — not a house token
  - wordmark not wrap-protected at 420px: "The Bellwether Falls, the Hike Gets Priced" computes white-space: normal (house rule: white-space: nowrap); rendered lines in this engine: 2.00 at 32px — one line must be guaranteed by the nowrap rule, not by this render's font metrics

```
DESIGN GATE — /home/hatch/workspace/uze-gira/monorepo/apps/uze-web/public/pod/2026-11-14.html

[OK]   palette lint — 7 fully transparent hex(es) ignored (alpha 00 renders as no color)
[FAIL] palette violation: #555555 (as #555) ×2 — not a house token
[FAIL] palette violation: #ddd3c8 (as #ddd3c8) ×2 — not a house token
[FAIL] palette violation: #fbf9f6 (as #fbf9f6) ×1 — not a house token
[OK]   render — screenshot-420.png (420px, full page)
[FAIL] wordmark not wrap-protected at 420px: "The Bellwether Falls, the Hike Gets Priced" computes white-space: normal (house rule: white-space: nowrap); rendered lines in this engine: 2.00 at 32px — one line must be guaranteed by the nowrap rule, not by this render's font metrics
[PASS] quiet-link check — no raw URL serves as link text
[WARN] axe floor — 3 violation rule(s) at 420px (report-only, see README):
         - color-contrast (serious, 15 node(s)) — Elements must meet minimum color contrast ratio thresholds
         - label-content-name-mismatch (serious, 1 node(s)) — Elements must have their visible text as part of their accessible name
         - landmark-unique (moderate, 1 node(s)) — Landmarks should have a unique role or role/label/title (i.e. accessible name) combination
[OK]   render — screenshot-1280.png (1280px, full page)

GATE: FAIL — 4 failure(s)
```
