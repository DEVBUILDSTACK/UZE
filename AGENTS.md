# AGENTS.md — DEVBUILDSTACK/UZE

Agent instructions for this repo. The design block below is the repo's
design anchor pointer: DESIGN.md carries the substance; this block makes
sure no agent starts work without meeting it.

## Design — read DESIGN.md before touching any branded surface

This repo builds inside the UZE design system. Before building, restyling,
or reviewing any page, email, or branded surface:

1. **Read `DESIGN.md`** at the repo root. It states the non-negotiables and
   points at the canonical tokens: `~/workspace/design-anchor/tokens.json`
   (values) and the house skill
   `~/workspace/custom-skills/uze-design-system/SKILL.md` (rules). Never
   work from remembered or invented values.
2. **Palette only** — the eight tokens, status feedback included. No red,
   no green, no conventional status hues, ever.
3. **The wordmark never wraps** — one line at phone width; reduce the
   size, never accept the wrap.
4. **Car wash before deploy — no exceptions.** Run the design gate on
   every page you ship and state the result in your delivery report:

   ```bash
   cd ~/workspace/tools/design-gate
   node gate.mjs <page-file-or-local-url>   # exit 0 pass · 1 fail · 2 could not run
   ```

   Then look at the 420px and 1280px screenshots it produces (house skill
   §6). A failed wash blocks the deploy; a page that has not been washed
   is not done, however well the code works.
5. **White-label:** tenants override token *values* only (see
   `~/workspace/design-anchor/tenant-override.spec.md`). Structure and the
   wash are invariant — never edit them per tenant.
6. **System changes** (a new token, a new tint, a rule change) are
   versioned amendments to `tokens.json` ratified by James — never a
   page-level edit.
