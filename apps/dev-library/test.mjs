// Phase 1 exit-gate rehearsal, automated. Runs the server against a
// TEMP data dir (the real chronicle is never touched) and walks the
// full lifecycle: one internal-track developer end to end (prospect →
// contact → reading room → comment → source → revocation → chronicle
// intact) and one external-track developer through the preview rule
// (track filtering). Comms in phase 1 (no mail key): QUEUED, never
// sent. Phase 2 (mail key set, stub mail API): sends fire at the
// event, the log marks them sent with the provider id, the delivered
// sign-in code works, and a failed send stays queued — never dropped.
import { spawn } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "devlib-test-"));
fs.cpSync(path.join(ROOT, "data"), tmp, { recursive: true });
// test-only fixture: an internal-only mock the external dev must never see
const mocks = JSON.parse(fs.readFileSync(path.join(tmp, "mocks.json"), "utf8"));
mocks.mocks.push({ slug: "internal-fixture", title: "Internal Fixture", description: "test only",
  topic: "Internal", date: "2026-11-18", repo: "DEVBUILDSTACK/UZE", repoAliases: [], aliases: [],
  clearance: [], track: "INTERNAL_ONLY", version: 1, changelog: ["v1 — test fixture"] });
fs.writeFileSync(path.join(tmp, "mocks.json"), JSON.stringify(mocks, null, 1));

const PORT = 18734;
const env = { ...process.env, PORT: String(PORT), LIBRARY_DATA: tmp,
  LIBRARY_MASTER_TOKEN: "test-master", LIBRARY_SECRET: "test-secret",
  RESEND_API_KEY: "", RESEND_API_URL: "" }; // phase 1: mail unconfigured, queue-only
const srv = spawn("node", ["server.mjs"], { cwd: ROOT, env, stdio: "pipe" });
const B = `http://127.0.0.1:${PORT}`;
let pass = 0, fail = 0;
const ok = (name, cond) => { if (cond) { pass++; console.log("PASS", name); } else { fail++; console.log("FAIL", name); } };
const call = async (p, { method = "GET", body, cookie, master } = {}) => {
  const r = await fetch(B + p, { method, headers: { "content-type": "application/json",
    ...(cookie ? { cookie } : {}), ...(master ? { "x-master-token": "test-master" } : {}) },
    body: body ? JSON.stringify(body) : undefined });
  return { status: r.status, body: await r.json().catch(() => ({})), cookie: r.headers.get("set-cookie") };
};
const comms = () => JSON.parse(fs.readFileSync(path.join(tmp, "comms-log.json"), "utf8")).sends;
const lastCode = (email) => {
  const s = comms().filter(x => x.to === email && x.kind === "otp").pop();
  return s && s.body.match(/code for the UZE Dev Library is (\d{6})/)[1];
};
const signIn = async (email) => {
  await call("/api/request-code", { method: "POST", body: { email } });
  const v = await call("/api/verify", { method: "POST", body: { email, code: lastCode(email) } });
  return v.cookie.split(";")[0];
};

try {
  for (let i = 0; i < 50; i++) { try { const r = await fetch(B + "/"); if (r.ok) break; } catch { await new Promise(r => setTimeout(r, 100)); } }

  ok("catalog without session -> 401", (await call("/api/catalog")).status === 401);
  const before = comms().length;
  await call("/api/request-code", { method: "POST", body: { email: "ghost@nowhere.test" } });
  ok("unlisted email: generic 200, nothing issued/logged", comms().length === before);

  const adm = { master: true };
  await call("/api/admin/add-developer", { method: "POST", master: true, body: { name: "Ina Internal", email: "ina@test.dev", track: "INTERNAL_ONLY", expertise: ["NEAR_AI"] } });
  await call("/api/admin/add-developer", { method: "POST", master: true, body: { name: "Xan External", email: "xan@test.dev", track: "EXTERNAL_PLACED", expertise: ["LIGHTNING"] } });
  ok("admin without token -> 403", (await call("/api/admin/developers")).status === 403);
  await call("/api/admin/mark-contact", { method: "POST", master: true, body: { email: "ina@test.dev", channel: "whatsapp" } });
  await call("/api/admin/grant-reading-room", { method: "POST", master: true, body: { email: "ina@test.dev" } });
  await call("/api/admin/grant-reading-room", { method: "POST", master: true, body: { email: "xan@test.dev" } });
  ok("invitations queued (not sent)", comms().filter(s => s.kind === "invitation" && ["ina@test.dev", "xan@test.dev"].includes(s.to)).length === 2 && comms().every(s => s.status === "queued"));

  const ina = await signIn("ina@test.dev");
  const cat = await call("/api/catalog", { cookie: ina });
  ok("internal dev sees BOTH + INTERNAL_ONLY mocks", cat.body.mocks.length === 2);
  ok("topic filter works", (await call("/api/catalog?topic=Internal", { cookie: ina })).body.mocks.length === 1);
  ok("repo filter works", (await call("/api/catalog?repo=DEVBUILDSTACK/uze-aeinfo-prediction-markets", { cookie: ina })).body.mocks.length === 1);
  ok("track filter works", (await call("/api/catalog?track=INTERNAL_ONLY", { cookie: ina })).body.mocks.length === 1);

  const xan = await signIn("xan@test.dev");
  const xcat = await call("/api/catalog", { cookie: xan });
  ok("external dev preview: sees BOTH, never INTERNAL_ONLY", xcat.body.mocks.length === 1 && xcat.body.mocks[0].slug === "agent-ticket-acquisition");
  ok("external dev direct-fetch of internal mock -> 404", (await call("/api/mock/internal-fixture", { cookie: xan })).status === 404);

  const c = await call("/api/comment", { method: "POST", cookie: xan, body: { slug: "agent-ticket-acquisition", text: "Suggest renaming the Miami fixture." } });
  ok("reading-room-only dev can comment pre-source", c.status === 200);
  const detail = await call("/api/mock/agent-ticket-acquisition", { cookie: xan });
  ok("comment lands on the mock", detail.body.comments.length === 1);

  ok("view-as by non-master -> 403", (await call("/api/catalog?email=xan@test.dev", { cookie: ina })).status === 403);
  ok("view-as by master -> 200", (await call("/api/catalog?email=xan@test.dev", { cookie: ina, master: true })).status === 200);

  await call("/api/admin/rename-mock", { method: "POST", master: true, body: { slug: "agent-ticket-acquisition", title: "Agent Ticket Acquisition — headless interface mock (renamed)", note: "title clarified in rehearsal" } });
  const redir = await call("/api/mock/agent-ticket-acquisition", { cookie: ina });
  ok("rename keeps slug, version bumps, changelog grows", redir.body.mock.version === 2 && redir.body.mock.changelog.length === 2);

  await call("/api/admin/reprompt", { method: "POST", master: true, body: { email: "ina@test.dev", note: "Access changed." } });
  ok("reprompt kills the live session (re-prompt behavior)", (await call("/api/me", { cookie: ina })).status === 401);

  const ina2 = await signIn("ina@test.dev");
  await call("/api/admin/grant-source", { method: "POST", master: true, body: { email: "ina@test.dev", repo: "DEVBUILDSTACK/uze-aeinfo-prediction-markets", roadmap: "AEInfo Sprint 6" } });
  const devs = await call("/api/admin/developers", adm);
  const inaRec = devs.body.developers.find(d => d.email === "ina@test.dev");
  ok("source grant recorded with stage", inaRec.stage === "source-access" && inaRec.source.length === 1);

  await call("/api/admin/revoke-all", { method: "POST", master: true, body: { email: "ina@test.dev", reason: "rehearsal complete" } });
  ok("revocation kills session", (await call("/api/me", { cookie: ina2 })).status === 401);
  const devs2 = await call("/api/admin/developers", adm);
  const inaRec2 = devs2.body.developers.find(d => d.email === "ina@test.dev");
  ok("reset to zero: no RR, no source, stage revoked", inaRec2.readingRoom === false && inaRec2.source.length === 0 && inaRec2.stage === "revoked");
  const chron = await call("/api/admin/chronicle", adm);
  const types = chron.body.entries.map(e => e.type);
  ok("chronicle preserved: add, contact, grants, comment, rename, reprompt, revoke all present",
    ["developer-added", "contact", "grant-reading-room", "grant-source", "comment", "mock-renamed", "reprompt", "revoke-all"].every(t => types.includes(t)));
  ok("revocation notice queued from desk@", comms().some(s => s.kind === "revocation" && s.from === "desk@uzemarkets.com" && s.status === "queued"));
} finally {
  srv.kill();
  fs.rmSync(tmp, { recursive: true, force: true });
}

// ---- Phase 2: the sending arm, against a stub mail API ----
const received = [];
const stub = http.createServer((req, res) => {
  let s = ""; req.on("data", (c) => (s += c)); req.on("end", () => {
    const payload = JSON.parse(s || "{}");
    received.push(payload);
    if ((payload.subject || "").includes("reset")) {
      res.writeHead(500, { "content-type": "application/json" });
      return res.end(JSON.stringify({ message: "stub failure" }));
    }
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({ id: "stub-msg-" + received.length }));
  });
});
await new Promise((r) => stub.listen(0, "127.0.0.1", r));
const tmp2 = fs.mkdtempSync(path.join(os.tmpdir(), "devlib-test2-"));
fs.cpSync(path.join(ROOT, "data"), tmp2, { recursive: true });
const PORT2 = 18735;
const env2 = { ...process.env, PORT: String(PORT2), LIBRARY_DATA: tmp2,
  LIBRARY_MASTER_TOKEN: "test-master", LIBRARY_SECRET: "test-secret",
  RESEND_API_KEY: "test-key", RESEND_API_URL: `http://127.0.0.1:${stub.address().port}/emails` };
const srv2 = spawn("node", ["server.mjs"], { cwd: ROOT, env: env2, stdio: "pipe" });
const B2 = `http://127.0.0.1:${PORT2}`;
const call2 = async (p, { method = "GET", body, master } = {}) => {
  const r = await fetch(B2 + p, { method, headers: { "content-type": "application/json",
    ...(master ? { "x-master-token": "test-master" } : {}) },
    body: body ? JSON.stringify(body) : undefined });
  return { status: r.status, body: await r.json().catch(() => ({})), cookie: r.headers.get("set-cookie") };
};
const comms2 = () => JSON.parse(fs.readFileSync(path.join(tmp2, "comms-log.json"), "utf8")).sends;
// The server drains the queue as the POST completes (same await point
// as the DB write-through), so poll briefly for the send to land.
const waitFor = async (fn, ms = 4000) => {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) { const v = fn(); if (v) return v; await new Promise(r => setTimeout(r, 100)); }
  return fn();
};
try {
  for (let i = 0; i < 50; i++) { try { const r = await fetch(B2 + "/"); if (r.ok) break; } catch { await new Promise(r => setTimeout(r, 100)); } }
  await call2("/api/admin/add-developer", { method: "POST", master: true, body: { name: "Mia Mail", email: "mia@test.dev", track: "EITHER", expertise: ["NEAR_AI"] } });
  await call2("/api/admin/grant-reading-room", { method: "POST", master: true, body: { email: "mia@test.dev" } });
  const inv = await waitFor(() => received.find((x) => (x.to || []).includes("mia@test.dev") && (x.subject || "").includes("access to the UZE Dev Library")));
  ok("mail configured: invitation SENT at the grant event, from desk@", !!inv && String(inv.from).includes("desk@uzemarkets.com"));
  ok("invitation is branded: greeting, tangerine, library link, desk signature",
    !!inv && inv.html.includes("Dear Development Partner") && inv.html.includes("#ff6b00") &&
    inv.html.includes("dev.uzemarkets.com") && inv.html.includes("The UZE Markets Desk") &&
    inv.text.includes("The UZE Markets Desk"));
  ok("house CTAs sit above the signature, logo underneath (James's layout rule)",
    !!inv && inv.html.includes("x.com/UZEmarkets_fyi") && inv.html.includes("podcast.uzemarkets.com") &&
    inv.html.indexOf("UZEmarkets_fyi") < inv.html.indexOf("The UZE Markets Desk") &&
    inv.html.indexOf("The UZE Markets Desk") < inv.html.indexOf("font-size:22px") &&
    inv.text.includes("UZEmarkets_fyi"));
  const invLog = await waitFor(() => { const e = comms2().find((s) => s.kind === "invitation" && s.to === "mia@test.dev"); return e && e.status === "sent" ? e : null; });
  ok("log marks the invitation sent with provider id", !!invLog && String(invLog.providerId).startsWith("stub-msg-"));

  await call2("/api/request-code", { method: "POST", body: { email: "mia@test.dev" } });
  const otpMail = await waitFor(() => received.filter((x) => (x.subject || "").includes("sign-in code")).pop());
  const delivered = otpMail && otpMail.text.match(/sign-in code for the UZE Dev Library is (\d{6})/)[1];
  ok("sign-in code SENT at the request event", !!delivered);
  ok("code email is branded and shows the code large",
    !!delivered && otpMail.html.includes(delivered) && otpMail.html.includes("Hello,"));
  const v = await call2("/api/verify", { method: "POST", body: { email: "mia@test.dev", code: delivered } });
  ok("the delivered code signs in", v.status === 200 && !!v.cookie);

  await call2("/api/admin/revoke-all", { method: "POST", master: true, body: { email: "mia@test.dev", reason: "stub failure rehearsal" } });
  const revLog = await waitFor(() => { const e = comms2().find((s) => s.kind === "revocation" && s.to === "mia@test.dev"); return e && e.attempts >= 1 ? e : null; });
  ok("failed send stays queued, attempt + error recorded (never dropped)",
    !!revLog && revLog.status === "queued" && !!revLog.lastError);
} finally {
  srv2.kill();
  stub.close();
  fs.rmSync(tmp2, { recursive: true, force: true });
}
console.log(`\nRESULT: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
