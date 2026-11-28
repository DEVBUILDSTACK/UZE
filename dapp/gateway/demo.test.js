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

  // Attestation / ITA-token button flow.
  {
    const client = createGatewayClient({ mock: true });
    const att = await client.fetchAttestation();
    const ita = await client.fetchItaToken();
    assert.strictEqual(att.mock, true);
    assert.ok(att.attestation.attestation.includes('[MOCK]'),
      'mock attestation report must be labelled mock');
    assert.strictEqual(ita.mock, true);
    assert.ok(ita.token.includes('[MOCK]'), 'mock ITA token must be labelled mock');
    const log = client._transport.log;
    assert.ok(log.some((l) => l.includes('/attestation/report')));
    assert.ok(log.some((l) => l.includes('/attestation/ita-token')));
    ok('page attestation flow: mock report + mock ITA token returned, both labelled mock');
  }

  // Models-list button flow.
  {
    const client = createGatewayClient({ mock: true });
    const res = await client.listModels();
    assert.strictEqual(res.mock, true);
    assert.ok(Array.isArray(res.models) && res.models.length >= 1,
      'mock models list must carry at least one model');
    assert.strictEqual(res.models[0].id, 'mock/gateway-model');
    assert.ok(client._transport.log.some((l) => l.includes('/models')));
    ok('page models flow: mock catalogue returned from /models, labelled mock');
  }

  // Refusal paths for the new sections: models-list failure modes.
  // Each one must surface as a coded error — never a fabricated catalogue,
  // never a silent empty list presented as success.
  for (const [name, opts, code] of [
    ['models transport error', { modelsFailure: 'transport' }, 'TRANSPORT_ERROR'],
    ['models malformed payload', { modelsFailure: 'malformed' }, 'MALFORMED_RESPONSE'],
    ['models empty catalogue', { modelsFailure: 'empty' }, 'EMPTY_CATALOGUE']
  ]) {
    const client = createGatewayClient({ mock: true, mockOpts: opts });
    let refused = null;
    try {
      await client.listModels();
    } catch (err) { refused = err; }
    assert.ok(refused && refused.code === code, name + ' must refuse with ' + code);
    assert.ok(/mock|simulated/i.test(refused.message),
      name + ' refusal must be labelled mock/simulated: ' + refused.message);
    ok('page models refusal flow: ' + name + ' refused (' + code + '), labelled mock/simulated');
  }

  // Refusal paths for the new sections: ITA-token failure modes.
  for (const [name, opts, code] of [
    ['ITA transport error', { itaFailure: 'transport' }, 'TRANSPORT_ERROR'],
    ['ITA malformed/missing token', { itaFailure: 'malformed' }, 'MALFORMED_RESPONSE']
  ]) {
    const client = createGatewayClient({ mock: true, mockOpts: opts });
    let refused = null;
    try {
      await client.fetchItaToken();
    } catch (err) { refused = err; }
    assert.ok(refused && refused.code === code, name + ' must refuse with ' + code);
    assert.ok(/mock|simulated/i.test(refused.message),
      name + ' refusal must be labelled mock/simulated: ' + refused.message);
    assert.ok(!refused.token, name + ' refusal must not hand on a token');
    ok('page ITA refusal flow: ' + name + ' refused (' + code + '), labelled mock/simulated, no token used');
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

  // New sections: wiring + mock labelling in the page copy and script.
  assert.ok(html.includes('id="runAtt"') && html.includes('id="outAtt"'),
    'attestation section must carry its button and output');
  assert.ok(html.includes('id="runModels"') && html.includes('id="outModels"'),
    'models section must carry its button and output');
  assert.ok(html.includes('fetchAttestation') && html.includes('fetchItaToken'),
    'attestation section must fetch report + ITA token through the client');
  assert.ok(html.includes('listModels'), 'models section must list through the client');
  assert.ok(html.includes('simulated'),
    'new sections must label their values simulated in the page copy');
  ok('new sections wiring: attestation/ITA + models sections, client paths, simulated labelling in copy');

  // New sections' refusal wiring: simulate buttons in each section, the
  // mockOpts failure modes behind them, and refusals rendering into the
  // section's own output through the marker-carrying error renderer.
  for (const id of ['runAttBadTransport', 'runAttBadToken',
    'runModelsBadTransport', 'runModelsBadMalformed', 'runModelsBadEmpty']) {
    assert.ok(html.includes('id="' + id + '"'),
      'refusal simulate button #' + id + ' must exist in its section');
  }
  assert.ok(html.includes("itaFailure: 'transport'") && html.includes("itaFailure: 'malformed'"),
    'attestation section must wire its ITA transport + malformed refusals');
  assert.ok(html.includes("modelsFailure: 'transport'") &&
    html.includes("modelsFailure: 'malformed'") && html.includes("modelsFailure: 'empty'"),
    'models section must wire its transport + malformed + empty refusals');
  assert.ok(html.includes("showErr('outAtt', err)") && html.includes("showErr('outModels', err)"),
    'new-section refusals must render into their own section output via showErr');
  ok('new sections refusal wiring: 5 simulate buttons, mockOpts failure modes, showErr into outAtt/outModels');

  // Rendered output: run the page's own inline script against a stub DOM,
  // click every button, and read what the page actually renders.
  {
    const vm = require('node:vm');
    const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
    assert.strictEqual(blocks.length, 1, 'page must carry exactly one inline script block');
    const elements = {};
    function makeEl(id) {
      return {
        id, textContent: '', innerHTML: '', children: [], handlers: {},
        addEventListener(ev, fn) { this.handlers[ev] = fn; },
        appendChild(c) { this.children.push(c); this.textContent += c.textContent; }
      };
    }
    const documentStub = {
      getElementById(id) { return elements[id] || (elements[id] = makeEl(id)); },
      createElement() { return makeEl('anon'); }
    };
    const sandbox = {
      window: { UzeGateway: require('./gateway-client.js') },
      document: documentStub,
      console
    };
    vm.createContext(sandbox);
    vm.runInContext(blocks[0], sandbox);
    const tick = () => new Promise((r) => setImmediate(r));
    for (const id of ['runA', 'runB', 'runAtt', 'runModels']) {
      assert.ok(elements[id] && elements[id].handlers.click, 'button #' + id + ' must be wired');
      elements[id].handlers.click();
      await tick(); await tick();
    }
    assert.ok(elements.outA.textContent.includes('[MOCK]'),
      'Class A rendered output must be labelled mock');
    assert.ok(elements.outB.textContent.includes('provider_tee'),
      'Class B rendered output must show the verified signatureKind');
    assert.ok(elements.outAtt.textContent.includes('MOCK'),
      'attestation rendered output must carry mock labelling');
    assert.ok(elements.outAtt.textContent.includes('[MOCK] simulated Gateway attestation report'),
      'attestation rendered output must show the mock report value');
    assert.ok(elements.outAtt.textContent.includes('[MOCK] simulated ITA token'),
      'attestation rendered output must show the mock ITA token value');
    assert.ok(elements.outAtt.textContent.includes('simulated'),
      'attestation rendered output must say the values are simulated');
    assert.ok(elements.outModels.textContent.includes('MOCK'),
      'models rendered output must carry mock labelling');
    assert.ok(elements.outModels.textContent.includes('mock/gateway-model'),
      'models rendered output must list the mock model');
    assert.ok(elements.outModels.textContent.includes('simulated'),
      'models rendered output must say the catalogue is simulated');
    ok('rendered output: all sections render; new sections show mock-labelled report, ITA token, and model');
  }

  // Rendered refusals: run the page's inline script in a FRESH stub DOM,
  // click only the new sections' simulate buttons, and read what the page
  // actually renders — a REFUSED line in ink behind the tangerine marker,
  // labelled mock/simulated, in the section's own output.
  {
    const vm = require('node:vm');
    const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
    const elements = {};
    function makeEl(id) {
      return {
        id, textContent: '', innerHTML: '', children: [], handlers: {},
        addEventListener(ev, fn) { this.handlers[ev] = fn; },
        appendChild(c) { this.children.push(c); this.textContent += c.textContent; }
      };
    }
    const documentStub = {
      getElementById(id) { return elements[id] || (elements[id] = makeEl(id)); },
      createElement() { return makeEl('anon'); }
    };
    const sandbox = {
      window: { UzeGateway: require('./gateway-client.js') },
      document: documentStub,
      console
    };
    vm.createContext(sandbox);
    vm.runInContext(blocks[0], sandbox);
    const tick = () => new Promise((r) => setImmediate(r));
    const settle = async () => { for (let i = 0; i < 8; i += 1) await tick(); };

    function assertRefusalRendered(outId, code) {
      const out = elements[outId];
      assert.ok(out, 'output #' + outId + ' must exist');
      assert.ok(out.textContent.includes('REFUSED (' + code + ')'),
        '#' + outId + ' must render REFUSED (' + code + '), got: ' + out.textContent);
      assert.ok(/mock|simulated/i.test(out.textContent),
        '#' + outId + ' refusal must be labelled mock/simulated, got: ' + out.textContent);
      const marker = out.children.find((c) => c.className === 'marker');
      assert.ok(marker && marker.textContent.includes('—'),
        '#' + outId + ' refusal must carry the tangerine marker span');
      const errSpan = out.children.find((c) => c.className === 'err');
      assert.ok(errSpan && errSpan.textContent.includes('REFUSED'),
        '#' + outId + ' refusal text must render in the ink err span');
    }

    for (const [btn, outId, code] of [
      ['runAttBadTransport', 'outAtt', 'TRANSPORT_ERROR'],
      ['runAttBadToken', 'outAtt', 'MALFORMED_RESPONSE'],
      ['runModelsBadTransport', 'outModels', 'TRANSPORT_ERROR'],
      ['runModelsBadMalformed', 'outModels', 'MALFORMED_RESPONSE'],
      ['runModelsBadEmpty', 'outModels', 'EMPTY_CATALOGUE']
    ]) {
      assert.ok(elements[btn] && elements[btn].handlers.click,
        'refusal button #' + btn + ' must be wired');
      const outEl = documentStub.getElementById(outId);
      outEl.children = [];
      outEl.textContent = '';
      elements[btn].handlers.click();
      await settle();
      assertRefusalRendered(outId, code);
    }
    ok('rendered refusals: all 5 new-section failure modes render REFUSED with the tangerine marker, labelled mock/simulated, in their own section output');
  }

  console.log('\nAll ' + passed + ' checks passed.');
})().catch((err) => {
  console.error('FAIL — ' + (err && err.stack ? err.stack : err));
  process.exit(1);
});
