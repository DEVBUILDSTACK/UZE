# Design gate report

- Target: /home/hatch/workspace/uze-gira/monorepo/apps/uze-web/public/pod/index.html
- When: 2026-11-20T14:42:14.850Z
- Chrome: /home/hatch/.cache/puppeteer/chrome/linux-157.0.8103.50/chrome-linux64/chrome
- Verdict: FAIL
- Failures:
  - palette violation: #555555 (as #555) ×1 — not a house token
  - palette violation: #ddd3c8 (as #ddd3c8) ×2 — not a house token
  - palette violation: #fbf9f6 (as #fbf9f6) ×1 — not a house token
  - wordmark not wrap-protected at 420px: "Every edition, week by week" computes white-space: normal (house rule: white-space: nowrap); rendered lines in this engine: 2.00 at 32px — one line must be guaranteed by the nowrap rule, not by this render's font metrics

```
DESIGN GATE — /home/hatch/workspace/uze-gira/monorepo/apps/uze-web/public/pod/index.html

[FAIL] palette violation: #555555 (as #555) ×1 — not a house token
[FAIL] palette violation: #ddd3c8 (as #ddd3c8) ×2 — not a house token
[FAIL] palette violation: #fbf9f6 (as #fbf9f6) ×1 — not a house token
[OK]   render — screenshot-420.png (420px, full page)
[FAIL] wordmark not wrap-protected at 420px: "Every edition, week by week" computes white-space: normal (house rule: white-space: nowrap); rendered lines in this engine: 2.00 at 32px — one line must be guaranteed by the nowrap rule, not by this render's font metrics
[PASS] quiet-link check — no raw URL serves as link text
[WARN] axe floor — 3 violation rule(s) at 420px (report-only, see README):
         - color-contrast (serious, 14 node(s)) — Elements must meet minimum color contrast ratio thresholds
         - heading-order (moderate, 1 node(s)) — Heading levels should only increase by one
         - label-content-name-mismatch (serious, 1 node(s)) — Elements must have their visible text as part of their accessible name
[OK]   render — screenshot-1280.png (1280px, full page)

GATE: FAIL — 4 failure(s)
```
