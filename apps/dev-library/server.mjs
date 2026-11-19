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
import { drainComms, sendEntryNow } from "./lib/mailer.mjs";
import { applyWebhook, webhookConfigured } from "./lib/webhook.mjs";
import * as life from "./lib/lifecycle.mjs";
import * as adv from "./lib/advisors.mjs";
import * as orgreg from "./lib/orgs.mjs";
import * as eng from "./lib/engagements.mjs";
import * as asm from "./lib/assessments.mjs";
import { loadPublications, findPublication, publicView } from "./lib/publisher.mjs";

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
  expertise: d.expertise, pairs: d.pairs || [], readingRoom: d.readingRoom.active,
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
      if (email) {
        const r = await requestCode(String(email)); // generic answer either way
        // The code sends SYNCHRONOUSLY: the attempt and its outcome
        // (status / provider id / error) are persisted before this
        // response returns, so the general queue — drained after the
        // response, oldest entries first — can never starve an OTP
        // behind stale entries again. The id is excluded from this
        // request's drain so it is not attempted twice.
        if (r && r.entryId) {
          await sendEntryNow(r.entryId).catch(() => {});
          (req._commsAttempted ??= new Set()).add(r.entryId);
        }
      }
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

    // --- the public publication viewer (P2 §2.6/§4): the published
    // copy proves an engagement exists and is progressing; it
    // identifies nobody. Public by design — the artifacts are
    // redacted by construction in lib/publisher.mjs, which holds no
    // identity-store read path. ---
    if (p === "/api/publications" && req.method === "GET") {
      return send(res, 200, { publications: loadPublications().map(publicView) });
    }
    if (p.startsWith("/api/publications/") && req.method === "GET") {
      const pub = findPublication(decodeURIComponent(p.slice("/api/publications/".length)));
      if (!pub) return send(res, 404, { error: "publication not found" });
      return send(res, 200, { publication: publicView(pub) });
    }

    // --- master control (SoSem; x-master-token) ---
    if (p.startsWith("/api/admin/")) {
      if (!isMaster(req)) return send(res, 403, { error: "master only" });
      if (p === "/api/admin/developers" && req.method === "GET") {
        let devs = load("developers.json").developers;
        // Expertise filters (P3 D3): role and/or realm; both together
        // match the exact Role×Realm pair.
        const role = url.searchParams.get("role"), realm = url.searchParams.get("realm");
        if (role || realm) devs = devs.filter(d => (d.pairs || []).some(pr =>
          (!role || pr.role === role) && (!realm || pr.realm === realm)));
        return send(res, 200, { developers: devs.map(publicDev) });
      }
      if (p === "/api/admin/chronicle" && req.method === "GET") return send(res, 200, load("chronicle.json"));
      if (p === "/api/admin/comms" && req.method === "GET") return send(res, 200, load("comms-log.json"));
      // --- L2L & Ecosystem Advisors: the advisory roster (distinct
      // from the Developer List — no tracks, grants, or sign-in) ---
      if (p === "/api/admin/advisors" && req.method === "GET") {
        return send(res, 200, { advisors: adv.loadAdvisors() });
      }
      if (p === "/api/admin/orgs" && req.method === "GET") {
        return send(res, 200, { orgs: orgreg.loadOrgs() });
      }
      // --- engagements (M1): desk surface + the blind client view ---
      const engMatch = p.match(/^\/api\/admin\/engagements(?:\/([^/]+)(\/client-view)?)?$/);
      if (engMatch && req.method === "GET") {
        if (!engMatch[1]) return send(res, 200, { engagements: eng.loadEngagements().map(eng.deskView) });
        const e = eng.findEngagement(engMatch[1]);
        if (!e) return send(res, 404, { error: "engagement not found" });
        return send(res, 200, engMatch[2] ? { view: eng.clientView(e) } : { engagement: eng.deskView(e) });
      }
      // --- P2 Assessment (Scope 2, separated track): desk surface ---
      if (p === "/api/admin/role-configs" && req.method === "GET") {
        return send(res, 200, { roleConfigs: asm.loadRoleConfigs() });
      }
      if (p === "/api/admin/assessments" && req.method === "GET") {
        return send(res, 200, { assessments: asm.loadAssessments().map(asm.assessmentView) });
      }
      const asmMatch = p.match(/^\/api\/admin\/assessments\/([^/]+)$/);
      if (asmMatch && req.method === "GET") {
        const a = asm.findAssessment(asmMatch[1]);
        if (!a) return send(res, 404, { error: "assessment not found" });
        return send(res, 200, { assessment: asm.assessmentView(a),
          runs: asm.loadRuns().filter(r => r.assessmentId === a.id) });
      }
      if (p === "/api/admin/approvers" && req.method === "GET") {
        return send(res, 200, { approvers: asm.loadApprovers(), config: asm.assessmentConfig() });
      }
      const engOutcomes = p.match(/^\/api\/admin\/engagements\/([^/]+)\/assessment-outcomes$/);
      if (engOutcomes && req.method === "GET") {
        return send(res, 200, { outcomes: asm.outcomeForEngagement(engOutcomes[1]) });
      }
      if (req.method === "POST") {
        const b = await body(req);
        if (p === "/api/admin/rename-mock") return send(res, 200, { ok: true, mock: life.renameMock(b.slug, b) });
        if (p === "/api/admin/advisors") return send(res, 200, { ok: true, advisor: adv.addAdvisor(b) });
        if (p === "/api/admin/advisors/remove") return send(res, 200, { ok: true, advisor: adv.removeAdvisor(b.email || b.id) });
        if (p === "/api/admin/engagements") return send(res, 200, { ok: true, engagement: eng.deskView(eng.openEngagement(b)) });
        // --- P2 Assessment POST surface ---
        if (p === "/api/admin/role-configs") return send(res, 200, { ok: true, roleConfig: asm.createRoleConfig(b) });
        if (p === "/api/admin/approvers") return send(res, 200, { ok: true, approvers: asm.setApprover(b.vertical, b.names) });
        const rcGen = p.match(/^\/api\/admin\/role-configs\/([^/]+)\/generate$/);
        if (rcGen) return send(res, 200, { ok: true, assessment: asm.assessmentView(asm.generateAssessment(rcGen[1], { by: b.by || "console" })) });
        const asmAction = p.match(/^\/api\/admin\/assessments\/([^/]+)\/(gate1|gate2|regenerate|runs|score-by-talent|publish-outcome)$/);
        if (asmAction) {
          const [, aid, action] = asmAction;
          if (action === "gate1") {
            const out = b.decision === "return" ? asm.returnGate1(aid, b) : asm.signGate1(aid, b);
            return send(res, 200, { ok: true, assessment: asm.assessmentView(out) });
          }
          if (action === "gate2") {
            const out = b.decision === "return" ? asm.returnGate2(aid, b) : asm.signGate2(aid, b);
            return send(res, 200, { ok: true, assessment: asm.assessmentView(out) });
          }
          if (action === "regenerate") return send(res, 200, { ok: true, assessment: asm.assessmentView(asm.regenerateAssessment(aid, { by: b.by || "console" })) });
          if (action === "runs") return send(res, 200, { ok: true, run: asm.recordRun({ assessmentId: aid, ...b }) });
          if (action === "score-by-talent") return send(res, 200, { ok: true, score: asm.scoreByTalent({ assessmentId: aid, talentDid: b.talentDid }) });
          if (action === "publish-outcome") return send(res, 200, { ok: true, publication: await asm.publishOutcomeForAssessment(aid, { runId: b.runId || null }) });
        }
        const runAction = p.match(/^\/api\/admin\/runs\/([^/]+)\/(attach-engagement|quote|publish)$/);
        if (runAction) {
          const [, rid, action] = runAction;
          if (action === "attach-engagement") return send(res, 200, { ok: true, run: asm.attachToEngagement(rid, b.engagementId) });
          if (action === "quote") return send(res, 200, { ok: true, quote: asm.quotePathA(rid, b) });
          if (action === "publish") return send(res, 200, { ok: true, publication: await asm.publishRunOutcome(rid) });
        }
        const engAction = p.match(/^\/api\/admin\/engagements\/([^/]+)\/(staff|unstaff|sign|deposit|close|cancel)$/);
        if (engAction) {
          const [, id, action] = engAction;
          const run = {
            staff: () => eng.staffEngagement(id, b.email),
            unstaff: () => eng.unstaffEngagement(id),
            sign: () => eng.recordSigned(id, b.ref || null),
            deposit: () => eng.recordDeposit(id, b.ref || null),
            close: () => eng.closeEngagement(id),
            cancel: () => eng.cancelEngagement(id, b.reason || ""),
          }[action];
          return send(res, 200, { ok: true, engagement: eng.deskView(run()) });
        }
        const ops = {
          "/api/admin/add-developer": () => life.addDeveloper(b),
          "/api/admin/mark-contact": () => life.markContact(b.email, b.channel),
          "/api/admin/set-expertise": () => life.setExpertise(b.email, b.pairs),
          "/api/admin/set-track": () => life.setTrack(b.email, b.track),
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
// log records what actually went out (drainComms dedupes the log,
// sends OTP entries first, and caps attempts per invocation so a
// clogged queue cannot burn the function budget); (2) in DB mode the
// write-through lands before the invocation completes — the record
// is durable, not hoped (the drain runs first so sent statuses
// persist too).
const server = http.createServer(async (req, res) => {
  await handleRequest(req, res);
  if (req.method === "POST") {
    await drainComms({ excludeIds: req._commsAttempted || new Set() }).catch(() => {});
    if (flushFn) await flushFn();
  }
});
export default server; // @vercel/node serves the http.Server instance

import { pathToFileURL } from "node:url";
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  server.listen(PORT, () => console.log(`dev-library listening on :${PORT}`));
}
