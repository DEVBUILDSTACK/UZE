/*
 * demo.test.js — harness test for the mock-mode integration demo (demo.html).
 * Plain Node, no framework, no network. Drives the exact flows the page's
 * buttons run, against gateway-client.js in mock mode, and statically
 * asserts the page's wiring and design-law bounds.
 *
 * Run: node demo.test.js
 * Exits 0 when all checks pass, 1 otherwise.
 */
'use strict';

const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const { createGatewayClient, REQUIRED_SIGNATURE_KIND } = require('./gateway-client.js');

const MODEL = 'mock/gateway-model';
const MESSAGES = [{ role: 'user', content: 'Reply with the single word: ready' }];

let passed = 0;
function ok(name) {
  passed += 1;
  console.log('PASS ' + passed + ' — ' + name);
}

(async () => {
  // --- The flows the page runs ---

  // Class A button flow.
  {
    const client = createGatewayClient({ mock: true });
    const res = await client.chatCompletion({ model: MODEL, messages: MESSAGES, maxTokens: 8 });
    assert.strictEqual(res.mock, true);
    assert.ok(res.content.includes('[MOCK]'));
    ok('page Class A flow: mock completion returned, labelled mock');
  }

  // Class B button flow, with attestation-before-request ordering.
  {
    const client = createGatewayClient({ mock: true });
    const res = await client.teeCompletion({ model: MODEL, messages: MESSAGES, maxTokens: 8 });
    assert.strictEqual(res.signatureKind, REQUIRED_SIGNATURE_KIND);
    assert.ok(res.attestation);
    const log = client._transport.log;
    assert.ok(log.findIndex((l) => l.includes('/attestation/report')) <
              log.findIndex((l) => l.includes('/chat/completions')));
    ok('page Class B flow: attestation precedes request; provider_tee verified');
  }

  // Fail-closed buttons: all three refusals surface as errors.
  for (const [name, opts, code] of [
    ['wrong signatureKind', { signatureKind: 'unverified_source' }, 'VERIFICATION_FAILED'],
    ['absent signatureKind', { signatureKind: null }, 'VERIFICATION_FAILED'],
    ['Gateway refusal', { refuseClassB: true }, 'GATEWAY_HTTP']
  ]) {
    const client = createGatewayClient({ mock: true, mockOpts: opts });
    let refused = null;
    try {
      await client.teeCompletion({ model: MODEL, messages: MESSAGES, maxTokens: 8 });
    } catch (err) { refused = err; }
    assert.ok(refused && refused.code === code, name + ' must refuse with ' + code);
    ok('page fail-closed flow: ' + name + ' refused (' + code + '), no answer used');
  }

  // --- The page itself ---

  const html = fs.readFileSync(path.join(__dirname, 'demo.html'), 'utf8');

  assert.ok(html.includes('<script src="./gateway-client.js"></script>'),
    'page must load the staged client module');
  assert.ok(html.includes('mock: true'), 'page must construct the client in mock mode');
  assert.ok(!/createGatewayClient\(\{\s*\}\)/.test(html),
    'page must never construct a real-mode client');
  assert.ok(!html.includes('index.html'), 'page must not reference the live DApp');
  assert.ok(html.includes("marker.className = 'marker'"),
    'refusals must render the dash through the tangerine marker, the rest in ink');
  ok('page wiring: staged client, mock mode only, no live-DApp reference, tangerine refusal marker');

  // Lockup: real swoop asset in header and footer, perfected geometry.
  const swoops = html.match(/\.\.\/swoop\.png/g) || [];
  assert.ok(swoops.length >= 2, 'Tri-Swoop lockup must appear in header and footer');
  assert.ok(html.includes('height:.55em;left:-.437em;top:-.185em'),
    'lockup must carry the perfected geometry');
  assert.ok(html.includes('white-space:nowrap'), 'wordmark must never wrap');
  ok('lockup: swoop asset in header + footer, perfected geometry, nowrap wordmark');

  // Palette audit: every hex in the page is a token of record.
  const TOKENS = new Set(['#1a1a1a', '#f5f2ee', '#ff6b00', '#fdeee2',
    '#ddd5c9', '#6b655e', '#b8b0a4', '#ffffff']);
  const hexes = html.match(/#[0-9a-fA-F]{3,8}\b/g) || [];
  const bad = [...new Set(hexes.map((h) => h.toLowerCase()))].filter((h) => !TOKENS.has(h));
  assert.deepStrictEqual(bad, [], 'off-palette hexes found: ' + bad.join(', '));
  ok('palette audit: ' + new Set(hexes.map((h) => h.toLowerCase())).size +
     ' distinct hex values, all house tokens');

  console.log('\nAll ' + passed + ' checks passed.');
})().catch((err) => {
  console.error('FAIL — ' + (err && err.stack ? err.stack : err));
  process.exit(1);
});
