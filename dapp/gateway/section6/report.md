# Design gate report

- Target: /home/hatch/workspace/ghpages-push/dapp/gateway/demo.html
- When: 2026-11-28T03:17:44.986Z
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

## Turn 3 — palette cycle re-audit (2026-11-27)

### Discrepancy note

Turn 2's audit (`work/audits/turn-002-audit.md`) failed this PR on the palette
check alone, naming `#b8b0a4` as off-token and directing its replacement.
That audit's token list omitted **Band-muted `#b8b0a4`**.

The design system §1 ( `~/workspace/custom-skills/uze-design-system/SKILL.md`,
the source of record) lists Band-muted `#b8b0a4` as a token, with the role
"Eyebrow text reversed out of ink bands". In `demo.html` it is used only in
that filed role:

- `--band-muted:#b8b0a4` (line 15), consumed as `color:var(--band-muted)` by
  `.band .eyebrow` — the header ink band's eyebrow;
- footer meta inside the ink `.band` footer:
  `style="color:var(--band-muted);…"`.

No other use exists. A conformant token was not replaced. No color change
was made in Turn 3.

### Palette audit — complete §1 token list

Complete §1 token list used for this comparison (8 tokens, case-insensitive):

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
88:#1a1a1a
88:#f5f2ee
88:#ff6b00
88:#fdeee2
89:#ddd5c9
89:#6b655e
89:#b8b0a4
89:#ffffff

=== gateway-client.test.js ===
(no matches)

=== gateway-client.js ===
(no matches)
```

Result: **PASS against the complete list.** `demo.html` carries exactly
8 distinct hex values, and every one is a §1 token (case-insensitive match;
`#FDEEE2` in the page vs `#fdeee2` in the test file is the same token).
`demo.test.js` carries the same 8 tokens — its own `TOKENS` set already
includes `#b8b0a4`. No value is outside the complete list, so no replacement
was made.

### Tests re-run (Maker, Turn 3)

```
$ node dapp/gateway/demo.test.js
PASS 1 — page Class A flow: mock completion returned, labelled mock
PASS 2 — page Class B flow: attestation precedes request; provider_tee verified
PASS 3 — page fail-closed flow: wrong signatureKind refused (VERIFICATION_FAILED), no answer used
PASS 4 — page fail-closed flow: absent signatureKind refused (VERIFICATION_FAILED), no answer used
PASS 5 — page fail-closed flow: Gateway refusal refused (GATEWAY_HTTP), no answer used
PASS 6 — page wiring: staged client, mock mode only, no live-DApp reference, tangerine refusal marker
PASS 7 — lockup: swoop asset in header + footer, perfected geometry, nowrap wordmark
PASS 8 — palette audit: 8 distinct hex values, all house tokens
All 8 checks passed.   (8/8, exit 0)

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

### §6 screenshot check

No §6 rendering tool/script exists in this branch — `dapp/gateway/section6/`
contains only this report and the two screenshots, and no color changed in
Turn 3, so the filed screenshots remain the renders of the shipped markup.
Both were re-read and visually checked by the Turn 3 Maker:

- `screenshot-420.png` — wordmark "UZEmarkets" on one line, Tri-Swoop in
  header and footer, eyebrow reversed out of the ink header band, black pill
  primary buttons, white secondary pills, creamsicle soft band with ink text,
  footer meta reversed out of the ink band. PASS.
- `screenshot-1280.png` — same checks at desktop width. PASS.

The one report-only axe WARN from the original gate run (link-in-text-block
on the footer wordmark link) stands as previously filed; the no-underline
footer wordmark treatment is prescribed by design system §2.
