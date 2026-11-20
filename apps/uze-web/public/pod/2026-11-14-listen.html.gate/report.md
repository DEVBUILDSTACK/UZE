# Design gate report

- Target: /home/hatch/workspace/uze-gira/monorepo/apps/uze-web/public/pod/2026-11-14-listen.html
- When: 2026-11-20T12:33:50.712Z
- Chrome: /home/hatch/.cache/puppeteer/chrome/linux-157.0.8103.50/chrome-linux64/chrome
- Verdict: FAIL
- Failures:
  - palette violation: #555555 (as #555) ×2 — not a house token
  - palette violation: #ddd3c8 (as #ddd3c8) ×2 — not a house token
  - palette violation: #8a8378 (as #8a8378) ×1 — not a house token
  - palette violation: #fbf9f6 (as #fbf9f6) ×2 — not a house token
  - palette violation: #ffe3cc (as #ffe3cc) ×1 — not a house token
  - wordmark not wrap-protected at 420px: "Saturday POD — The Bellwether Falls, the Hike Gets Priced" computes white-space: normal (house rule: white-space: nowrap); rendered lines in this engine: 3.00 at 30px — one line must be guaranteed by the nowrap rule, not by this render's font metrics

```
DESIGN GATE — /home/hatch/workspace/uze-gira/monorepo/apps/uze-web/public/pod/2026-11-14-listen.html

[FAIL] palette violation: #555555 (as #555) ×2 — not a house token
[FAIL] palette violation: #ddd3c8 (as #ddd3c8) ×2 — not a house token
[FAIL] palette violation: #8a8378 (as #8a8378) ×1 — not a house token
[FAIL] palette violation: #fbf9f6 (as #fbf9f6) ×2 — not a house token
[FAIL] palette violation: #ffe3cc (as #ffe3cc) ×1 — not a house token
[OK]   render — screenshot-420.png (420px, full page)
[FAIL] wordmark not wrap-protected at 420px: "Saturday POD — The Bellwether Falls, the Hike Gets Priced" computes white-space: normal (house rule: white-space: nowrap); rendered lines in this engine: 3.00 at 30px — one line must be guaranteed by the nowrap rule, not by this render's font metrics
[PASS] quiet-link check — no raw URL serves as link text
[WARN] axe floor — 2 violation rule(s) at 420px (report-only, see README):
         - color-contrast (serious, 40 node(s)) — Elements must meet minimum color contrast ratio thresholds
         - label-content-name-mismatch (serious, 1 node(s)) — Elements must have their visible text as part of their accessible name
[OK]   render — screenshot-1280.png (1280px, full page)

GATE: FAIL — 6 failure(s)
```
