// MCP JSON-RPC dispatcher, shared by the stdio and Streamable HTTP
// transports. Implements the current MCP lifecycle: initialize ->
// notifications/initialized -> tools/list -> tools/call, plus ping.
// Auth rides two custom methods (uze/challenge, uze/verify) so the same
// wallet-bound handshake works identically on both transports; on HTTP
// the resulting session token is then sent as a Bearer credential.
import { CATALOG, BASE_TOOLS } from "./tools.mjs";
import { admit } from "./gate.mjs";

const PROTOCOL_VERSIONS = ["2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25"];
const DEFAULT_PROTOCOL = "2025-06-18";

export function createDispatcher(ctx) {
  const { store, auth, chronicle, handlers } = ctx;

  const toolResult = (payload, isError = false) => ({
    content: [{ type: "text", text: JSON.stringify(payload) }],
    structuredContent: payload,
    isError,
  });

  async function toolsCall(params, conn) {
    const name = params?.name;
    const args = params?.arguments || {};
    const token = conn.getToken();
    const session = auth.session(token);
    if (!session) {
      chronicle.append("tool.refused", { principal: null, tool: name || null, reason: "unauthenticated", detail: { note: "no live session (missing, expired, or revoked)" } });
      return { error: { code: -32003, message: "unauthenticated: no live session (sign in with uze/challenge + uze/verify, or the session was revoked)" } };
    }
    const gate = admit(ctx, session, name, args);
    if (!gate.ok) {
      chronicle.append("tool.refused", { principal: session.wallet, sessionId: token.slice(0, 8), tool: name, reason: gate.reason, detail: { message: gate.message } });
      return { result: toolResult({ refused: true, tool: name, reason: gate.reason, message: gate.message }, true) };
    }
    const out = await handlers[name](session, args);
    if (out.refusal) {
      chronicle.append("tool.refused", { principal: session.wallet, sessionId: token.slice(0, 8), tool: name, reason: out.refusal.reason, detail: { message: out.refusal.message } });
      return { result: toolResult({ refused: true, tool: name, reason: out.refusal.reason, message: out.refusal.message }, true) };
    }
    chronicle.append("tool.executed", { principal: session.wallet, sessionId: token.slice(0, 8), tool: name, meter: gate.price, detail: out.detail || {} });
    return { result: toolResult(out.result) };
  }

  // Returns a JSON-RPC response object, or null for notifications.
  async function handle(msg, conn) {
    if (!msg || msg.jsonrpc !== "2.0" || !msg.method) return null;
    const isNotification = msg.id === undefined;
    const reply = (result) => ({ jsonrpc: "2.0", id: msg.id, result });
    const fail = (code, message) => ({ jsonrpc: "2.0", id: msg.id, error: { code, message } });
    try {
      switch (msg.method) {
        case "initialize": {
          const want = msg.params?.protocolVersion;
          return reply({
            protocolVersion: PROTOCOL_VERSIONS.includes(want) ? want : DEFAULT_PROTOCOL,
            capabilities: { tools: {} },
            serverInfo: { name: "uze-instant-mcp", version: "0.1.0" },
            instructions: "UZE Instant MCP (M2 local build). Authenticate with uze/challenge + uze/verify (ed25519 signature over the server nonce). Settlement tools: available M3.",
          });
        }
        case "ping":
          return reply({});
        case "tools/list":
          return reply({ tools: BASE_TOOLS.map((name) => ({ name, description: CATALOG[name].description, inputSchema: CATALOG[name].inputSchema })) });
        case "tools/call": {
          const out = await toolsCall(msg.params || {}, conn);
          return out.error ? fail(out.error.code, out.error.message) : reply(out.result);
        }
        case "uze/challenge": {
          const out = auth.challenge(msg.params?.wallet);
          return out.error ? fail(-32010, out.message) : reply(out);
        }
        case "uze/verify": {
          const out = auth.verify(msg.params?.wallet, msg.params?.signature, store);
          if (out.error) return fail(-32011, out.message);
          conn.setToken(out.sessionToken);
          return reply(out);
        }
        default:
          return isNotification ? null : fail(-32601, `method not found: ${msg.method}`);
      }
    } catch (e) {
      return isNotification ? null : fail(-32603, `internal error: ${e.message}`);
    }
  }

  return { handle };
}
