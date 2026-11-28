# Design gate report

- Target: /home/hatch/workspace/ghpages-push/dapp/gateway/demo.html
- When: 2026-11-28T03:51:19.845Z
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

## Turn 5 — refusal-path coverage for the Turn 4 sections (2026-11-27)

The gate run above re-rendered this report and both screenshots against the
extended page. The Turn 4 record previously appended here is preserved in git
history (commit `ec95473`).

### What was built

Refusal-path coverage for the two sections Turn 4 added — attestation/ITA
token and models list — following the harness's existing fail-closed pattern
(rendered errors in ink behind the tangerine "—" marker, via `showErr`):

- `gateway-client.js` — minimal, additive changes:
  - Mock transport failure modes: `mockOpts.modelsFailure`
    (`transport` / `malformed` / `empty`) and `mockOpts.itaFailure`
    (`transport` / `malformed` — a payload carrying no token).
  - `request()` now normalizes any transport/network rejection to a coded
    `TRANSPORT_ERROR` (labelled `[MOCK] simulated transport failure` in mock
    mode) instead of leaking a raw TypeError.
  - `listModels()` fails closed: a payload whose `data` is not an array of
    models with IDs is refused as `MALFORMED_RESPONSE`; an empty catalogue
    is refused as `EMPTY_CATALOGUE` rather than presented as a working list.
  - `fetchItaToken()` fails closed: a payload with no usable token string is
    refused as `MALFORMED_RESPONSE` — a missing token is never handed on.
  - No existing behavior changed: the happy-path payloads and codes are
    untouched, and the client self-test still passes 7/7 unmodified.
- `demo.html` — the two sections each gained simulate buttons (white
  secondary pills, existing classes only) that run the same flow functions
  as the section's primary button with the failure `mockOpts`, so a refusal
  renders into the section's own output (`outAtt` / `outModels`) through
  `showErr`: ITA transport failure + missing ITA token in the attestation
  section; transport failure + malformed catalogue + empty catalogue in the
  models section. One explanatory sentence per section, in the existing copy
  voice. No new colors, no new classes.
- `demo.test.js` — seven new checks (12 → 19): client-level refusals for all
  five failure modes (each asserting the error code and that the refusal
  message is labelled mock/simulated; the ITA cases also assert no token is
  handed on), a static wiring check for the five simulate buttons and their
  `mockOpts`, and a rendered-refusal check that runs the page's inline
  script in a fresh stub DOM, clicks each simulate button, and asserts the
  section output renders `REFUSED (<code>)` with a tangerine marker span
  child, the refusal text in the ink `err` span, and mock/simulated
  labelling.

### Tests re-run (Maker, Turn 5)

```
$ node dapp/gateway/demo.test.js
PASS 1 — page Class A flow: mock completion returned, labelled mock
PASS 2 — page Class B flow: attestation precedes request; provider_tee verified
PASS 3 — page fail-closed flow: wrong signatureKind refused (VERIFICATION_FAILED), no answer used
PASS 4 — page fail-closed flow: absent signatureKind refused (VERIFICATION_FAILED), no answer used
PASS 5 — page fail-closed flow: Gateway refusal refused (GATEWAY_HTTP), no answer used
PASS 6 — page attestation flow: mock report + mock ITA token returned, both labelled mock
PASS 7 — page models flow: mock catalogue returned from /models, labelled mock
PASS 8 — page models refusal flow: models transport error refused (TRANSPORT_ERROR), labelled mock/simulated
PASS 9 — page models refusal flow: models malformed payload refused (MALFORMED_RESPONSE), labelled mock/simulated
PASS 10 — page models refusal flow: models empty catalogue refused (EMPTY_CATALOGUE), labelled mock/simulated
PASS 11 — page ITA refusal flow: ITA transport error refused (TRANSPORT_ERROR), labelled mock/simulated, no token used
PASS 12 — page ITA refusal flow: ITA malformed/missing token refused (MALFORMED_RESPONSE), labelled mock/simulated, no token used
PASS 13 — page wiring: staged client, mock mode only, no live-DApp reference, tangerine refusal marker
PASS 14 — lockup: swoop asset in header + footer, perfected geometry, nowrap wordmark
PASS 15 — palette audit: 8 distinct hex values, all house tokens
PASS 16 — new sections wiring: attestation/ITA + models sections, client paths, simulated labelling in copy
PASS 17 — new sections refusal wiring: 5 simulate buttons, mockOpts failure modes, showErr into outAtt/outModels
PASS 18 — rendered output: all sections render; new sections show mock-labelled report, ITA token, and model
PASS 19 — rendered refusals: all 5 new-section failure modes render REFUSED with the tangerine marker, labelled mock/simulated, in their own section output
All 19 checks passed.   (19/19, exit 0)

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

Complete §1 token list used for this comparison (all 8 tokens, cited
verbatim from the §1 table of
`~/workspace/custom-skills/uze-design-system/SKILL.md`):

Ink `#1a1a1a` · Muted `#6b655e` · Creamsicle `#FDEEE2` ·
Band-muted `#b8b0a4` · Hairline `#ddd5c9` · Cream `#f5f2ee` ·
Tangerine `#ff6b00` · White `#ffffff`

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
152:#1a1a1a
152:#f5f2ee
152:#ff6b00
152:#fdeee2
153:#ddd5c9
153:#6b655e
153:#b8b0a4
153:#ffffff

=== gateway-client.test.js ===
(no matches)

=== gateway-client.js ===
(no matches)
```

Result: **PASS against the complete list — zero hexes outside the 8
tokens.** `demo.html` carries exactly the 8 §1 tokens and nothing else; the
refusal-path extension added no new color values.

### §6 screenshot check

Rendered fresh this turn by the design gate
(`~/workspace/tools/design-gate/gate.mjs`, run with
`--wordmark "header .wm"`) at 420px and 1280px; both screenshots in this
folder were regenerated and visually checked by the Turn 5 Maker:

- `screenshot-420.png` — wordmark "UZEmarkets" on one line with the
  Tri-Swoop in header and footer, tangerine UZE, eyebrow reversed out of
  the ink header band; both Turn 4 sections now carry their white-pill
  simulate buttons under the black-pill primary; creamsicle soft band with
  ink text; footer meta reversed out of the ink band. PASS.
- `screenshot-1280.png` — same checks at desktop width. PASS.

Gate verdict: **PASS** (see the gate output at the top of this file). The one
report-only axe WARN (link-in-text-block on the footer wordmark link) stands
as previously filed; the no-underline footer wordmark treatment is
prescribed by design system §2.
