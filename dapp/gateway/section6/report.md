# Design gate report

- Target: /home/hatch/workspace/ghpages-push/dapp/gateway/demo.html
- When: 2026-11-28T03:37:06.853Z
- Chrome: /home/hatch/.cache/puppeteer/chrome/linux-157.0.8103.78/chrome-linux64/chrome
- Verdict: PASS
- Failures: none

```
DESIGN GATE — /home/hatch/workspace/ghpages-push/dapp/gateway/demo.html

[PASS] palette lint — 8 distinct hex value(s), all house tokens
[OK]   render — screenshot-420.png (420px, full page)
[PASS] wordmark one-line at 420px — "UZEmarkets" on one line (height 25.0px = 1.00 line at 23px, white-space: nowrap)
[PASS] quiet-link check — no raw URL serves as link text
[WARN] axe floor — 1 violation rule(s) at 420px (report-only, see README):
         - link-in-text-block (serious, 1 node(s)) — Links must be distinguishable without relying on color
[OK]   render — screenshot-1280.png (1280px, full page)

GATE: PASS
```

## Turn 4 — harness extension: attestation/ITA display + models-list mock view (2026-11-27)

The gate run above re-rendered this report and both screenshots against the
extended page. The Turn 3 palette-cycle record previously appended here is
preserved in git history (commit `cd34818`).

### What was built

- `demo.html` — two new mock-mode sections, all existing sections unchanged:
  - **Attestation & ITA token — simulated evidence**: button fetches the mock
    attestation report (`fetchAttestation`) and the mock ITA token
    (`fetchItaToken`) through the client and renders both values under a
    "MOCK — simulated values only" label line.
  - **Models — the mock catalogue**: button lists the mock models from the
    client's `/models` path (`listModels`), each entry rendered with a
    `[MOCK]` suffix under a "MOCK — simulated catalogue only" label line.
- `gateway-client.js` — the mock transport already served `/models` and
  `/attestation/ita-token`, but the client exposed no methods for them; added
  `listModels()` and `fetchItaToken()` in the same pattern as
  `fetchAttestation()` (key required in real mode; additive only — no
  existing behavior changed).
- `demo.test.js` — four new checks (attestation flow, models flow, new-section
  wiring, and a rendered-output check that runs the page's own inline script
  against a stub DOM, clicks every button, and asserts mock labelling in what
  the page actually renders).

### Tests re-run (Maker, Turn 4)

```
$ node dapp/gateway/demo.test.js
PASS 1 — page Class A flow: mock completion returned, labelled mock
PASS 2 — page Class B flow: attestation precedes request; provider_tee verified
PASS 3 — page fail-closed flow: wrong signatureKind refused (VERIFICATION_FAILED), no answer used
PASS 4 — page fail-closed flow: absent signatureKind refused (VERIFICATION_FAILED), no answer used
PASS 5 — page fail-closed flow: Gateway refusal refused (GATEWAY_HTTP), no answer used
PASS 6 — page attestation flow: mock report + mock ITA token returned, both labelled mock
PASS 7 — page models flow: mock catalogue returned from /models, labelled mock
PASS 8 — page wiring: staged client, mock mode only, no live-DApp reference, tangerine refusal marker
PASS 9 — lockup: swoop asset in header + footer, perfected geometry, nowrap wordmark
PASS 10 — palette audit: 8 distinct hex values, all house tokens
PASS 11 — new sections wiring: attestation/ITA + models sections, client paths, simulated labelling in copy
PASS 12 — rendered output: all sections render; new sections show mock-labelled report, ITA token, and model
All 12 checks passed.   (12/12, exit 0)

$ node dapp/gateway/gateway-client.test.js
PASS 1 — one door only: base is https://cloud-api.near.ai/v1
PASS 2 — mock Class A completion returns a clearly-labelled mock answer
PASS 3 — mock Class B: attestation precedes the request; provider_tee reply verified and returned
PASS 4 — fail-closed: reply with signatureKind != provider_tee is refused, answer never used
PASS 5 — fail-closed: reply with signatureKind absent is refused
PASS 6 — fail-closed: Gateway refusal surfaces as an honest error (HTTP 409), no fallback fiction
PASS 7 — no-key: real-mode call without a key fails with NO_KEY, naming the unblock
All 7 checks passed.   (7/7, exit 0)
```

### Palette audit — complete §1 token list

Complete §1 token list used for this comparison (8 tokens, case-insensitive,
cited verbatim from `~/workspace/custom-skills/uze-design-system/SKILL.md` §1):

`#1a1a1a` (Ink) · `#f5f2ee` (Cream) · `#ff6b00` (Tangerine) ·
`#FDEEE2` (Creamsicle) · `#ddd5c9` (Hairline) · `#6b655e` (Muted) ·
`#b8b0a4` (Band-muted) · `#ffffff` (White)

Full grep output — `grep -Eoni '#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|hsla?\([^)]*\)'`
(no rgb/rgba/hsl/hsla values occur in any file checked):

```
=== demo.html ===
9:#1a1a1a
10:#f5f2ee
11:#ff6b00
12:#FDEEE2
13:#ddd5c9
14:#6b655e
15:#b8b0a4
16:#ffffff

=== demo.test.js ===
116:#1a1a1a
116:#f5f2ee
116:#ff6b00
116:#fdeee2
117:#ddd5c9
117:#6b655e
117:#b8b0a4
117:#ffffff

=== gateway-client.test.js ===
(no matches)

=== gateway-client.js ===
(no matches)
```

Result: **PASS against the complete list — zero values outside the 8 tokens.**
`demo.html` carries exactly the 8 §1 tokens and nothing else; the extension
added no new color values.

### §6 screenshot check

Rendered fresh this turn by the design gate
(`~/workspace/tools/design-gate/gate.mjs`, the Turn 2 tooling) at 420px and
1280px; both screenshots in this folder were regenerated and visually
checked by the Turn 4 Maker:

- `screenshot-420.png` — wordmark "UZEmarkets" on one line with the
  Tri-Swoop in header and footer, tangerine UZE, eyebrow reversed out of the
  ink header band; both new sections present with black pill buttons; white
  secondary pills in the fail-closed card; creamsicle soft band with ink
  text; footer meta reversed out of the ink band. PASS.
- `screenshot-1280.png` — same checks at desktop width. PASS.

Gate verdict: **PASS** (see the gate output at the top of this file). The one
report-only axe WARN (link-in-text-block on the footer wordmark link) stands
as previously filed; the no-underline footer wordmark treatment is
prescribed by design system §2.
