// UZE Buildr Team rehearsal — the eco contributor surface
// (buildr-eco.uzemarkets.com, host-routed in this app). Runs the
// server against TEMP data dirs (the real chronicle is never
// touched) in three phases:
//   A — eco host, mail unconfigured: the door, org visibility
//       (James's segmentation ruling), the dual-holder flow
//       sequence, forgery refusal, resume.
//   B — eco host, stub mail API: the OTP actually sends from
//       "UZE Buildr Team <desk@uzemarkets.com>" — to the master-
//       seeded test persona at uze@uzemarkets.com ONLY — and the
//       dual invitation sends with both surfaces in order.
//   C — library host (eco reached via the x-eco-host test header):
//       host separation, OTP namespace isolation, the master
//       surface (roster, progress, stalled flags, composer rule),
//       and the library sign-in that completes a dual sequence.
// Test personas live in fixtures only; the five seeded principals
// receive nothing.
import { spawn } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
let pass = 0, fail = 0;
const ok = (name, cond) => { if (cond) { pass++; console.log("PASS", name); } else { fail++; console.log("FAIL", name); } };

const OLD = new Date(Date.now() - 73 * 3600 * 1000).toISOString();
function makeTmp() {
  const t = fs.mkdtempSync(path.join(os.tmpdir(), "eco-test-"));
  fs.cpSync(path.join(ROOT, "data"), t, { recursive: true });
  const eco = JSON.parse(fs.readFileSync(path.join(t, "eco-contributors.json"), "utf8"));
  const C = (id, name, email, orgs) => ({ id, name, email, role: "Ecosystem Contributor", orgs,
    sessionEpoch: 0, stage: "seeded", addedAt: "2026-11-19T00:00:00.000Z" });
  eco.contributors.push(
    C("eco-dual", "Dana Dual", "dual@test.dev", ["UZE", "L2Launch", "DFI", "FVC"]),
    C("eco-dual2", "Devon Dual", "dual2@test.dev", ["UZE", "L2Launch", "DFI", "FVC"]),
    C("eco-only", "Eko Only", "ecoonly@test.dev", ["UZE"]),
    C("eco-dual-stall", "Stalled Dual", "dualstall@test.dev", ["FVC"]),
    C("eco-single-old", "Old Single", "singleold@test.dev", ["FVC"]));
  fs.writeFileSync(path.join(t, "eco-contributors.json"), JSON.stringify(eco, null, 1));
  const devs = JSON.parse(fs.readFileSync(path.join(t, "developers.json"), "utf8"));
  const D = (name, email, active) => ({ name, email, expertise: [], pairs: [], roadmapExempt: false, track: "EITHER",
    contact: { email: { done: false, at: null }, whatsapp: { done: false, at: null } },
    readingRoom: { active, grantedAt: active ? "2026-11-19T00:00:00.000Z" : null, revokedAt: null },
    source: [], sessionEpoch: 0, roadmap: null, stage: active ? "reading-room" : "prospect", stageHistory: [] });
  devs.developers.push(D("Dana Dual", "dual@test.dev", true), D("Devon Dual", "dual2@test.dev", false),
    D("Lib Only", "libonly@test.dev", true), D("Stalled Dual", "dualstall@test.dev", true));
  fs.writeFileSync(path.join(t, "developers.json"), JSON.stringify(devs, null, 1));
  fs.writeFileSync(path.join(t, "eco-flow.json"), JSON.stringify({ version: 1, events: [
    { id: "fstall1", contributorId: "eco-dual-stall", step: "signed_in", at: OLD },
    { id: "fsingle1", contributorId: "eco-single-old", step: "signed_in", at: OLD },
  ] }, null, 1));
  return t;
}
function boot(port, tmp, extraEnv) {
  const env = { ...process.env, PORT: String(port), LIBRARY_DATA: tmp,
    LIBRARY_MASTER_TOKEN: "test-master", LIBRARY_SECRET: "test-secret",
    RESEND_API_KEY: "", RESEND_API_URL: "", DATABASE_URL: "", POSTGRES_URL: "", ...extraEnv };
  const srv = spawn("node", ["server.mjs"], { cwd: ROOT, env, stdio: "pipe" });
  return srv;
}
async function waitUp(B) {
  for (let i = 0; i < 50; i++) { try { const r = await fetch(B + "/"); if (r.status) return; } catch { await new Promise(r => setTimeout(r, 100)); } }
  throw new Error("server did not come up: " + B);
}
function client(B) {
  const call = async (p, { method = "GET", body, cookie, master, eco } = {}) => {
    const r = await fetch(B + p, { method, redirect: "manual",
      headers: { "content-type": "application/json", accept: "application/json",
        ...(cookie ? { cookie } : {}), ...(master ? { "x-master-token": "test-master" } : {}),
        ...(eco ? { "x-eco-host": "1" } : {}) },
      body: body ? JSON.stringify(body) : undefined });
    return { status: r.status, body: await r.json().catch(() => ({})), cookie: r.headers.get("set-cookie"), location: r.headers.get("location") };
  };
  const page = async (p, { cookie, eco } = {}) => {
    const r = await fetch(B + p, { redirect: "manual",
      headers: { ...(cookie ? { cookie } : {}), ...(eco ? { "x-eco-host": "1" } : {}) } });
    return { status: r.status, text: await r.text(), location: r.headers.get("location") };
  };
  return { call, page };
}
const comms = (tmp) => JSON.parse(fs.readFileSync(path.join(tmp, "comms-log.json"), "utf8")).sends;
const ecoCode = (tmp, email) => {
  const s = comms(tmp).filter(x => x.to === email && x.kind === "eco-otp").pop();
  return s && s.body.match(/code for the UZE Buildr Team is (\d{6})/)[1];
};
const libCode = (tmp, email) => {
  const s = comms(tmp).filter(x => x.to === email && x.kind === "otp").pop();
  return s && s.body.match(/code for the UZE Dev Library is (\d{6})/)[1];
};
async function ecoSignIn(cl, tmp, email) {
  await cl.call("/api/eco/request-code", { method: "POST", body: { email } });
  const v = await cl.call("/api/eco/verify", { method: "POST", body: { email, code: ecoCode(tmp, email) } });
  return v.cookie.split(";")[0];
}

// ================= Phase A — eco host, mail unconfigured =================
const tmpA = makeTmp();
const srvA = boot(18741, tmpA, { ECO_HOST_OVERRIDE: "1" });
const A = client("http://127.0.0.1:18741");
try {
  await waitUp("http://127.0.0.1:18741");

  const signin = await A.page("/");
  ok("A: sign-in page serves the Buildr Team door", signin.status === 200 &&
    signin.text.includes("UZE Buildr Team") && signin.text.includes("one-time code") &&
    signin.text.includes("no GitHub account"));
  ok("A: no internal naming anywhere on the sign-in page", !/reading room/i.test(signin.text));
  ok("A: sign-in page carries the house palette only",
    ["#ff6b00", "#f5f2ee", "#FDEEE2", "#1a1a1a"].every(h => signin.text.includes(h)) &&
    !/#b02a37|#2e7d32|#3ecf6e/.test(signin.text));

  const unauthEco = await A.page("/ecosystem");
  ok("A: unauthenticated /ecosystem redirects to the door", unauthEco.status === 302 && unauthEco.location === "/");
  const unauthMe = await A.call("/api/eco/me");
  ok("A: unauthenticated /api/eco/me refuses", unauthMe.status === 401);
  const unauthOrg = await A.page("/org/fvc");
  ok("A: unauthenticated org page redirects to the door", unauthOrg.status === 302);

  const before = comms(tmpA).length;
  const unk = await A.call("/api/eco/request-code", { method: "POST", body: { email: "nobody@example.com" } });
  ok("A: unknown email gets the generic answer and no code is issued",
    unk.status === 200 && comms(tmpA).filter(x => x.kind === "eco-otp").length === 0 && comms(tmpA).length === before);

  // SJ: the seeded record carries no email, so no code can ever be
  // requested for him — the registry fact plus the silent refusal.
  const roster = JSON.parse(fs.readFileSync(path.join(tmpA, "eco-contributors.json"), "utf8")).contributors;
  const sj = roster.find(c => c.id === "eco-shradesh-jodawat");
  ok("A: SJ is seeded with email null and full org visibility", !!sj && sj.email === null && sj.orgs.length === 4);
  await A.call("/api/eco/request-code", { method: "POST", body: { email: "shradesh.jodawat@test.dev" } });
  ok("A: no code can be requested for SJ (no email on file)",
    comms(tmpA).filter(x => x.kind === "eco-otp").length === 0);

  // Dipanshu — James's segmentation ruling, enforced server-side.
  await A.call("/api/eco/request-code", { method: "POST", body: { email: "dipanshuhappy@gmail.com" } });
  const dEntry = comms(tmpA).filter(x => x.to === "dipanshuhappy@gmail.com" && x.kind === "eco-otp").pop();
  ok("A: Dipanshu's code is queued as an eco OTP from the desk", !!dEntry && dEntry.from === "desk@uzemarkets.com");
  const wrong = await A.call("/api/eco/verify", { method: "POST", body: { email: "dipanshuhappy@gmail.com", code: "000000" } });
  ok("A: wrong code is refused", wrong.status === 401);
  const dv = await A.call("/api/eco/verify", { method: "POST", body: { email: "dipanshuhappy@gmail.com", code: ecoCode(tmpA, "dipanshuhappy@gmail.com") } });
  ok("A: Dipanshu verifies and gets the eco_session cookie", dv.status === 200 && (dv.cookie || "").includes("eco_session="));
  const dCookie = dv.cookie.split(";")[0];
  ok("A: Dipanshu GET /ecosystem 200", (await A.page("/ecosystem", { cookie: dCookie })).status === 200);
  ok("A: Dipanshu GET /org/fvc 200", (await A.page("/org/fvc", { cookie: dCookie })).status === 200);
  ok("A: Dipanshu GET /org/l2l 403", (await A.page("/org/l2l", { cookie: dCookie })).status === 403);
  ok("A: Dipanshu GET /org/dfi 403", (await A.page("/org/dfi", { cookie: dCookie })).status === 403);
  ok("A: Dipanshu GET /org/uze 403", (await A.page("/org/uze", { cookie: dCookie })).status === 403);
  const dHome = await A.page("/", { cookie: dCookie });
  ok("A: Dipanshu's home shows FVC and hides the ungranted sections",
    dHome.text.includes('href="/org/fvc"') && !dHome.text.includes('href="/org/l2l"') &&
    !dHome.text.includes('href="/org/dfi"') && !dHome.text.includes('href="/org/uze"'));
  ok("A: Dipanshu (single-surface) gets no resume lead and no other-surface card",
    !dHome.text.includes("Pick up where you left off") && !dHome.text.includes("Your other surface"));
  ok("A: the programmatic band is on the Ecosystem page, framed as underpinning — not a third surface",
    (await A.page("/ecosystem", { cookie: dCookie })).text.includes("not a third surface") &&
    (await A.page("/ecosystem", { cookie: dCookie })).text.includes("The programmatic core") &&
    (await A.page("/ecosystem", { cookie: dCookie })).text.includes("micro accomplishments"));

  // Jonathan — full access, single-surface (no library grant).
  const jCookie = await ecoSignIn(A, tmpA, "schmidtcommunications@gmail.com");
  for (const slug of ["uze", "l2l", "dfi", "fvc"]) {
    ok(`A: full-access session reaches /org/${slug}`, (await A.page(`/org/${slug}`, { cookie: jCookie })).status === 200);
  }
  const jHome = await A.page("/", { cookie: jCookie });
  ok("A: full-access single-surface home has no dual machinery",
    !jHome.text.includes("Pick up where you left off") && !jHome.text.includes("Your other surface"));
  ok("every eco page footer carries the three-surface brow — quiet gray links that resolve to ink on hover (James, 2026-11-19)",
    jHome.text.includes('class="brow"') && jHome.text.includes('>BUILDER COLLABORATOR</a>') && jHome.text.includes('.brow a:hover{color:var(--ink)'));
  ok("A: surfaces render in full for a signed-in contributor",
    (await A.page("/surfaces/human", { cookie: jCookie })).text.includes("Pillar") &&
    (await A.page("/surfaces/agentic", { cookie: jCookie })).status === 200);

  // The micro FAQ: post-OTP only, step by step in the app's own
  // labels, pillars named as pillars with doors to the surfaces.
  const unauthFaq = await A.page("/faq");
  ok("A: unauthenticated /faq redirects to the door (the micro FAQ is post-OTP only)",
    unauthFaq.status === 302 && unauthFaq.location === "/");
  const faq = await A.page("/faq", { cookie: jCookie });
  ok("A: the micro FAQ renders signed-in, step by step, in the app's own labels",
    faq.status === 200 && faq.text.includes("How Buildr Team works — step by step") &&
    faq.text.includes("Email me a sign-in code") && faq.text.includes("One-time code") &&
    faq.text.includes("Team overview — completed") && faq.text.includes("Pick up where you left off") &&
    faq.text.includes("Your other surface") && faq.text.includes("Not your section") &&
    faq.text.includes("Sign out") && faq.text.includes("desk@uzemarkets.com"));
  ok("A: the micro FAQ names the pillars as pillars and links to the surface pages where they live",
    faq.text.includes("Pillar 1 — One canonical source of values") &&
    faq.text.includes("Pillar 4 — The car wash: no page deploys unwashed") &&
    faq.text.includes("Pillar 7 — Judgment stays human") &&
    faq.text.includes("Pillar 2 — Market reasoning models and data assets — a real edge") &&
    faq.text.includes('href="/surfaces/human"') && faq.text.includes('href="/surfaces/agentic"') &&
    faq.text.includes("Diagram code") && faq.text.includes("not a third surface"));
  ok("A: no internal naming on the micro FAQ", !/reading room/i.test(faq.text));
  ok("A: home nav and the how-it-works card carry the door to the micro FAQ",
    jHome.text.includes('href="/faq"') && jHome.text.includes("How Buildr Team works — step by step"));

  // Dual-holder flow: the tracked sequence binds dual-holders only.
  const dualCookie = await ecoSignIn(A, tmpA, "dual@test.dev");
  const me = await A.call("/api/eco/me", { cookie: dualCookie });
  ok("A: dual-holder /api/eco/me reports dual + derived step signed_in",
    me.body.dual === true && me.body.progress.current === "signed_in" && me.body.progress.next === "overview_viewed");
  const dualHome = await A.page("/", { cookie: dualCookie });
  ok("A: dual-holder home leads with the resume block and the other-surface card",
    dualHome.text.includes("Pick up where you left off") && dualHome.text.includes("Your other surface") &&
    dualHome.text.includes("Continue to the UZE Dev Partner Library"));

  const forge = await A.call("/api/eco/flow", { method: "POST", cookie: dualCookie, body: { step: "overview_completed" } });
  ok("A: no endpoint accepts a step claim (forgery impossible)", forge.status === 404);
  const noSess = await A.call("/api/eco/flow/complete-overview", { method: "POST" });
  ok("A: complete-overview without a session refuses", noSess.status === 401);
  const dual2Cookie = await ecoSignIn(A, tmpA, "dual2@test.dev");
  const tooEarly = await A.call("/api/eco/flow/complete-overview", { method: "POST", cookie: dual2Cookie });
  ok("A: complete-overview before viewing the overview refuses (order enforced)", tooEarly.status === 400);

  await A.page("/ecosystem", { cookie: dualCookie });
  const me2 = await A.call("/api/eco/me", { cookie: dualCookie });
  ok("A: viewing the Ecosystem page records overview_viewed", me2.body.progress.steps.overview_viewed != null);
  const completed = await A.call("/api/eco/flow/complete-overview", { method: "POST", cookie: dualCookie });
  ok("A: the Next button records overview_completed", completed.status === 200 && completed.body.progress.current === "overview_completed");
  const adv = await A.page("/eco/advance-to-library", { cookie: dualCookie });
  ok("A: advancing goes to the library and records the step",
    adv.status === 302 && adv.location === "https://dev.uzemarkets.com" &&
    (await A.call("/api/eco/me", { cookie: dualCookie })).body.progress.steps.advanced_to_library != null);

  // Resume: sign out, sign back in — home still leads from the derived step.
  await A.call("/api/eco/signout", { method: "POST", cookie: dualCookie });
  const dualCookie2 = await ecoSignIn(A, tmpA, "dual@test.dev");
  const resumed = await A.page("/", { cookie: dualCookie2 });
  const me3 = await A.call("/api/eco/me", { cookie: dualCookie2 });
  ok("A: resume lands at the derived step (advanced; next is the library sign-in)",
    me3.body.progress.current === "advanced_to_library" && me3.body.progress.next === "library_signed_in" &&
    resumed.text.includes("Pick up where you left off"));

  // Eco-only persona: eco invitation path, no cross-link, no lead.
  const onlyCookie = await ecoSignIn(A, tmpA, "ecoonly@test.dev");
  const onlyHome = await A.page("/", { cookie: onlyCookie });
  ok("A: eco-only persona sees no other-surface card and no resume lead",
    !onlyHome.text.includes("Your other surface") && !onlyHome.text.includes("Pick up where you left off"));
} finally {
  srvA.kill();
}

// ================= Phase B — eco host + stub mail API =================
const received = [];
const stub = http.createServer((req, res) => {
  let s = ""; req.on("data", (c) => (s += c)); req.on("end", () => {
    received.push(JSON.parse(s || "{}"));
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({ id: "stub-msg-" + received.length }));
  });
});
await new Promise((r) => stub.listen(0, "127.0.0.1", r));
const tmpB = makeTmp();
const srvB = boot(18742, tmpB, { ECO_HOST_OVERRIDE: "1",
  RESEND_API_KEY: "test-key", RESEND_API_URL: `http://127.0.0.1:${stub.address().port}/emails` });
const Bc = client("http://127.0.0.1:18742");
try {
  await waitUp("http://127.0.0.1:18742");
  // The ONLY real address test mail may touch: James's internal
  // testing address, via a master-seeded test persona.
  const added = await Bc.call("/api/admin/eco/contributors", { method: "POST", master: true,
    body: { name: "SoSem mail-path test", email: "uze@uzemarkets.com", role: "Ecosystem Contributor", orgs: ["UZE", "L2Launch", "DFI", "FVC"] } });
  ok("B: master seeds the uze@ test persona", added.status === 200 && added.body.contributor.email === "uze@uzemarkets.com");
  await Bc.call("/api/eco/request-code", { method: "POST", body: { email: "uze@uzemarkets.com" } });
  const otpMail = received.find(m => (m.to || []).includes("uze@uzemarkets.com") && /sign-in code/.test(m.subject || ""));
  ok("B: the eco OTP sends from the Buildr Team name on desk@",
    !!otpMail && otpMail.from === "UZE Buildr Team <desk@uzemarkets.com>");
  const sentEntry = comms(tmpB).filter(x => x.to === "uze@uzemarkets.com" && x.kind === "eco-otp").pop();
  ok("B: the OTP entry is marked sent with a provider id, inside the request",
    !!sentEntry && sentEntry.status === "sent" && String(sentEntry.providerId || "").startsWith("stub-msg-"));
  const codeFromMail = otpMail && otpMail.text.match(/is (\d{6})\./)[1];
  const vB = await Bc.call("/api/eco/verify", { method: "POST", body: { email: "uze@uzemarkets.com", code: codeFromMail } });
  ok("B: the delivered code signs the test persona in", vB.status === 200 && (vB.cookie || "").includes("eco_session="));

  const inv = await Bc.call("/api/admin/eco/invite", { method: "POST", master: true, body: { email: "dual@test.dev" } });
  ok("B: the composer picks invitation_dual for a dual-holder", inv.body.kind === "invitation_dual" && !!inv.body.entryId);
  // The invitation sends via the post-response drain (the standing
  // discipline for non-OTP mail) — poll briefly for its arrival.
  let dualMail = null;
  for (let i = 0; i < 30 && !dualMail; i++) {
    dualMail = received.find(m => (m.to || []).includes("dual@test.dev") && /Start here/.test(m.subject || ""));
    if (!dualMail) await new Promise(r => setTimeout(r, 100));
  }
  ok("B: the dual invitation sends from the Buildr Team name, ecosystem first",
    !!dualMail && dualMail.from === "UZE Buildr Team <desk@uzemarkets.com>" &&
    dualMail.text.indexOf("buildr-eco.uzemarkets.com") >= 0 &&
    dualMail.text.indexOf("buildr-eco.uzemarkets.com") < dualMail.text.indexOf("dev.uzemarkets.com") &&
    dualMail.text.includes("Start with the ecosystem — the whole picture. Then the library, where the work itself lives."));
  ok("B: the dual invitation HTML carries the hosted hero and both surfaces in order",
    !!dualMail && dualMail.html.includes("https://dev.uzemarkets.com/hero.gif") &&
    dualMail.html.indexOf("buildr-eco.uzemarkets.com") < dualMail.html.lastIndexOf("dev.uzemarkets.com"));
  // The diagrams attachment: a full-visibility invitee's invitation
  // carries the complete diagrams set as a .md attachment.
  const dualAtt = dualMail && (dualMail.attachments || [])[0];
  const dualAttText = dualAtt ? Buffer.from(dualAtt.content, "base64").toString("utf8") : "";
  ok("B: the full-visibility dual invitation carries the diagrams attachment (all three Mermaids)",
    !!dualAtt && dualAtt.filename === "UZE-ecosystem-diagrams.md" &&
    (dualAttText.match(/```mermaid/g) || []).length === 3 &&
    dualAttText.includes("Diagram 1") && dualAttText.includes("Diagram 3"));
  const dualEntry = comms(tmpB).filter(x => x.to === "dual@test.dev" && x.kind === "invitation_dual").pop();
  ok("B: the attachment is recorded on the comms entry",
    !!dualEntry && Array.isArray(dualEntry.attachments) && dualEntry.attachments[0].file === "eco/content/diagrams.md");

  // The uze@ test persona: the bundled data ALSO carries James's
  // owner persona at this address with a library grant, so the
  // composer correctly treats it as a dual-holder — its invitation
  // is the dual one, and (full visibility) it carries the set.
  const uzeInv = await Bc.call("/api/admin/eco/invite", { method: "POST", master: true, body: { email: "uze@uzemarkets.com" } });
  ok("B: the uze@ test persona composes invitation_dual (it holds both surfaces)",
    uzeInv.body.kind === "invitation_dual");
  let uzeMail = null;
  for (let i = 0; i < 30 && !uzeMail; i++) {
    uzeMail = received.find(m => (m.to || []).includes("uze@uzemarkets.com") && /Start here/.test(m.subject || ""));
    if (!uzeMail) await new Promise(r => setTimeout(r, 100));
  }
  const uzeAtt = uzeMail && (uzeMail.attachments || [])[0];
  ok("B: the test invitation to uze@ carries the diagrams attachment",
    !!uzeMail && !!uzeAtt && uzeAtt.filename === "UZE-ecosystem-diagrams.md" &&
    (Buffer.from(uzeAtt.content, "base64").toString("utf8").match(/```mermaid/g) || []).length === 3);
  // Design lineage (James, 2026-11-19): the eco invitations render
  // on the SAME template as the Jonathan letter — the v5 template of
  // record: hosted hero (never data-URI, never CID), black pill
  // CTAs, the creamsicle band, hairlines, the © 2026 footer.
  ok("B: the invitation renders on the v5 template lineage (hosted hero, pills, creamsicle, footer)",
    !!uzeMail && uzeMail.html.includes('src="https://dev.uzemarkets.com/hero.gif"') &&
    !uzeMail.html.includes("data:image") && !uzeMail.html.includes("cid:") &&
    uzeMail.html.includes("background-color:#FDEEE2") && uzeMail.html.includes("border-radius:999px") &&
    uzeMail.html.includes("© 2026") && uzeMail.from === "UZE Buildr Team <desk@uzemarkets.com>");

  // A segmented invitee: no subset file exists, so nothing is
  // attached and the reason is recorded — sections never leak.
  await Bc.call("/api/admin/eco/invite", { method: "POST", master: true, body: { email: "ecoonly@test.dev" } });
  let onlyMail = null;
  for (let i = 0; i < 30 && !onlyMail; i++) {
    onlyMail = received.find(m => (m.to || []).includes("ecoonly@test.dev") && /Your access to the UZE Buildr Team/.test(m.subject || ""));
    if (!onlyMail) await new Promise(r => setTimeout(r, 100));
  }
  const onlyEntry = comms(tmpB).filter(x => x.to === "ecoonly@test.dev" && x.kind === "eco-invitation").pop();
  ok("B: a segmented invitee's invitation carries NO attachment, with the reason recorded",
    !!onlyMail && !(onlyMail.attachments && onlyMail.attachments.length) &&
    !!onlyEntry && /No visibility-consistent diagrams file/.test(onlyEntry.attachmentNote || ""));
} finally {
  srvB.kill(); stub.close();
}

// ================= Phase C — library host; eco via test header =================
const srvC = boot(18743, tmpA, {});
const Cc = client("http://127.0.0.1:18743");
try {
  await waitUp("http://127.0.0.1:18743");
  const libHome = await Cc.page("/");
  ok("C: the library host still serves the Dev Library, untouched", libHome.status === 200 && libHome.text.includes("Dev Library"));
  const ecoHome = await Cc.page("/", { eco: true });
  ok("C: the eco host header routes to the Buildr Team door", ecoHome.status === 200 && ecoHome.text.includes("UZE Buildr Team"));

  const rosterRes = await Cc.call("/api/admin/eco/contributors", { master: true });
  ok("C: master roster lists the five seeded principals",
    rosterRes.status === 200 && rosterRes.body.contributors.length >= 5 &&
    rosterRes.body.contributors.find(c => c.id === "eco-shradesh-jodawat").email === null &&
    JSON.stringify(rosterRes.body.contributors.find(c => c.id === "eco-dipanshu-singh").orgs) === '["FVC"]');
  const noMaster = await Cc.call("/api/admin/eco/progress");
  ok("C: progress API refuses without the master token", noMaster.status === 403);
  const prog = await Cc.call("/api/admin/eco/progress", { master: true });
  const byId = Object.fromEntries(prog.body.progress.map(x => [x.contributorId, x]));
  ok("C: progress derives the dual-holder's steps from Phase A events",
    byId["eco-dual"].current === "advanced_to_library" && byId["eco-dual"].dual === true && byId["eco-dual"].completed === false);
  ok("C: a dual-holder idle 73h is flagged stalled", byId["eco-dual-stall"].stalled === true);
  ok("C: a single-surface contributor is NEVER flagged stalled (no requirement → no stall)",
    byId["eco-single-old"].stalled === false && byId["eco-single-old"].dual === false);

  // Composer rule, all three branches (queue-only inspection).
  const invDual = await Cc.call("/api/admin/eco/invite", { method: "POST", master: true, body: { email: "dual@test.dev" } });
  const invEco = await Cc.call("/api/admin/eco/invite", { method: "POST", master: true, body: { email: "ecoonly@test.dev" } });
  const invLib = await Cc.call("/api/admin/eco/invite", { method: "POST", master: true, body: { email: "libonly@test.dev" } });
  ok("C: composer — dual-holder composes invitation_dual", invDual.body.kind === "invitation_dual");
  ok("C: composer — eco-only composes the eco invitation", invEco.body.kind === "eco-invitation");
  ok("C: composer — library-only stays lifecycle's own invitation (nothing queued here)",
    invLib.body.kind === "invitation" && invLib.body.entryId === null);
  const dualEntry = comms(tmpA).filter(x => x.to === "dual@test.dev" && x.kind === "invitation_dual").pop();
  ok("C: the dual invitation body names both surfaces in order",
    !!dualEntry && dualEntry.body.indexOf("UZE Buildr Team — start here") >= 0 &&
    dualEntry.body.indexOf("buildr-eco.uzemarkets.com") < dualEntry.body.indexOf("dev.uzemarkets.com") &&
    dualEntry.body.includes("UZE Dev Partner Library — then step into the library"));
  // Jonathan (the inaugural full-visibility case): composing his
  // invitation records the complete diagrams attachment on the entry.
  await Cc.call("/api/admin/eco/invite", { method: "POST", master: true, body: { email: "schmidtcommunications@gmail.com" } });
  const jonEntry = comms(tmpA).filter(x => x.to === "schmidtcommunications@gmail.com" && x.kind === "eco-invitation").pop();
  ok("C: a full-visibility principal's composed invitation records the diagrams attachment",
    !!jonEntry && Array.isArray(jonEntry.attachments) && jonEntry.attachments[0].filename === "UZE-ecosystem-diagrams.md");

  // The library grant flow itself honors the dual rule.
  const grant = await Cc.call("/api/admin/grant-reading-room", { method: "POST", master: true, body: { email: "dual2@test.dev" } });
  const dual2Entries = comms(tmpA).filter(x => x.to === "dual2@test.dev");
  ok("C: granting the library to an eco contributor composes ONE dual invitation, never a competing library one",
    grant.status === 200 && dual2Entries.some(x => x.kind === "invitation_dual") &&
    !dual2Entries.some(x => x.kind === "invitation"));

  // OTP namespace isolation: an eco code is not a library code, and
  // a library code is not an eco code.
  await Cc.call("/api/eco/request-code", { method: "POST", eco: true, body: { email: "dual@test.dev" } });
  const eCode = ecoCode(tmpA, "dual@test.dev");
  const crossLib = await Cc.call("/api/verify", { method: "POST", body: { email: "dual@test.dev", code: eCode } });
  ok("C: an eco code does not open the Dev Library", crossLib.status === 401);
  await Cc.call("/api/request-code", { method: "POST", body: { email: "dual@test.dev" } });
  const lCode = libCode(tmpA, "dual@test.dev");
  const crossEco = await Cc.call("/api/eco/verify", { method: "POST", eco: true, body: { email: "dual@test.dev", code: lCode } });
  ok("C: a library code does not open the Buildr Team surface", crossEco.status === 401);

  // The library sign-in completes the dual sequence.
  const libVerify = await Cc.call("/api/verify", { method: "POST", body: { email: "dual@test.dev", code: lCode } });
  ok("C: the library sign-in itself works as before", libVerify.status === 200 && (libVerify.cookie || "").includes("dl_session="));
  const prog2 = await Cc.call("/api/admin/eco/progress", { master: true });
  const dualAfter = prog2.body.progress.find(x => x.contributorId === "eco-dual");
  ok("C: the dual sequence completes at library_signed_in",
    dualAfter.steps.library_signed_in != null && dualAfter.completed === true && dualAfter.stalled === false);
} finally {
  srvC.kill();
}

console.log(`\nRESULT: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
