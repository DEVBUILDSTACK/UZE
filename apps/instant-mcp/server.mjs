// UZE Instant MCP — merged program M2 (Scope 3 Phase 1): core MCP +
// Instance tier. Zero-dependency Node, house style of apps/dev-library.
// Transports: Streamable HTTP (POST /mcp) and stdio (--stdio).
// Provisioning is a LOCAL MOCK (lib/provisioner.mjs) — real NEAR AI
// Cloud provisioning is blocked on credits (M0-B). Nothing here makes
// an external network call, moves funds, or creates a public endpoint.
import http from "node:http";
import path from "node:path";
import readline from "node:readline";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";
import { Chronicle } from "./lib/chronicle.mjs";
import { Store } from "./lib/store.mjs";
import { Auth } from "./lib/auth.mjs";
import { MockProvisioner } from "./lib/provisioner.mjs";
import { makeHandlers } from "./lib/tools.mjs";
import { createTalentClient } from "./lib/talent-client.mjs";
import { createDispatcher } from "./lib/mcp.mjs";
import { base58Decode } from "./lib/base58.mjs";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = process.env.INSTANT_MCP_DATA_DIR || path.join(ROOT, "data");
const PORT = Number(process.env.PORT || 8741);
const ADMIN_TOKEN = process.env.INSTANT_MCP_ADMIN_TOKEN || "";

export function buildContext() {
  const chronicle = new Chronicle(path.join(DATA_DIR, "chronicle.jsonl"));
  const store = new Store(path.join(DATA_DIR, "state.json"));
  const auth = new Auth(chronicle);
  const provisioner = new MockProvisioner(store);
  const talent = createTalentClient();
  const handlers = makeHandlers({ store, provisioner, chronicle, talent });
  return { chronicle, store, auth, provisioner, handlers, talent };
}

const ctx = buildContext();
const dispatcher = createDispatcher(ctx);

const send = (res, code, obj, headers = {}) => {
  res.writeHead(code, { "content-type": "application/json", ...headers });
  res.end(JSON.stringify(obj));
};
const body = (req) => new Promise((resolve) => {
  let s = ""; req.on("data", (c) => (s += c)); req.on("end", () => { try { resolve(JSON.parse(s || "{}")); } catch { resolve({}); } });
});
const bearer = (req) => {
  const h = req.headers.authorization || "";
  return h.startsWith("Bearer ") ? h.slice(7) : null;
};
const isAdmin = (req) => ADMIN_TOKEN && req.headers["x-admin-token"] === ADMIN_TOKEN;

export function createServer() {
  return http.createServer(async (req, res) => {
    const url = new URL(req.url, "http://localhost");
    try {
      if (req.method === "GET" && url.pathname === "/health") {
        return send(res, 200, { ok: true, server: "uze-instant-mcp", phase: "M2 local build", provisioner: "LOCAL MOCK (M0-B pending)" });
      }

      // REST mirrors of the auth handshake (the JSON-RPC methods
      // uze/challenge and uze/verify on /mcp do the same thing).
      if (req.method === "POST" && url.pathname === "/auth/challenge") {
        const b = await body(req);
        const out = ctx.auth.challenge(b.wallet);
        return send(res, out.error ? 400 : 200, out);
      }
      if (req.method === "POST" && url.pathname === "/auth/verify") {
        const b = await body(req);
        const out = ctx.auth.verify(b.wallet, b.signature, ctx.store);
        return send(res, out.error ? 401 : 200, out);
      }

      // Admin path: the user's re-authenticated act — sets the
      // pre-authorization limits (layer a) and fires the revoke cascade.
      if (url.pathname.startsWith("/admin/")) {
        if (!ADMIN_TOKEN) return send(res, 503, { error: "admin_disabled", message: "INSTANT_MCP_ADMIN_TOKEN is not set" });
        if (!isAdmin(req)) return send(res, 401, { error: "unauthorized" });
        if (req.method === "POST" && url.pathname === "/admin/principals") {
          const b = await body(req);
          let pub = null;
          try { pub = base58Decode(b.wallet || ""); } catch { /* handled below */ }
          if (!pub || pub.length !== 32) return send(res, 400, { error: "invalid_wallet" });
          if (!["instance", "markets"].includes(b.tier)) return send(res, 400, { error: "invalid_tier" });
          const rec = ctx.store.upsertPrincipal({ wallet: b.wallet, tier: b.tier, limits: b.limits || {}, revoked: false });
          ctx.chronicle.append("principal.registered", { principal: b.wallet, detail: { tier: b.tier, limits: rec.limits } });
          return send(res, 200, { ok: true, principal: rec });
        }
        if (req.method === "POST" && url.pathname === "/admin/revoke") {
          const b = await body(req);
          const prev = ctx.store.getPrincipal(b.wallet);
          if (!prev) return send(res, 404, { error: "unknown_principal" });
          ctx.store.upsertPrincipal({ ...prev, revoked: true });
          const killed = ctx.auth.revokeSessions(b.wallet);
          ctx.chronicle.append("principal.revoked", { principal: b.wallet, detail: { sessionsKilled: killed } });
          return send(res, 200, { ok: true, wallet: b.wallet, sessionsKilled: killed });
        }
        if (req.method === "GET" && url.pathname === "/admin/principals") {
          return send(res, 200, { principals: [...ctx.store.principals.values()] });
        }
        if (req.method === "GET" && url.pathname === "/admin/chronicle") {
          const w = url.searchParams.get("principal");
          return send(res, 200, { events: w ? ctx.chronicle.forPrincipal(w) : ctx.chronicle.all() });
        }
        return send(res, 404, { error: "not_found" });
      }

      // Streamable HTTP transport.
      if (url.pathname === "/mcp") {
        if (req.method === "GET") return send(res, 405, { error: "method_not_allowed", message: "this server does not offer a standalone GET stream" });
        if (req.method !== "POST") return send(res, 405, { error: "method_not_allowed" });
        const payload = await body(req);
        const msgs = Array.isArray(payload) ? payload : [payload];
        const conn = { getToken: () => bearer(req), setToken: () => {} };
        const responses = [];
        for (const m of msgs) {
          const r = await dispatcher.handle(m, conn);
          if (r) responses.push(r);
        }
        if (responses.length === 0) { res.writeHead(202); return res.end(); }
        const headers = {};
        if (msgs.some((m) => m.method === "initialize")) headers["mcp-session-id"] = crypto.randomBytes(16).toString("hex");
        return send(res, 200, Array.isArray(payload) ? responses : responses[0], headers);
      }

      return send(res, 404, { error: "not_found" });
    } catch (e) {
      return send(res, 500, { error: "internal", message: e.message });
    }
  });
}

// stdio transport: newline-delimited JSON-RPC on stdin/stdout. The
// connection holds the session token set by uze/verify.
async function runStdio() {
  let token = null;
  const conn = { getToken: () => token, setToken: (t) => { token = t; } };
  const rl = readline.createInterface({ input: process.stdin });
  for await (const line of rl) {
    if (!line.trim()) continue;
    let msg;
    try { msg = JSON.parse(line); } catch { continue; }
    const out = await dispatcher.handle(msg, conn);
    if (out) process.stdout.write(JSON.stringify(out) + "\n");
  }
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  if (process.argv.includes("--stdio")) {
    runStdio();
  } else {
    createServer().listen(PORT, () => {
      console.error(`uze-instant-mcp: HTTP on :${PORT} (POST /mcp, /auth/*, /admin/*) — LOCAL MOCK provisioner`);
    });
  }
}
