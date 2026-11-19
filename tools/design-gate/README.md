# UZE design gate

The pre-ship verification gate for UZE-branded pages, built as Onboard 2 of the
design-capability recommendation (`~/workspace/research_notes/design-capability-2026-11-19/`).
It encodes the house system in `~/workspace/custom-skills/uze-design-system/SKILL.md` §6
as a single command that **fails the build** instead of relying on a human catching
design errors on a phone after deploy.

## Run it

```bash
cd ~/workspace/tools/design-gate
node gate.mjs <page-file-or-local-url> [--out <dir>]
```

- Target: a local HTML file, or a URL on `localhost` / `127.0.0.1` (serve the app
  locally first). Public URLs are refused: the sandbox Chrome binary cannot reach
  the internet (direct connections fail with `ERR_TUNNEL_CONNECTION_FAILED`), and a
  gate that renders a different network copy than the one being shipped proves little.
- Output: `report.md` plus `screenshot-420.png` and `screenshot-1280.png` in the out
  dir — default `<page-file>.gate/` beside the target file (or `./design-gate-out/`
  for URL targets).
- Exit codes: `0` PASS · `1` FAIL (named failures printed) · `2` gate could not run.
- Chrome is auto-discovered from `~/.cache/puppeteer/` (newest full Chrome, falling
  back to chrome-headless-shell); override with `CHROME_PATH=/path/to/chrome`.
- Dependencies (`puppeteer-core`, `axe-core`) are installed locally in this folder
  only — `npm install --no-workspaces` — never global.

## What it checks

1. **Palette lint.** Every hex color in the page source (3/4/6/8-digit forms,
   normalized to 6-digit RGB, case-insensitive) must be one of the eight house
   tokens: `#1a1a1a` ink · `#f5f2ee` cream · `#ff6b00` tangerine · `#FDEEE2`
   creamsicle · `#ddd5c9` hairline · `#6b655e` muted · `#b8b0a4` band-muted ·
   `#ffffff` white. Any other value is a named failure with its occurrence count.
   This is the check that makes the 2026-11-18 red/green status colors
   (`#b02a37` / `#2e7d32`) a build failure instead of a screenshot review.
2. **Renders.** Full-page screenshots at 420px (phone) and 1280px (desktop),
   saved beside the report for the builder's own visual pass (house skill §6.1–6.2:
   the screenshots are looked at, not just produced).
3. **Wordmark one-line check at 420px**, measured on the live render of the header
   `h1`, in two parts:
   - the wordmark must carry `white-space: nowrap` (computed style; house rule §2).
     This is the guarantee: rendered fit in one engine is font-metric luck — the
     2026-11-18 wrap reached a phone whose render differed from desktop Chromium —
     so the gate refuses to accept a wordmark that merely *happens* to fit here;
   - it must occupy exactly one line (rendered height ÷ computed line-height ≤ 1.25)
     with no horizontal overflow (scrollWidth vs clientWidth). This measure is live
     independently: a forced break fails it even with `nowrap` present
     (see PROOF-2026-11-19.md, mutant 4).
4. **Axe floor.** axe-core runs on the 420px render; violations are printed by rule
   id with impact and node count, and recorded in the report.

## Axe status

**Working.** `axe-core` (npm, MPL-2.0) is installed locally in this folder and
injected into the rendered page from its local file (`node_modules/axe-core/axe.min.js`)
— no network needed at gate time.

Axe findings are currently **report-only (WARN, not a gate failure)**, deliberately:
the Dev Library page carries two known findings (see PROOF-2026-11-19.md —
`select-name`, critical, the filter `<select>`s have no accessible name; and
`heading-order`, moderate). Failing every build on findings that predate the gate
would train everyone to ignore the gate. **Known next step:** fix those two findings
in the page, then promote axe violations of impact `critical`/`serious` to hard
failures in `gate.mjs`. Until then the floor exists, is printed on every run, and
cannot silently regress without showing up in a report.

## Proof

`PROOF-2026-11-19.md` in this folder: the current Dev Library page PASSes; a mutant
with `#b02a37` injected FAILs naming the palette violation; a mutant with the
wordmark `nowrap` removed FAILs naming the one-line violation — commands and actual
outputs, with the screenshots under `proof/`.
