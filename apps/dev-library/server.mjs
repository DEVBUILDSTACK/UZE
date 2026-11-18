// UZE Dev Library — the reading room. Phase 1 (reading room foundation).
// App-level gate on a dedicated subdomain (dev.uzemarkets.com at go-live):
// the server checks the allowlist before anything is served. Source code
// never lives here — GitHub is the source gate; this room holds
// descriptions and mocks only. Zero-dependency Node, same house style
// as the AEInfo demos. Data layer: lib/store.mjs (JSON today; the
// talent schema migration 001 in services/compose is the core-side home).
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { load, save, chronicle } from "./lib/store.mjs";
import { findDeveloper, requestCode, verifyCode, signSession, readSession, visibleMocks } from "./lib/gate.mjs";
import { drainComms } from "./lib/mailer.mjs";
import { applyWebhook, webhookConfigured } from "./lib/webhook.mjs";
import * as life from "./lib/lifecycle.mjs";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const PORT = process.env.PORT || 8734;
const MASTER = process.env.LIBRARY_MASTER_TOKEN || "";
const INDEX = fs.readFileSync(path.join(ROOT, "public", "index.html"), "utf8");

const send = (res, code, obj, headers = {}) => {
  res.writeHead(code, { "content-type": "application/json", ...headers });
  res.end(JSON.stringify(obj));
};
const body = (req) => new Promise((resolve) => {
  let s = ""; req.on("data", (c) => (s += c)); req.on("end", () => { try { resolve(JSON.parse(s || "{}")); } catch { resolve({}); } });
});
const rawBody = (req) => new Promise((resolve) => {
  let s = ""; req.on("data", (c) => (s += c)); req.on("end", () => resolve(s));
});
const sessionOf = (req) => {
  const cookie = req.headers.cookie || "";
  const m = cookie.match(/dl_session=([^;]+)/);
  return m ? readSession(decodeURIComponent(m[1])) : null;
};
const isMaster = (req) => MASTER && req.headers["x-master-token"] === MASTER;
const publicDev = (d) => d && ({ name: d.name, email: d.email, track: d.track || "EITHER", stage: d.stage,
  expertise: d.expertise, readingRoom: d.readingRoom.active,
  source: d.source.filter((s) => !s.revokedAt).map((s) => s.repo) });

// DB mode (DATABASE_URL set): the talent data layer is the durable
// record — hydrate the working set from it before serving.
let flushFn = null;
if (process.env.DATABASE_URL || process.env.POSTGRES_URL) {
  // Serverless filesystems are read-only but for /tmp: seed the
  // working set there from the bundled data/ on first cold start.
  if (process.env.LIBRARY_DATA) {
    fs.mkdirSync(process.env.LIBRARY_DATA, { recursive: true });
    if (!fs.existsSync(path.join(process.env.LIBRARY_DATA, "developers.json"))) {
      for (const f of fs.readdirSync(path.join(ROOT, "data"))) {
        fs.copyFileSync(path.join(ROOT, "data", f), path.join(process.env.LIBRARY_DATA, f));
      }
    }
  }
  const pgStore = await import("./lib/store-pg.mjs");
  await pgStore.initPgStore();
  flushFn = pgStore.flushPg;
  console.log("dev-library: DB mode (Postgres data layer)");
}

const handleRequest = async (req, res) => {
  const url = new URL(req.url, "http://x");
  const p = url.pathname;
  try {
    if (p === "/" && req.method === "GET") { res.writeHead(200, { "content-type": "text/html" }); return res.end(INDEX); }

    // --- email imagery (public by design: mail clients load these
    // without a session). Hosted on our own domain per the design
    // spec — hero.jpg is the static 1200x400 (2x) hero, hero.gif the
    // animated version whose first frame is that same design. ---
    if ((p === "/hero.jpg" || p === "/hero.gif") && req.method === "GET") {
      const file = path.join(ROOT, "assets", p.slice(1));
      if (!fs.existsSync(file)) return send(res, 404, { error: "not found" });
      res.writeHead(200, { "content-type": p.endsWith(".gif") ? "image/gif" : "image/jpeg",
        "cache-control": "public, max-age=86400" });
      return res.end(fs.readFileSync(file));
    }

    // --- the door ---
    if (p === "/api/request-code" && req.method === "POST") {
      const { email } = await body(req);
      if (email) await requestCode(String(email)); // generic answer either way
      return send(res, 200, { ok: true });
    }
    if (p === "/api/verify" && req.method === "POST") {
      const { email, code } = await body(req);
      if (!email || !(await verifyCode(String(email), String(code)))) return send(res, 401, { error: "invalid code" });
      const token = signSession(String(email));
      return send(res, 200, { ok: true, developer: publicDev(findDeveloper(email)) },
        { "set-cookie": `dl_session=${encodeURIComponent(token)}; HttpOnly; SameSite=Lax; Path=/` });
    }
    if (p === "/api/signout" && req.method === "POST") {
      return send(res, 200, { ok: true }, { "set-cookie": "dl_session=; Max-Age=0; Path=/" });
    }
    if (p === "/api/me" && req.method === "GET") {
      const d = sessionOf(req); if (!d) return send(res, 401, { error: "no session" });
      return send(res, 200, { developer: publicDev(d) });
    }

    // --- the room (session required) ---
    if (p === "/api/catalog" && req.method === "GET") {
      const d = sessionOf(req); if (!d) return send(res, 401, { error: "no session" });
      let viewer = d;
      const asEmail = url.searchParams.get("email");
      if (asEmail && asEmail.toLowerCase() !== d.email.toLowerCase()) {
        if (!isMaster(req)) return send(res, 403, { error: "view-as is master-only" });
        viewer = findDeveloper(asEmail); if (!viewer) return send(res, 404, { error: "developer not found" });
      }
      let mocks = visibleMocks(viewer);
      for (const key of ["topic", "date", "repo", "track"]) {
        const v = url.searchParams.get(key);
        if (v) mocks = mocks.filter((m) => String(m[key] || (key === "track" ? "BOTH" : "")) === v);
      }
      return send(res, 200, { viewer: viewer.email, mocks });
    }
    if (p === "/api/facets" && req.method === "GET") {
      const d = sessionOf(req); if (!d) return send(res, 401, { error: "no session" });
      const mocks = visibleMocks(d);
      const f = (k) => [...new Set(mocks.map((m) => m[k] || (k === "track" ? "BOTH" : "")).filter(Boolean))].sort();
      return send(res, 200, { topics: f("topic"), dates: f("date"), repos: f("repo"), tracks: f("track") });
    }
    if (p.startsWith("/api/mock/") && req.method === "GET") {
      const d = sessionOf(req); if (!d) return send(res, 401, { error: "no session" });
      const slug = decodeURIComponent(p.slice("/api/mock/".length));
      const mocks = load("mocks.json").mocks;
      const alias = mocks.find((m) => (m.aliases || []).includes(slug));
      if (alias) return send(res, 200, { redirect: alias.slug });
      const mock = visibleMocks(d).find((m) => m.slug === slug);
      if (!mock) return send(res, 404, { error: "not found or not cleared" });
      const comments = load("comments.json").comments.filter((c) => c.slug === mock.slug);
      return send(res, 200, { mock, comments });
    }
    if (p === "/api/comment" && req.method === "POST") {
      const d = sessionOf(req); if (!d) return send(res, 401, { error: "no session" });
      const { slug, text } = await body(req);
      const mock = visibleMocks(d).find((m) => m.slug === slug);
      if (!mock) return send(res, 404, { error: "not found or not cleared" });
      if (!text || !String(text).trim()) return send(res, 400, { error: "empty comment" });
      const db = load("comments.json");
      const c = { slug, by: d.email, at: new Date().toISOString(), text: String(text).slice(0, 4000) };
      db.comments.push(c); save("comments.json", db);
      chronicle("comment", { slug, by: d.email });
      return send(res, 200, { ok: true, comment: c });
    }

    // --- Resend delivery webhooks (Svix-signed; records the real
    // fate of each send on its comms entry) ---
    if (p === "/api/resend-webhook" && req.method === "POST") {
      if (!webhookConfigured()) return send(res, 503, { error: "webhook not armed" });
      const r = applyWebhook(await rawBody(req), req.headers);
      return send(res, r.ok ? 200 : 401, r);
    }

    // --- master control (SoSem; x-master-token) ---
    if (p.startsWith("/api/admin/")) {
      if (!isMaster(req)) return send(res, 403, { error: "master only" });
      if (p === "/api/admin/developers" && req.method === "GET") {
        return send(res, 200, { developers: load("developers.json").developers.map(publicDev) });
      }
      if (p === "/api/admin/chronicle" && req.method === "GET") return send(res, 200, load("chronicle.json"));
      if (p === "/api/admin/comms" && req.method === "GET") return send(res, 200, load("comms-log.json"));
      if (req.method === "POST") {
        const b = await body(req);
        if (p === "/api/admin/rename-mock") return send(res, 200, { ok: true, mock: life.renameMock(b.slug, b) });
        const ops = {
          "/api/admin/add-developer": () => life.addDeveloper(b),
          "/api/admin/mark-contact": () => life.markContact(b.email, b.channel),
          "/api/admin/grant-reading-room": () => life.grantReadingRoom(b.email),
          "/api/admin/grant-source": () => life.grantSource(b.email, b.repo, b.roadmap || null),
          "/api/admin/revoke-all": () => life.revokeAll(b.email, b.reason || ""),
          "/api/admin/reprompt": () => life.reprompt(b.email, b.note || undefined),
        };
        if (ops[p]) return send(res, 200, { ok: true, developer: publicDev(ops[p]()) });
      }
      return send(res, 404, { error: "unknown admin route" });
    }
    return send(res, 404, { error: "not found" });
  } catch (e) {
    return send(res, 500, { error: String(e.message || e) });
  }
};

// After a mutating request: (1) the comms queue drains — sends fire
// at the moment of the event when the mail key is configured, and the
// log records what actually went out; (2) in DB mode the write-through
// lands before the invocation completes — the record is durable,
// not hoped (the drain runs first so sent statuses persist too).
const server = http.createServer(async (req, res) => {
  await handleRequest(req, res);
  if (req.method === "POST") {
    await drainComms().catch(() => {});
    if (flushFn) await flushFn();
  }
});
export default server; // @vercel/node serves the http.Server instance

import { pathToFileURL } from "node:url";
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  server.listen(PORT, () => console.log(`dev-library listening on :${PORT}`));
}
