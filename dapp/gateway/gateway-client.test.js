/*
 * gateway-client.test.js — plain Node self-test for gateway-client.js.
 * No framework, no network: every Gateway interaction runs in mock mode.
 *
 * Run: node gateway-client.test.js
 * Exits 0 when all checks pass, 1 otherwise.
 */
'use strict';

const assert = require('node:assert');
const { createGatewayClient, GATEWAY_BASE, REQUIRED_SIGNATURE_KIND } =
  require('./gateway-client.js');

const MODEL = 'mock/gateway-model';
const MESSAGES = [{ role: 'user', content: 'Reply with the single word: ready' }];

let passed = 0;
function ok(name) {
  passed += 1;
  console.log('PASS ' + passed + ' — ' + name);
}

(async () => {
  // The one door: the module's base is the Gateway, nothing else.
  assert.strictEqual(GATEWAY_BASE, 'https://cloud-api.near.ai/v1');
  ok('one door only: base is https://cloud-api.near.ai/v1');

  // 1. Mock Class A completion.
  {
    const client = createGatewayClient({ mock: true });
    const res = await client.chatCompletion({ model: MODEL, messages: MESSAGES, maxTokens: 8 });
    assert.ok(res.content.includes('[MOCK]'), 'Class A content must be labelled mock');
    assert.strictEqual(res.mock, true);
    ok('mock Class A completion returns a clearly-labelled mock answer');
  }

  // 2. Mock Class B: attestation fetched BEFORE the request, reply verified.
  {
    const client = createGatewayClient({ mock: true });
    const res = await client.teeCompletion({ model: MODEL, messages: MESSAGES, maxTokens: 8 });
    assert.strictEqual(res.signatureKind, REQUIRED_SIGNATURE_KIND);
    assert.ok(res.content.includes('[MOCK]'), 'Class B content must be labelled mock');
    assert.ok(res.attestation, 'attestation must be carried with the result');
    const log = client._transport.log;
    const attIdx = log.findIndex((l) => l.includes('/attestation/report'));
    const chatIdx = log.findIndex((l) => l.includes('/chat/completions'));
    assert.ok(attIdx !== -1 && chatIdx !== -1 && attIdx < chatIdx,
      'attestation must be fetched before the completion call');
    ok('mock Class B: attestation precedes the request; provider_tee reply verified and returned');
  }

  // 3a. Fail-closed: a Class B reply lacking provider_tee is refused.
  {
    const client = createGatewayClient({
      mock: true,
      mockOpts: { signatureKind: 'unverified_source' }
    });
    let refused = null;
    try {
      await client.teeCompletion({ model: MODEL, messages: MESSAGES, maxTokens: 8 });
    } catch (err) {
      refused = err;
    }
    assert.ok(refused, 'a reply without provider_tee must be refused, not returned');
    assert.strictEqual(refused.code, 'VERIFICATION_FAILED');
    ok('fail-closed: reply with signatureKind != provider_tee is refused, answer never used');
  }

  // 3b. Fail-closed: a Class B reply with NO signatureKind is refused.
  {
    const client = createGatewayClient({
      mock: true,
      mockOpts: { signatureKind: null }
    });
    let refused = null;
    try {
      await client.teeCompletion({ model: MODEL, messages: MESSAGES, maxTokens: 8 });
    } catch (err) {
      refused = err;
    }
    assert.ok(refused && refused.code === 'VERIFICATION_FAILED',
      'a reply with no signatureKind must be refused');
    ok('fail-closed: reply with signatureKind absent is refused');
  }

  // 3c. Fail-closed: a Gateway refusal of a Class B request surfaces honestly.
  {
    const client = createGatewayClient({
      mock: true,
      mockOpts: { refuseClassB: true }
    });
    let refused = null;
    try {
      await client.teeCompletion({ model: MODEL, messages: MESSAGES, maxTokens: 8 });
    } catch (err) {
      refused = err;
    }
    assert.ok(refused && refused.code === 'GATEWAY_HTTP' && refused.status === 409,
      'a Gateway refusal must surface as an error, never a fabricated answer');
    ok('fail-closed: Gateway refusal surfaces as an honest error (HTTP 409), no fallback fiction');
  }

  // 4. No-key error: a real (non-mock) client with no key refuses cleanly.
  {
    const saved = process.env.NEARAI_API_KEY;
    delete process.env.NEARAI_API_KEY;
    try {
      const client = createGatewayClient({});
      let refused = null;
      try {
        await client.chatCompletion({ model: MODEL, messages: MESSAGES });
      } catch (err) {
        refused = err;
      }
      assert.ok(refused && refused.code === 'NO_KEY',
        'a keyless real-mode call must fail with the NO_KEY error');
    } finally {
      if (saved !== undefined) process.env.NEARAI_API_KEY = saved;
    }
    ok('no-key: real-mode call without a key fails with NO_KEY, naming the unblock');
  }

  console.log('\nAll ' + passed + ' checks passed.');
})().catch((err) => {
  console.error('FAIL — ' + (err && err.stack ? err.stack : err));
  process.exit(1);
});
