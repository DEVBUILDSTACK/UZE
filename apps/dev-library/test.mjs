// Phase 1 exit-gate rehearsal, automated. Runs the server against a
// TEMP data dir (the real chronicle is never touched) and walks the
// full lifecycle: one internal-track developer end to end (prospect →
// contact → reading room → comment → source → revocation → chronicle
// intact) and one external-track developer through the preview rule
// (track filtering). Comms sends must be QUEUED, never sent.
import { spawn } from "node:child_process";
import fs from "node:fs";
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
  LIBRARY_MASTER_TOKEN: "test-master", LIBRARY_SECRET: "test-secret" };
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
  ok("invitations queued (not sent)", comms().filter(s => s.kind === "invitation").length === 2 && comms().every(s => s.status === "queued"));

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
console.log(`\nRESULT: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
