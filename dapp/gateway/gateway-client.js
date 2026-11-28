/*
 * gateway-client.js — the DApp's Gateway client module.
 *
 * Implements the routing design of record (DFI Launch Team, Lead — Front End,
 * Phase 2: "the DApp's instance through the NEAR Gateway"):
 *
 *   ONE DOOR ONLY. Every intelligence call leaves through the NEAR AI Cloud
 *   Gateway at https://cloud-api.near.ai/v1. There is no second route and no
 *   fallback. Direct endpoints are never integrated (support ends
 *   December 6, 2026); the GATEWAY_BASE constant below is the only base URL
 *   this module will ever address, so the Dec 6 zero-Direct audit is a grep.
 *
 *   CLASS A — ordinary intelligence calls. Gateway chat completions,
 *   non-E2EE, for work that carries no TEE requirement.
 *
 *   CLASS B — TEE-classified sessions (E2EE v3). Before the request, the
 *   model's attestation is fetched from the Gateway. The reply is used ONLY
 *   after its receipt verifies with signatureKind: provider_tee. A reply
 *   that arrives but does not verify is refused and filed as a failed
 *   verification — never consumed, never papered over.
 *
 *   FAIL-CLOSED. If the Gateway refuses a Class B request (no compatible
 *   NEAR-serving path), or any call fails, the error surfaces honestly to
 *   the caller. This module never fabricates an answer and never reroutes
 *   through a different protocol.
 *
 *   KEY HANDLING. The API key is read from the injected config, or from the
 *   NEARAI_API_KEY environment variable under Node. It is never hardcoded,
 *   never stored by this module, and never logged.
 *
 *   PRODUCTION NOTE. Field-level E2EE v3 encryption on the wire (Ed25519
 *   suite 0x02 — X25519 · HKDF-SHA256 · XChaCha20-Poly1305, per-field AAD
 *   binding) is performed by the official NEAR AI inference SDK in the
 *   production integration — the same SDK the staged initiation script
 *   (~/workspace/vps-build/gateway/e2ee_roundtrip_test.py) exercises. This
 *   dependency-free module enforces the routing and verification discipline
 *   around that path: attestation before the request, the provider_tee
 *   gate before any answer is used, fail-closed throughout.
 *
 *   MOCK MODE. With { mock: true } the module simulates the Gateway with
 *   clearly-labelled mock responses ([MOCK] in every payload), for offline
 *   development. No network call is made in mock mode. Mock mode exists
 *   because no valid key is in hand yet; it is a development stand-in,
 *   never a production path, and its outputs are labelled so a mock answer
 *   can never be mistaken for a Gateway answer.
 *
 * Dependency-free. Runs in the browser (window.UzeGateway) and under Node
 * (module.exports). No network calls are made at load time.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.UzeGateway = api;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var GATEWAY_BASE = 'https://cloud-api.near.ai/v1';
  var REQUIRED_SIGNATURE_KIND = 'provider_tee';

  /* ---------------- errors ---------------- */

  function GatewayError(code, message, status) {
    var err = new Error(message);
    err.name = 'GatewayError';
    err.code = code;
    if (status !== undefined) err.status = status;
    return err;
  }

  function noKeyError() {
    return GatewayError(
      'NO_KEY',
      'No Gateway API key available. The key is read from the injected ' +
        'config or the NEARAI_API_KEY environment variable; it is entered ' +
        'by the principal via the secure route and is never hardcoded.'
    );
  }

  function verificationError(detail) {
    return GatewayError(
      'VERIFICATION_FAILED',
      'Class B reply refused: verification failed (' + detail + '). The ' +
        'answer was NOT used. A reply is consumed only when its receipt ' +
        'carries signatureKind: ' + REQUIRED_SIGNATURE_KIND + '.'
    );
  }

  /* ---------------- mock transport ----------------
   * Simulates the Gateway endpoints this module uses. Every payload is
   * labelled mock. mockOpts.signatureKind controls the signatureKind the
   * mock Class B receipt carries (default 'provider_tee'); set it to
   * anything else — or null to omit it — to exercise the fail-closed path.
   * mockOpts.refuseClassB simulates the Gateway refusing a Class B request
   * (no compatible NEAR-serving path). mockOpts.modelsFailure simulates a
   * broken /models answer: 'transport' (network failure), 'malformed'
   * (payload whose data is not an array), or 'empty' (an empty catalogue).
   * mockOpts.itaFailure simulates a broken ITA-token answer: 'transport'
   * (network failure) or 'malformed' (a payload carrying no token). The
   * mock records a request log so tests can assert ordering (attestation
   * before the completion call).
   */
  function createMockTransport(mockOpts) {
    var opts = mockOpts || {};
    var signatureKind = Object.prototype.hasOwnProperty.call(opts, 'signatureKind')
      ? opts.signatureKind
      : REQUIRED_SIGNATURE_KIND;
    var log = [];

    function jsonResponse(status, obj) {
      return {
        ok: status >= 200 && status < 300,
        status: status,
        json: function () { return Promise.resolve(obj); },
        text: function () { return Promise.resolve(JSON.stringify(obj)); }
      };
    }

    function transport(url, init) {
      var method = (init && init.method) || 'GET';
      log.push(method + ' ' + url);

      if (url === GATEWAY_BASE + '/models') {
        if (opts.modelsFailure === 'transport') {
          return Promise.reject(new Error(
            'simulated network failure — the /models request never arrived'));
        }
        if (opts.modelsFailure === 'malformed') {
          return Promise.resolve(jsonResponse(200, {
            object: 'list',
            mock: true,
            data: { unexpected: 'shape — not a model array' }
          }));
        }
        if (opts.modelsFailure === 'empty') {
          return Promise.resolve(jsonResponse(200, {
            object: 'list',
            mock: true,
            data: []
          }));
        }
        return Promise.resolve(jsonResponse(200, {
          object: 'list',
          mock: true,
          data: [{ id: 'mock/gateway-model', object: 'model', mock: true }]
        }));
      }

      if (url === GATEWAY_BASE + '/attestation/report') {
        return Promise.resolve(jsonResponse(200, {
          mock: true,
          attestation: '[MOCK] simulated Gateway attestation report — ' +
            'not a hardware attestation.'
        }));
      }

      if (url === GATEWAY_BASE + '/attestation/ita-token') {
        if (opts.itaFailure === 'transport') {
          return Promise.reject(new Error(
            'simulated network failure — the ITA-token request never arrived'));
        }
        if (opts.itaFailure === 'malformed') {
          return Promise.resolve(jsonResponse(200, {
            mock: true
            /* no token field — a malformed answer */
          }));
        }
        return Promise.resolve(jsonResponse(200, {
          mock: true,
          token: '[MOCK] simulated ITA token'
        }));
      }

      if (url === GATEWAY_BASE + '/chat/completions') {
        var body = {};
        try { body = JSON.parse(init.body || '{}'); } catch (e) { body = {}; }
        var isClassB = init.headers &&
          init.headers['X-Encryption-Version'] === '3';

        if (isClassB && opts.refuseClassB) {
          return Promise.resolve(jsonResponse(409, {
            mock: true,
            error: {
              message: '[MOCK] Gateway refusal: no compatible NEAR-serving ' +
                'path for this E2EE request.'
            }
          }));
        }

        var completion = {
          id: 'mock-completion',
          object: 'chat.completion',
          mock: true,
          model: body.model || 'mock/gateway-model',
          choices: [{
            index: 0,
            message: {
              role: 'assistant',
              content: '[MOCK] Simulated Gateway completion — no network ' +
                'call was made and no real model answered.'
            },
            finish_reason: 'stop'
          }]
        };
        if (isClassB && signatureKind !== null && signatureKind !== undefined) {
          completion.signatureKind = signatureKind;
        }
        return Promise.resolve(jsonResponse(200, completion));
      }

      return Promise.resolve(jsonResponse(404, {
        mock: true,
        error: { message: '[MOCK] Unknown mock endpoint: ' + url }
      }));
    }

    transport.log = log;
    return transport;
  }

  /* ---------------- client ---------------- */

  function resolveKey(config) {
    if (config.apiKey) return config.apiKey;
    if (typeof process !== 'undefined' && process.env &&
        process.env.NEARAI_API_KEY) {
      return process.env.NEARAI_API_KEY;
    }
    return null;
  }

  function resolveFetch(config) {
    if (config.fetchImpl) return config.fetchImpl;
    if (typeof fetch !== 'undefined') return fetch;
    return null;
  }

  /**
   * createGatewayClient({
   *   apiKey,          // injected key (or NEARAI_API_KEY env under Node)
   *   fetchImpl,       // injected fetch (defaults to global fetch)
   *   mock,            // true → simulated Gateway, no network calls
   *   mockOpts         // { signatureKind, refuseClassB, modelsFailure,
                        //   itaFailure } — mock mode only
   * })
   */
  function createGatewayClient(config) {
    config = config || {};
    var mock = !!config.mock;
    var transport = mock ? createMockTransport(config.mockOpts) : resolveFetch(config);
    var key = mock ? (config.apiKey || 'mock-key-not-a-real-key') : resolveKey(config);

    function requireKey() {
      if (!key) throw noKeyError();
    }

    function requireTransport() {
      if (!transport) {
        throw GatewayError(
          'NO_TRANSPORT',
          'No fetch implementation available. Inject fetchImpl in the ' +
            'client config, or run where a global fetch exists.'
        );
      }
    }

    function request(path, init) {
      requireTransport();
      var headers = Object.assign(
        { 'Content-Type': 'application/json' },
        init && init.headers ? init.headers : {}
      );
      if (!mock) headers['Authorization'] = 'Bearer ' + key;
      else headers['Authorization'] = 'Bearer [MOCK]';
      return transport(GATEWAY_BASE + path, Object.assign({}, init, { headers: headers }))
        .then(null, function (err) {
          /* A transport/network failure is a refusal, not a TypeError the
           * caller has to decode: normalize it, fail-closed. */
          throw GatewayError(
            'TRANSPORT_ERROR',
            (mock ? '[MOCK] simulated transport failure: '
                  : 'Gateway transport failure: ') +
              (err && err.message ? err.message : 'network error'));
        })
        .then(function (res) {
          return res.json().catch(function () { return {}; }).then(function (body) {
            if (!res.ok) {
              var msg = (body && body.error && body.error.message) ||
                ('Gateway request failed with HTTP ' + res.status);
              throw GatewayError('GATEWAY_HTTP', msg, res.status);
            }
            return body;
          });
        });
    }

    /* Class A — ordinary Gateway completion (non-E2EE). */
    function chatCompletion(params) {
      params = params || {};
      if (!mock) requireKey();
      if (!params.model) {
        return Promise.reject(GatewayError('BAD_REQUEST',
          'chatCompletion requires a Gateway model ID (from GET /v1/models).'));
      }
      return request('/chat/completions', {
        method: 'POST',
        body: JSON.stringify({
          model: params.model,
          messages: params.messages || [],
          max_tokens: params.maxTokens,
          temperature: params.temperature,
          stream: false
        })
      }).then(function (body) {
        return {
          content: body.choices && body.choices[0] && body.choices[0].message
            ? body.choices[0].message.content : '',
          model: body.model,
          mock: !!body.mock,
          raw: body
        };
      });
    }

    /* Attestation fetch — the Class B precondition. */
    function fetchAttestation() {
      if (!mock) requireKey();
      return request('/attestation/report', { method: 'GET' })
        .then(function (body) {
          return { attestation: body, mock: !!body.mock };
        });
    }

    /* Models list — the Gateway's model catalogue (GET /v1/models).
     * Fail-closed: a payload whose data is not an array of identified
     * models is malformed and refused, and an empty catalogue is refused
     * rather than presented as a working list — a caller must never build
     * on a catalogue that is not there. */
    function listModels() {
      if (!mock) requireKey();
      return request('/models', { method: 'GET' })
        .then(function (body) {
          var label = mock ? '[MOCK] simulated models response' : 'Gateway models response';
          if (!Array.isArray(body.data) ||
              body.data.some(function (m) { return !m || typeof m.id !== 'string' || !m.id; })) {
            throw GatewayError('MALFORMED_RESPONSE',
              label + ' was malformed: expected a data array of models ' +
              'with IDs. Refused — no catalogue was used.');
          }
          if (body.data.length === 0) {
            throw GatewayError('EMPTY_CATALOGUE',
              label + ' carried an empty catalogue: no models were ' +
              'returned. Refused — an empty list is not a working catalogue.');
          }
          return { models: body.data, mock: !!body.mock, raw: body };
        });
    }

    /* ITA token fetch — the attestation companion credential.
     * Fail-closed: a payload with no usable token string is malformed
     * and refused — a missing token is never handed on as a credential. */
    function fetchItaToken() {
      if (!mock) requireKey();
      return request('/attestation/ita-token', { method: 'GET' })
        .then(function (body) {
          if (typeof body.token !== 'string' || !body.token) {
            throw GatewayError('MALFORMED_RESPONSE',
              (mock ? '[MOCK] simulated ITA-token response' : 'Gateway ITA-token response') +
              ' was malformed: no token was carried. Refused — no token was used.');
          }
          return { token: body.token, mock: !!body.mock, raw: body };
        });
    }

    /*
     * Class B — TEE-classified session (E2EE v3 discipline).
     * Order of operations is the design: attestation BEFORE the request;
     * signature verification BEFORE the answer is returned. Any failure —
     * attestation unavailable, Gateway refusal, missing or wrong
     * signatureKind — throws and the answer is never handed to the caller.
     */
    function teeCompletion(params) {
      params = params || {};
      if (!mock) requireKey();
      if (!params.model) {
        return Promise.reject(GatewayError('BAD_REQUEST',
          'teeCompletion requires a Gateway model ID (from GET /v1/models).'));
      }
      return fetchAttestation().then(function (att) {
        return request('/chat/completions', {
          method: 'POST',
          headers: {
            'X-Encryption-Version': '3',
            'X-Signing-Algo': 'ed25519',
            'x-no-aliasing': 'true'
          },
          body: JSON.stringify({
            model: params.model,
            messages: params.messages || [],
            max_tokens: params.maxTokens,
            stream: false,
            e2ee: true
          })
        }).then(function (body) {
          var kind = body.signatureKind || body.signature_kind || null;
          if (kind !== REQUIRED_SIGNATURE_KIND) {
            throw verificationError(
              'receipt signatureKind is ' +
                (kind === null ? 'absent' : JSON.stringify(kind)) +
                ', required ' + JSON.stringify(REQUIRED_SIGNATURE_KIND));
          }
          return {
            content: body.choices && body.choices[0] && body.choices[0].message
              ? body.choices[0].message.content : '',
            model: body.model,
            signatureKind: kind,
            attestation: att.attestation,
            mock: !!body.mock,
            raw: body
          };
        });
      });
    }

    return {
      base: GATEWAY_BASE,
      isMock: mock,
      chatCompletion: chatCompletion,
      teeCompletion: teeCompletion,
      fetchAttestation: fetchAttestation,
      listModels: listModels,
      fetchItaToken: fetchItaToken,
      _transport: transport // exposed for tests (mock request log)
    };
  }

  return {
    GATEWAY_BASE: GATEWAY_BASE,
    REQUIRED_SIGNATURE_KIND: REQUIRED_SIGNATURE_KIND,
    createGatewayClient: createGatewayClient
  };
});
