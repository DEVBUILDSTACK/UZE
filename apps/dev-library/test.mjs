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
import crypto from "node:crypto";
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

  const heroJpg = await fetch(B + "/hero.jpg");
  ok("hero.jpg served (hosted email imagery, public)", heroJpg.status === 200 && (heroJpg.headers.get("content-type") || "").includes("image/jpeg"));
  const heroGif = await fetch(B + "/hero.gif");
  ok("hero.gif served (hosted email imagery, public)", heroGif.status === 200 && (heroGif.headers.get("content-type") || "").includes("image/gif"));
  const swoop = await fetch(B + "/swoop.png");
  ok("swoop.png served (the Tri-Swoop email lockup, public)", swoop.status === 200 && (swoop.headers.get("content-type") || "").includes("image/png"));

  // Scope status on this host (James, 2026-11-19): signed-in devs
  // read the same report the Buildr Team surface renders.
  const ssAnon = await fetch(B + "/scope-status", { redirect: "manual" });
  ok("scope-status: signed-out redirects to the door", ssAnon.status === 302);
  const idx = await (await fetch(B + "/")).text();
  ok("macro FAQ carries the scope-status entry with both surfaces' doors",
    idx.includes("Scope status — where the work stands") && idx.includes('href="/scope-status"') &&
    idx.includes("buildr-eco.uzemarkets.com/scopes"));

  // ---- FAQ: one macro section on the page + a per-sample How-To
  // generated from each mock's catalog fields at render time ----
  const pageHtml = await (await fetch(B + "/")).text();
  const faqAt = pageHtml.indexOf('id="faq"');
  const faqSection = faqAt >= 0 ? pageHtml.slice(faqAt, pageHtml.indexOf("</section>", faqAt)) : "";
  ok("page footer: the three surfaces ride as quiet gray hover links above the ink band (James, 2026-11-19)",
    pageHtml.includes('class="brow"') && pageHtml.includes('>THE TALENT DESK</a>') && pageHtml.includes('>DEV LIBRARY</a>') &&
    pageHtml.includes('>BUILDER COLLABORATOR</a>') && pageHtml.includes('.brow a:hover { color:var(--ink);'));
  ok("FAQ: macro section served on the page, all eleven topics present",
    ["Access &amp; sign-in", "Browsing the catalog", "The samples", "Commenting &amp; suggesting",
     "Tracks &amp; expertise", "Engagements &amp; the money models", "Assessments (Scope 2)",
     "Access changes &amp; resets", "The two addresses — the UZE Dev Library &amp; UZE Buildr Team",
     "The two design surfaces — in pictures",
     "Contact — the desk"].every(t => faqSection.includes(t)));
  // The design-surface pictures (James, 2026-11-19): knowledge-base
  // material behind the session — never public like the hero.
  const diaAnon = await fetch(B + "/diagrams/human-design-surface.png", { redirect: "manual" });
  ok("diagrams: signed-out redirects to the door (OTP-gated, not public)", diaAnon.status === 302);
  ok("macro FAQ carries the pictures entry with both gated doors",
    faqSection.includes("The two design surfaces — in pictures") &&
    faqSection.includes('href="/diagrams/human-design-surface.png"') &&
    faqSection.includes('href="/diagrams/agentic-design-surface.png"'));
  ok("FAQ: macro section covers the second address per-address — UZE Buildr Team at buildr-eco.uzemarkets.com, its own sign-in, ecosystem first",
    faqSection.includes("buildr-eco.uzemarkets.com") && faqSection.includes("UZE Buildr Team") &&
    faqSection.includes("dev.uzemarkets.com") && faqSection.includes("Email me a sign-in code") &&
    faqSection.includes("One-time code") && faqSection.includes("Your other surface") &&
    faqSection.includes("Continue to the UZE Dev Partner Library") &&
    faqSection.includes("L2 Launchpad") && faqSection.includes("DealFi") && faqSection.includes("Fundio"));
  ok("FAQ: macro section names the desk as the contact and carries the exact-address sign-in rule",
    faqSection.includes("desk@uzemarkets.com") && faqSection.includes("character for character") &&
    faqSection.includes("no password"));
  ok("FAQ: macro section is the UZE Dev Partner FAQ, framed for this page and its dev partners (not a global UZE FAQ)",
    faqSection.includes("UZE Dev Partner FAQ") && faqSection.includes("For development partners") &&
    faqSection.includes("how this page") && !faqSection.includes("How-To &amp; FAQ"));
  const faqGenAt = pageHtml.indexOf("[faq-sample:start]");
  const faqGen = faqGenAt >= 0 ? pageHtml.slice(faqGenAt, pageHtml.indexOf("[faq-sample:end]")) : "";
  ok("FAQ: per-sample generator ships in the page and the catalog render calls it for every card",
    faqGen.includes("How-To — about this sample") && pageHtml.includes("sampleFaq(m)"));
  ok("FAQ: no internal naming in FAQ copy (macro section + per-sample generator)",
    !/reading room/i.test(faqSection) && !/reading room/i.test(faqGen));

  // ---- Design system: the page carries the approved v5 email's
  // tokens (lib/mailer.mjs renderHtml is the standard of record), so
  // the page and the email cannot silently drift apart ----
  ok("design: served page carries the email design tokens (ink, cream, tangerine, creamsicle, hairline, muted)",
    ["#1a1a1a", "#f5f2ee", "#ff6b00", "#FDEEE2", "#ddd5c9", "#6b655e"].every(t => pageHtml.includes(t)));
  ok("design: black pill buttons, Georgia serif display, reversed ink header band, creamsicle soft band",
    pageHtml.includes("border-radius:999px") && pageHtml.includes("Georgia") &&
    pageHtml.includes('class="band"') && pageHtml.includes('class="softband"'));
  ok("design: standard footer — ink band, © line, tangerine UZE linking to uzemarkets.com (no underline)",
    pageHtml.includes("<footer>") && pageHtml.includes("© 2026") &&
    pageHtml.includes('class="uze-link"') && pageHtml.includes('href="https://uzemarkets.com"'));
  ok("design: no off-palette status hues — feedback renders in the palette (ink + tangerine marker), never red/green",
    !pageHtml.includes("#b02a37") && !pageHtml.includes("#2e7d32"));
  ok("design: the wordmark never wraps — one line at phone width (nowrap + reduced band size under the mobile breakpoint)",
    pageHtml.includes("white-space:nowrap") && pageHtml.includes(".band h1{font-size:23px}"));
  ok("a11y: every select carries an accessible name (aria-label) — the design gate's select-name finding",
    (pageHtml.match(/<select\b[^>]*>/g) || []).length >= 9 &&
    (pageHtml.match(/<select\b[^>]*>/g) || []).every(t => /aria-label="[^"]+"/.test(t)));
  ok("a11y: heading order is sequential — h1 wordmark, h2 section titles, h3 subsections, no h4 skip — the design gate's heading-order finding",
    !pageHtml.includes("<h4") && pageHtml.includes("<h2") &&
    pageHtml.indexOf("<h1") < pageHtml.indexOf("<h2") && pageHtml.indexOf("<h2") < pageHtml.indexOf("<h3"));

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
  const ss = await fetch(B + "/scope-status", { headers: { cookie: ina } });
  const ssText = await ss.text();
  ok("scope-status: renders all four scopes + the drill-down, signed in",
    ss.status === 200 && ssText.includes("Scope 1") && ssText.includes("Scope 4") &&
    ssText.includes("Repository drill-down") && ssText.includes("10:29 PM EST"));

  // Two faces (James, 2026-11-19): the agent-acquisition sample
  // carries the venue app's human UI as its preview, session-gated.
  const pvAnon = await fetch(B + "/samples/venue-ticketing-ui.html", { redirect: "manual" });
  ok("sample preview: signed-out redirects to the door", pvAnon.status === 302);
  const pv = await fetch(B + "/samples/venue-ticketing-ui.html", { headers: { cookie: ina } });
  const pvText = await pv.text();
  ok("sample preview: the venue ticketing UI serves, signed in",
    pv.status === 200 && pvText.includes("Venue Ticketing"));
  ok("sample preview: no loose .html file for the static layer to expose",
    !fs.existsSync(path.join(ROOT, "samples", "venue-ticketing-ui.html")));
  // The classification layer (James, 2026-11-19): owners,
  // principal, advisor, dev internal vs external — master-only.
  ok("classifications without master -> 403", (await call("/api/admin/classifications")).status === 403);
  const cls = await call("/api/admin/classifications", { master: true });
  const byClass = (c) => (cls.body.people || []).filter(p => p.class === c).map(p => p.email);
  ok("classification layer: owners are the family three, principal is Jonathan alone, mentor is Bruno, advisor class empty, devs split internal/external",
    cls.status === 200 &&
    JSON.stringify(byClass("owner").sort()) === JSON.stringify(["dugan.hjd5@gmail.com", "dugan.x@gmail.com", "uze@uzemarkets.com"]) &&
    JSON.stringify(byClass("principal")) === JSON.stringify(["schmidtcommunications@gmail.com"]) &&
    JSON.stringify(byClass("advisor")) === JSON.stringify([]) &&
    JSON.stringify(byClass("mentor")) === JSON.stringify(["brunocsalles@gmail.com"]) &&
    JSON.stringify(byClass("dev-internal").sort()) === JSON.stringify(["rohansinglawork@gmail.com", "shradeshjain123@gmail.com"]) &&
    JSON.stringify(byClass("dev-external").sort()) === JSON.stringify(["dipanshuhappy@gmail.com", "mnithin1422@gmail.com"]) &&
    (cls.body.people.find(p => p.email === "uze@uzemarkets.com") || {}).greeting === "Hammond");

  // The advisor mock link: public by design (an advisor gets a
  // link, not a sign-in), human face only.
  const mk = await fetch(B + "/mock/venue-ticketing");
  ok("advisor mock link: the venue UI serves publicly at /mock/venue-ticketing",
    mk.status === 200 && (await mk.text()).includes("Venue Ticketing"));
  // Letters linkify bare URLs in the HTML part; the text part
  // keeps the raw URL.
  const { renderHtml: rH, renderText: rT } = await import("./lib/mailer.mjs");
  const probe = { kind: "letter", to: "x@example.com", subject: "s", body: "See it here: https://dev.uzemarkets.com/mock/venue-ticketing — that is the whole of it." };
  ok("letter body: a bare URL renders as a link in HTML, stays raw in text",
    rH(probe).includes('<a href="https://dev.uzemarkets.com/mock/venue-ticketing"') &&
    rT(probe).includes("https://dev.uzemarkets.com/mock/venue-ticketing") && !rT(probe).includes("<a href"));

  const ata = await call("/api/mock/agent-ticket-acquisition", { cookie: ina });
  ok("agent-acquisition sample carries its two faces (humanView + the verbal summary)",
    ata.status === 200 && ata.body.mock.humanView?.file === "venue-ticketing-ui.html" &&
    (ata.body.mock.facesNote || "").includes("two faces") && ata.body.mock.version === 2);
  const cat = await call("/api/catalog", { cookie: ina });
  ok("internal dev sees BOTH + INTERNAL_ONLY mocks", cat.body.mocks.length === 2);
  ok("FAQ: every catalog entry carries the fields its per-sample FAQ renders from",
    cat.body.mocks.length > 0 && cat.body.mocks.every(m =>
      !!m.title && !!m.topic && !!m.repo && !!m.date && m.version != null &&
      typeof m.description === "string" && Array.isArray(m.changelog)));
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

  const preRename = await call("/api/mock/agent-ticket-acquisition", { cookie: ina });
  await call("/api/admin/rename-mock", { method: "POST", master: true, body: { slug: "agent-ticket-acquisition", title: "Agent Ticket Acquisition — headless interface mock (renamed)", note: "title clarified in rehearsal" } });
  const redir = await call("/api/mock/agent-ticket-acquisition", { cookie: ina });
  ok("rename keeps slug, version bumps, changelog grows",
    redir.body.mock.version === preRename.body.mock.version + 1 &&
    redir.body.mock.changelog.length === preRename.body.mock.changelog.length + 1);

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

  // ---- L2L & Ecosystem Advisors: a roster distinct from the
  // Developer List — no tracks, no pairs, no grants, no sign-in ----
  const advAt = pageHtml.indexOf('id="advisors"');
  const advSection = advAt >= 0 ? pageHtml.slice(advAt, pageHtml.indexOf('id="engagements"', advAt)) : "";
  ok("advisors: section present in served page, after Master control",
    advSection.includes("L2L &amp; Ecosystem Advisors") && advAt > pageHtml.indexOf('id="master"'));
  ok("advisors: no internal naming in the section copy", !/reading room/i.test(advSection));
  ok("advisors without token -> 403", (await call("/api/admin/advisors")).status === 403);
  ok("orgs without token -> 403", (await call("/api/admin/orgs")).status === 403);
  const orgList = await call("/api/admin/orgs", adm);
  const orgByKey = Object.fromEntries((orgList.body.orgs || []).map(o => [o.key, o]));
  ok("orgs: the registry seeds four organizations, first-class (key, name, acronym)",
    orgList.status === 200 && (orgList.body.orgs || []).length === 4 &&
    orgByKey.DFI?.name === "DealFi" && orgByKey.DFI?.acronym === "DFI" &&
    orgByKey.FVC?.name === "Fundio" && orgByKey.FVC?.acronym === "FVC" &&
    orgByKey.UZE?.name === "UZEmarkets" && orgByKey.UZE?.acronym === "UZE" &&
    orgByKey.L2Launch?.name === "L2 Launchpad" && orgByKey.L2Launch?.acronym === "L2Launch");
  const advSeed = await call("/api/admin/advisors", adm);
  const seedAdvs = advSeed.body.advisors || [];
  const jon = seedAdvs.find(a => a.email === "schmidtcommunications@gmail.com");
  ok("advisors: seeded Jonathan Schmidt present — L2 Launchpad key, title, base, lane",
    advSeed.status === 200 && seedAdvs.length === 3 && !!jon && jon.name === "Jonathan Schmidt" &&
    jon.title === "Creative Intelligence Principal" && jon.org === "L2Launch" &&
    jon.base === "Santo Domingo, DR" && /design evaluation advisory/.test(jon.lane) && !!jon.id && !!jon.addedAt);
  const wcd = seedAdvs.find(a => a.email === "dugan.x@gmail.com");
  ok("advisors: seeded William Cumberland Dugan — Launch Principal, L2 Launchpad",
    !!wcd && wcd.name === "William Cumberland Dugan" && wcd.title === "Launch Principal" &&
    wcd.org === "L2Launch" && wcd.base === "DC–Baltimore" && /commercial art/.test(wcd.lane));
  const joey = seedAdvs.find(a => a.name === "Joey Hunter");
  ok("advisors: seeded Joey Hunter — Launch Principal with NO email on file (email optional)",
    !!joey && joey.title === "Launch Principal" && joey.org === "L2Launch" &&
    joey.base === "Fort Lauderdale" && /creator collaborator/.test(joey.lane) && !joey.email);
  const advAdd = await call("/api/admin/advisors", { method: "POST", master: true, body: {
    name: "Ada Advisor", email: "ada@test.dev", title: "Design Advisor", org: "L2Launch",
    base: "Fort Lauderdale, US", lane: "Motion graphics — design evaluation advisory" } });
  ok("advisors: add lands with the roster fields + org key", advAdd.status === 200 &&
    advAdd.body.advisor.email === "ada@test.dev" && advAdd.body.advisor.title === "Design Advisor" &&
    advAdd.body.advisor.org === "L2Launch" && !!advAdd.body.advisor.id && !!advAdd.body.advisor.addedAt);
  const advBadOrg = await call("/api/admin/advisors", { method: "POST", master: true, body: {
    name: "Ora Orgless", email: "ora@test.dev", title: "x", org: "NOPE", base: "z", lane: "w" } });
  ok("advisors: an org key outside the registry is rejected", advBadOrg.status === 500 && /unknown org/.test(advBadOrg.body.error || ""));
  const advDup = await call("/api/admin/advisors", { method: "POST", master: true, body: {
    name: "Ada Again", email: "ada@test.dev", title: "x", org: "UZE", base: "z", lane: "w" } });
  ok("advisors: duplicate email rejected (unique when present)", advDup.status === 500 && /already listed/.test(advDup.body.error || ""));
  const advNoMail = await call("/api/admin/advisors", { method: "POST", master: true, body: {
    name: "Noah Nomail", title: "Advisor", org: "UZE", base: "Miami, US", lane: "Ecosystem advisory" } });
  ok("advisors: add without an email lands (email optional), record carries null",
    advNoMail.status === 200 && !advNoMail.body.advisor.email && !!advNoMail.body.advisor.id);
  const advList2 = await call("/api/admin/advisors", adm);
  ok("advisors: list shows the three seeds + two added", advList2.body.advisors.length === 5);
  const advRemNoMail = await call("/api/admin/advisors/remove", { method: "POST", master: true, body: { id: advNoMail.body.advisor.id } });
  ok("advisors: an email-less advisor is removable by id", advRemNoMail.status === 200 &&
    advRemNoMail.body.advisor.name === "Noah Nomail");
  const advRem = await call("/api/admin/advisors/remove", { method: "POST", master: true, body: { email: "ada@test.dev" } });
  ok("advisors: remove by email lands", advRem.status === 200 && advRem.body.advisor.email === "ada@test.dev");
  const advList3 = await call("/api/admin/advisors", adm);
  ok("advisors: list back to the three seeds after removals", advList3.body.advisors.length === 3 &&
    advList3.body.advisors.some(a => a.email === "schmidtcommunications@gmail.com"));
  const advRemGone = await call("/api/admin/advisors/remove", { method: "POST", master: true, body: { email: "ada@test.dev" } });
  ok("advisors: removing an unlisted email is refused", advRemGone.status === 500 && /not found/.test(advRemGone.body.error || ""));
  const chronAdv = await call("/api/admin/chronicle", adm);
  const advTypes = chronAdv.body.entries.map(e => e.type);
  ok("advisors: add + remove emitted chronicle Events",
    advTypes.includes("advisor-added") && advTypes.includes("advisor-removed"));

  // ---- M1: Role × Realm taxonomy + dual-track placement ----
  await call("/api/admin/add-developer", { method: "POST", master: true, body: { name: "Abe Internal", email: "abe@test.dev", track: "INTERNAL_ONLY" } });
  const sx = await call("/api/admin/set-expertise", { method: "POST", master: true, body: { email: "xan@test.dev",
    pairs: [{ role: "SMART_CONTRACT_DEV", realm: "LIGHTNING" }, { role: "FULL_STACK_DEV", realm: "NEAR_AI" }] } });
  ok("M1 taxonomy: pairs set with PRIMARY/SECONDARY ranks", sx.status === 200 &&
    sx.body.developer.pairs.length === 2 && sx.body.developer.pairs[0].rank === "PRIMARY" &&
    sx.body.developer.pairs[1].rank === "SECONDARY" && sx.body.developer.pairs[0].role === "SMART_CONTRACT_DEV");
  ok("M1 taxonomy: realm list mirrors the pairs", JSON.stringify(sx.body.developer.expertise) === JSON.stringify(["LIGHTNING", "NEAR_AI"]));
  await call("/api/admin/set-expertise", { method: "POST", master: true, body: { email: "abe@test.dev",
    pairs: [{ role: "BLOCKCHAIN_DEV", realm: "CROSS_CHAIN" }] } });
  const six = await call("/api/admin/set-expertise", { method: "POST", master: true, body: { email: "xan@test.dev",
    pairs: [1, 2, 3, 4, 5, 6].map(i => ({ role: "OTHER_ROLE", realm: ["LIGHTNING", "NFT_WALLETS", "NEAR_AI", "CROSS_CHAIN", "LIGHTER", "OTHER_REALM"][i - 1] })) } });
  ok("M1 taxonomy: a 6th pair is rejected (I1 ceiling)", six.status === 500 && /5 pairs/.test(six.body.error || ""));
  const badRole = await call("/api/admin/set-expertise", { method: "POST", master: true, body: { email: "xan@test.dev", pairs: [{ role: "WIZARD", realm: "LIGHTNING" }] } });
  ok("M1 taxonomy: invalid role rejected", badRole.status === 500 && /invalid role/.test(badRole.body.error || ""));
  const badRealm = await call("/api/admin/set-expertise", { method: "POST", master: true, body: { email: "xan@test.dev", pairs: [{ role: "OTHER_ROLE", realm: "MARS" }] } });
  ok("M1 taxonomy: invalid realm rejected", badRealm.status === 500 && /invalid realm/.test(badRealm.body.error || ""));
  const dup = await call("/api/admin/set-expertise", { method: "POST", master: true, body: { email: "xan@test.dev",
    pairs: [{ role: "OTHER_ROLE", realm: "LIGHTNING" }, { role: "OTHER_ROLE", realm: "LIGHTNING" }] } });
  ok("M1 taxonomy: duplicate pair rejected", dup.status === 500 && /duplicate pair/.test(dup.body.error || ""));
  const xanAfter = (await call("/api/admin/developers", adm)).body.developers.find(d => d.email === "xan@test.dev");
  ok("M1 taxonomy: rejected writes leave the record untouched", xanAfter.pairs.length === 2 && xanAfter.pairs[0].role === "SMART_CONTRACT_DEV");
  const pairFilter = await call("/api/admin/developers?role=SMART_CONTRACT_DEV&realm=LIGHTNING", adm);
  ok("M1 filter: SMART_CONTRACT_DEV × LIGHTNING returns exactly the holders",
    pairFilter.body.developers.some(d => d.email === "xan@test.dev") &&
    !pairFilter.body.developers.some(d => ["abe@test.dev", "ina@test.dev"].includes(d.email)));
  const realmFilter = await call("/api/admin/developers?realm=CROSS_CHAIN", adm);
  ok("M1 filter: realm-only filter works", realmFilter.body.developers.some(d => d.email === "abe@test.dev") &&
    !realmFilter.body.developers.some(d => d.email === "xan@test.dev"));
  await call("/api/admin/set-track", { method: "POST", master: true, body: { email: "abe@test.dev", track: "EXTERNAL_PLACED" } });
  const abeBack = await call("/api/admin/set-track", { method: "POST", master: true, body: { email: "abe@test.dev", track: "INTERNAL_ONLY" } });
  ok("M1 tracks: transitions both directions, logged", abeBack.status === 200 && abeBack.body.developer.track === "INTERNAL_ONLY");

  const noFee = await call("/api/admin/engagements", { method: "POST", master: true, body: { title: "Solana dev", clientName: "Harbor Hotels (test)", service: "PLACE", deployment: "REMOTE", commercialModel: "PLACEMENT" } });
  ok("M1 engagement: PLACEMENT without a fee is rejected", noFee.status === 500 && /at least 1 month/.test(noFee.body.error || ""));
  const lowFee = await call("/api/admin/engagements", { method: "POST", master: true, body: { title: "Solana dev", clientName: "Harbor Hotels (test)", service: "PLACE", deployment: "REMOTE", commercialModel: "PLACEMENT", feeMonths: 0.5 } });
  ok("M1 engagement: PLACEMENT fee under 1 month is rejected", lowFee.status === 500);
  const blended = await call("/api/admin/engagements", { method: "POST", master: true, body: { title: "Solana dev", clientName: "Harbor Hotels (test)", service: "OUTSTAFF", deployment: "REMOTE", commercialModel: "OUTSTAFFING", feeMonths: 1 } });
  ok("M1 engagement: fee under OUTSTAFFING is rejected (models never blended)", blended.status === 500 && /PLACEMENT model only/.test(blended.body.error || ""));
  const opened = await call("/api/admin/engagements", { method: "POST", master: true, body: { title: "Solana smart-contract dev", clientName: "Harbor Hotels (test)", service: "PLACE", deployment: "REMOTE", commercialModel: "PLACEMENT", feeMonths: 1.5 } });
  ok("M1 engagement: opens in state OPEN (derived)", opened.status === 200 && opened.body.engagement.state === "OPEN" && opened.body.engagement.revealed === false);
  const engId = opened.body.engagement.id;
  const staffA = await call(`/api/admin/engagements/${engId}/staff`, { method: "POST", master: true, body: { email: "abe@test.dev" } });
  ok("M1 staffing: Track A (INTERNAL_ONLY) talent is never placed", staffA.status === 500 && /never placed/.test(staffA.body.error || ""));
  const staffed = await call(`/api/admin/engagements/${engId}/staff`, { method: "POST", master: true, body: { email: "xan@test.dev" } });
  ok("M1 staffing: desk staffs a Track B developer", staffed.status === 200 && staffed.body.engagement.state === "STAFFED");
  const blind1 = await call(`/api/admin/engagements/${engId}/client-view`, adm);
  const blindJson = JSON.stringify(blind1.body.view);
  ok("M1 blind view: skills visible, identity absent before signed+deposit",
    blind1.body.view.revealed === false && blind1.body.view.talent.pairs.length === 2 &&
    !blindJson.includes("Xan External") && !blindJson.includes("xan@test.dev"));
  const earlyDeposit = await call(`/api/admin/engagements/${engId}/deposit`, { method: "POST", master: true, body: { ref: "dep-early" } });
  ok("M1 lifecycle: deposit before signing is refused", earlyDeposit.status === 500 && /after the engagement is signed/.test(earlyDeposit.body.error || ""));
  const signed = await call(`/api/admin/engagements/${engId}/sign`, { method: "POST", master: true, body: { ref: "sig-001" } });
  ok("M1 lifecycle: signing moves STAFFED -> SIGNED", signed.status === 200 && signed.body.engagement.state === "SIGNED");
  const blind2 = await call(`/api/admin/engagements/${engId}/client-view`, adm);
  ok("M1 blind view: still blind after signing alone", blind2.body.view.revealed === false &&
    !JSON.stringify(blind2.body.view).includes("xan@test.dev"));
  const deposited = await call(`/api/admin/engagements/${engId}/deposit`, { method: "POST", master: true, body: { ref: "dep-001" } });
  ok("M1 lifecycle: deposit completes ACTIVE + revealed", deposited.status === 200 &&
    deposited.body.engagement.state === "ACTIVE" && deposited.body.engagement.revealed === true);
  const shown = await call(`/api/admin/engagements/${engId}/client-view`, adm);
  ok("M1 reveal: identity present only after signed + deposit",
    shown.body.view.revealed === true && shown.body.view.talent.name === "Xan External" && shown.body.view.talent.email === "xan@test.dev");
  const closed = await call(`/api/admin/engagements/${engId}/close`, { method: "POST", master: true, body: {} });
  ok("M1 lifecycle: close from ACTIVE -> CLOSED (derived)", closed.status === 200 && closed.body.engagement.state === "CLOSED");
  const staffClosed = await call(`/api/admin/engagements/${engId}/staff`, { method: "POST", master: true, body: { email: "xan@test.dev" } });
  ok("M1 lifecycle: a closed engagement cannot be staffed", staffClosed.status === 500);
  const opened2 = await call("/api/admin/engagements", { method: "POST", master: true, body: { title: "NEAR AI engineer (outstaffed)", clientName: "Harbor Hotels (test)", service: "OUTSTAFF", deployment: "HYBRID", commercialModel: "OUTSTAFFING" } });
  const eng2 = opened2.body.engagement.id;
  await call(`/api/admin/engagements/${eng2}/staff`, { method: "POST", master: true, body: { email: "xan@test.dev" } });
  const cancelled = await call(`/api/admin/engagements/${eng2}/cancel`, { method: "POST", master: true, body: { reason: "client paused" } });
  ok("M1 lifecycle: OUTSTAFFING engagement staffs and cancels clean", opened2.body.engagement.feeMonths === null &&
    cancelled.status === 200 && cancelled.body.engagement.state === "CANCELLED");
  const list = await call("/api/admin/engagements", adm);
  ok("M1 tracking: desk list tracks engagements end-to-end", list.body.engagements.length === 2 &&
    list.body.engagements.find(e => e.id === engId).history.length >= 5);
  const chron2 = await call("/api/admin/chronicle", adm);
  const types2 = chron2.body.entries.map(e => e.type);
  ok("M1 chronicle: every transition emitted an Event",
    ["expertise-set", "track-set", "engagement-opened", "engagement-staffed", "engagement-signed",
     "engagement-deposit", "engagement-revealed", "engagement-closed", "engagement-cancelled"].every(t => types2.includes(t)));
  // ---- P2: Assessment (Scope 2, separated track) — Sprint 1 ----
  // Structural provability: the publisher holds NO identity-store
  // read path — its imports are the document store (its own file),
  // the pinning adapters, and node:crypto. Nothing else.
  const pubSrc = fs.readFileSync(path.join(ROOT, "lib", "publisher.mjs"), "utf8");
  const pubImports = pubSrc.split("\n").filter(l => l.startsWith("import"));
  ok("P2 publisher: imports reach no identity module (gate/lifecycle/engagements/assessments)",
    pubImports.length >= 2 && pubImports.every(l => !/gate\.mjs|lifecycle|engagements|assessments|developers/.test(l)) &&
    pubImports.some(l => /store\.mjs/.test(l)) && pubImports.some(l => /pinning\.mjs/.test(l)));
  const pinning = await import("./lib/pinning.mjs");
  const inertErr = await pinning.filebasePinataAdapter.pin("{}").catch(e => e);
  ok("P2 pinning: Filebase/Pinata adapter is INERT without credentials (no network attempted)",
    inertErr instanceof Error && /INERT/.test(inertErr.message));

  for (const [name, email] of [["Cara Candidate", "cand1@test.dev"], ["Cand Two", "cand2@test.dev"],
      ["Cand Three", "cand3@test.dev"], ["Cand Four", "cand4@test.dev"], ["Cand Five", "cand5@test.dev"],
      ["Rex Retake", "rex@test.dev"]]) {
    await call("/api/admin/add-developer", { method: "POST", master: true, body: { name, email, track: "EXTERNAL_PLACED" } });
  }
  const respFor = (assessment, score) => Object.fromEntries(
    assessment.instrument.dimensions.map(d => [d.key, { score, evidence: "rehearsal evidence" }]));

  // P2-1 intake: keyed Role record; the taxonomy is the key space.
  const badPairCfg = await call("/api/admin/role-configs", { method: "POST", master: true, body: {
    employerRef: "Harbor Hotels (test)", vertical: "CRE_UNDERWRITING", title: "Analyst", pairs: [{ role: "WIZARD", realm: "OTHER_REALM" }] } });
  ok("P2-1 intake: invalid Role × Realm pair rejected (M1 taxonomy reused)", badPairCfg.status === 500 && /invalid role/.test(badPairCfg.body.error || ""));
  const noPairCfg = await call("/api/admin/role-configs", { method: "POST", master: true, body: {
    employerRef: "Harbor Hotels (test)", vertical: "CRE_UNDERWRITING", title: "Analyst", pairs: [] } });
  ok("P2-1 intake: a role record requires at least one keying pair", noPairCfg.status === 500 && /at least one Role/.test(noPairCfg.body.error || ""));
  const rcRes = await call("/api/admin/role-configs", { method: "POST", master: true, body: {
    employerRef: "Harbor Hotels (test)", vertical: "CRE_UNDERWRITING", title: "CRE Financial Underwriting Analyst",
    seniority: "senior", market: "India", engagementMode: "PLACE",
    skills: ["underwriting", "noi", "valuation", "financial statement analysis"],
    pairs: [{ role: "DATA_SCIENTIST", realm: "OTHER_REALM" }] } });
  ok("P2-1 intake: role configured end-to-end as a keyed Role record",
    rcRes.status === 200 && rcRes.body.roleConfig.pairs[0].rank === "PRIMARY" && rcRes.body.roleConfig.workHistoryRequired === true);
  const rcId = rcRes.body.roleConfig.id;

  // P2-2 generation: extraction -> selection -> slot-filling.
  const gen = await call(`/api/admin/role-configs/${rcId}/generate`, { method: "POST", master: true, body: {} });
  const asmId = gen.body.assessment.id;
  ok("P2-2 generator: CRE role selects the underwriting template, DealFi screens included",
    gen.status === 200 && gen.body.assessment.templateId === "tpl_cre_underwriting_analyst_v1" &&
    gen.body.assessment.instrument.dimensions.some(d => d.key === "dealfi_acquisition_screens") &&
    gen.body.assessment.instrument.screens.length === 4 && gen.body.assessment.state === "GENERATED");
  ok("P2-2 generator: slot-filling parameterizes prompts from the role (no authored instrument)",
    gen.body.assessment.instrument.dimensions[0].prompt.includes("CRE Financial Underwriting Analyst") &&
    !gen.body.assessment.instrument.dimensions[0].prompt.includes("{title}"));

  // P2-3 gates: order, human-only, approver registry.
  const asmView = async () => (await call(`/api/admin/assessments/${asmId}`, adm)).body.assessment;
  const earlyRun = await call(`/api/admin/assessments/${asmId}/runs`, { method: "POST", master: true, body: { talentEmail: "cand1@test.dev", responses: respFor(gen.body.assessment, 90) } });
  ok("P2-3 gates: a run before both gates is refused", earlyRun.status === 500 && /nothing runs before both gates/.test(earlyRun.body.error || ""));
  const g2early = await call(`/api/admin/assessments/${asmId}/gate2`, { method: "POST", master: true, body: { signer: { name: "Approver One", kind: "human" }, viaMasterTest: true } });
  ok("P2-3 gates: Gate 2 before Gate 1 is refused", g2early.status === 500 && /cannot precede Gate 1/.test(g2early.body.error || ""));
  const g1agent = await call(`/api/admin/assessments/${asmId}/gate1`, { method: "POST", master: true, body: { signer: { name: "Agent Smith", kind: "agent" } } });
  ok("P2-3 gates: an agent identity cannot sign Gate 1", g1agent.status === 500 && /agent cannot sign/.test(g1agent.body.error || ""));
  const g1ret = await call(`/api/admin/assessments/${asmId}/gate1`, { method: "POST", master: true, body: { signer: { name: "Employer One", kind: "human" }, decision: "return" } });
  ok("P2-3 gates: a Gate 1 return sends the instrument back (RETURNED)", g1ret.status === 200 && g1ret.body.assessment.state === "RETURNED");
  const regen = await call(`/api/admin/assessments/${asmId}/regenerate`, { method: "POST", master: true, body: {} });
  ok("P2-3 gates: regeneration clears the gate facts, history keeps them",
    regen.status === 200 && regen.body.assessment.state === "GENERATED" && regen.body.assessment.instrumentVersion === 2 &&
    regen.body.assessment.gate1 === null && regen.body.assessment.history.some(h => h.event === "assessment-gate1-returned"));
  const g1 = await call(`/api/admin/assessments/${asmId}/gate1`, { method: "POST", master: true, body: { signer: { name: "Employer One", kind: "human" } } });
  ok("P2-3 gates: Gate 1 human signature lands (GATE1_SIGNED)", g1.status === 200 && g1.body.assessment.state === "GATE1_SIGNED");
  const g2noreg = await call(`/api/admin/assessments/${asmId}/gate2`, { method: "POST", master: true, body: { signer: { name: "Approver One", kind: "human" } } });
  ok("P2-3 gates: Gate 2 refuses while no approver of record is configured (ruling 6 unsettled)",
    g2noreg.status === 500 && /no approver of record is configured/.test(g2noreg.body.error || ""));
  const g2 = await call(`/api/admin/assessments/${asmId}/gate2`, { method: "POST", master: true, body: { signer: { name: "Approver One", kind: "human" }, viaMasterTest: true } });
  ok("P2-3 gates: master test/proof context signs Gate 2, basis recorded",
    g2.status === 200 && g2.body.assessment.state === "APPROVED" && g2.body.assessment.gate2.basis === "master-test");
  // The registry path (second seed vertical): configured approver only.
  const hospCfg = await call("/api/admin/role-configs", { method: "POST", master: true, body: {
    employerRef: "Harbor Hotels (test)", vertical: "HOSPITALITY", title: "Front Desk Agent",
    seniority: "mid", market: "India", skills: ["front desk", "guest service", "pms"],
    pairs: [{ role: "TALENT_HR_SPECIALIST", realm: "OTHER_REALM" }] } });
  const hospGen = await call(`/api/admin/role-configs/${hospCfg.body.roleConfig.id}/generate`, { method: "POST", master: true, body: {} });
  const hospId = hospGen.body.assessment.id;
  ok("P2-2 generator: hospitality role selects the hospitality template",
    hospGen.body.assessment.templateId === "tpl_hospitality_front_desk_v1");
  await call("/api/admin/approvers", { method: "POST", master: true, body: { vertical: "HOSPITALITY", names: ["Hana Approver"] } });
  await call(`/api/admin/assessments/${hospId}/gate1`, { method: "POST", master: true, body: { signer: { name: "Employer One", kind: "human" } } });
  const g2wrong = await call(`/api/admin/assessments/${hospId}/gate2`, { method: "POST", master: true, body: { signer: { name: "Wrong Person", kind: "human" }, viaMasterTest: true } });
  ok("P2-3 gates: a configured registry binds Gate 2 to the named approver (master-test does not override it)",
    g2wrong.status === 500 && /not the approver of record/.test(g2wrong.body.error || ""));
  const g2reg = await call(`/api/admin/assessments/${hospId}/gate2`, { method: "POST", master: true, body: { signer: { name: "Hana Approver", kind: "human" } } });
  ok("P2-3 gates: the approver of record signs Gate 2 (basis: registry)",
    g2reg.status === 200 && g2reg.body.assessment.state === "APPROVED" && g2reg.body.assessment.gate2.basis === "registry");

  // P2-4 runs + scoring center.
  const asmFull = await asmView();
  const runFor = async (email, score, takenAt) => call(`/api/admin/assessments/${asmId}/runs`,
    { method: "POST", master: true, body: { talentEmail: email, responses: respFor(asmFull, score), ...(takenAt ? { takenAt } : {}) } });
  const r1 = await runFor("cand1@test.dev", 92);
  ok("P2-4 scoring: a run grades end-to-end, keyed to the PRIMARY pair, validity as gap acknowledgment",
    r1.status === 200 && r1.body.run.score === 92 && r1.body.run.gradeBand === "90-100" &&
    r1.body.run.humanReviewFlag === false && r1.body.run.pair.role === "DATA_SCIENTIST" && r1.body.run.pair.realm === "OTHER_REALM" &&
    r1.body.run.validity.form === "gap" && r1.body.run.reviewThreshold === 70 && r1.body.run.talentDid.startsWith("did:uze:talent_"));
  const run1Id = r1.body.run.id, cand1Did = r1.body.run.talentDid;
  const r2 = await runFor("cand2@test.dev", 73);
  ok("P2-4 scoring: a borderline result raises the human-review flag at the stated threshold",
    r2.status === 200 && r2.body.run.score === 73 && r2.body.run.humanReviewFlag === true);
  for (const [email, score] of [["cand3@test.dev", 85], ["cand4@test.dev", 85], ["cand5@test.dev", 85]]) await runFor(email, score);
  // Retake policy: window refusal, then two retakes, then the ceiling.
  const rex1 = await runFor("rex@test.dev", 60, "2025-01-05");
  ok("P2-4 retakes: the first run lands", rex1.status === 200);
  const rexEarly = await runFor("rex@test.dev", 65, "2025-01-20");
  ok("P2-4 retakes: a retake inside six months is refused and logged",
    rexEarly.status === 500 && /one retake per six months/.test(rexEarly.body.error || ""));
  ok("P2-4 retakes: retake 1 after the window lands", (await runFor("rex@test.dev", 66, "2025-08-01")).status === 200);
  ok("P2-4 retakes: retake 2 after the window lands", (await runFor("rex@test.dev", 67, "2026-03-01")).status === 200);
  const rexThird = await runFor("rex@test.dev", 68, "2026-09-15");
  ok("P2-4 retakes: a third retake is refused by the policy (maximum two total)",
    rexThird.status === 500 && /maximum two retakes total/.test(rexThird.body.error || ""));

  // P2-5/P2-6 hooks: Path A quote + Path B attachment + disclosure.
  const runsOf = async () => (await call(`/api/admin/assessments/${asmId}`, adm)).body.runs;
  const cand3Run = (await runsOf()).find(r => r.talentEmail === "cand3@test.dev");
  const quote = await call(`/api/admin/runs/${cand3Run.id}/quote`, { method: "POST", master: true, body: { market: "India", laborRate: 1000, markupPct: 20 } });
  ok("P2-6 quote: Path A composes from the band of record and locks (1000 @ 20% -> 1200)",
    quote.status === 200 && quote.body.quote.billedRate === 1200 && !!quote.body.quote.lockedAt);
  const quoteOut = await call(`/api/admin/runs/${cand3Run.id}/quote`, { method: "POST", master: true, body: { market: "India", laborRate: 1000, markupPct: 30 } });
  ok("P2-6 quote: a markup outside the band of record is refused", quoteOut.status === 500 && /outside the band of record/.test(quoteOut.body.error || ""));
  const quoteNone = await call(`/api/admin/runs/${cand3Run.id}/quote`, { method: "POST", master: true, body: { market: "Atlantis", laborRate: 1000 } });
  ok("P2-6 quote: a market with no band of record is refused, never invented (ruling 5)",
    quoteNone.status === 500 && /no markup band of record/.test(quoteNone.body.error || ""));

  // P2-6 (publisher): min-anonymity refusal on a lone cohort first.
  const hospRun = await call(`/api/admin/assessments/${hospId}/runs`, { method: "POST", master: true,
    body: { talentEmail: "cand1@test.dev", responses: respFor(hospGen.body.assessment, 80) } });
  const lonePub = await call(`/api/admin/runs/${hospRun.body.run.id}/publish`, { method: "POST", master: true, body: {} });
  ok("P2 publisher: a cohort below the minimum anonymity set (5) does not publish",
    lonePub.status === 500 && /below the minimum anonymity set/.test(lonePub.body.error || ""));
  const pub = await call(`/api/admin/runs/${run1Id}/publish`, { method: "POST", master: true, body: {} });
  const art = pub.body.publication?.artifact || {};
  const artJson = JSON.stringify(art);
  ok("P2 publisher: the CRE outcome publishes — content-addressed, pseudonymous, banded",
    pub.status === 200 && pub.body.publication.cid.startsWith("sha256:") && pub.body.publication.adapter === "local-sha256" &&
    art.pseudonym?.startsWith("talent-") && art.gradeBand === "90-100" && !("score" in art));
  ok("P2 publisher: redaction holds — no talent name, no email, no company name in the artifact",
    !artJson.includes("Cara Candidate") && !artJson.includes("cand1@test.dev") && !artJson.includes("Harbor Hotels"));
  ok("P2 publisher: validity is stated only in the enforced form (gap acknowledgment)",
    typeof art.validity === "string" && art.validity.startsWith("gap acknowledged:"));
  const pubList = await call("/api/publications");
  ok("P2 viewer: the public viewer serves the redacted copy without any session",
    pubList.status === 200 && pubList.body.publications.some(p => p.id === pub.body.publication.id) &&
    !JSON.stringify(pubList.body).includes("cand1@test.dev"));

  // Disclosure through the M1 machinery: pseudonym before signing,
  // identity at engagement + deposit.
  const p2eng = await call("/api/admin/engagements", { method: "POST", master: true, body: {
    title: "Underwriting analyst (assessed)", clientName: "Harbor Hotels (test)", service: "PLACE",
    deployment: "REMOTE", commercialModel: "PLACEMENT", feeMonths: 1 } });
  const p2engId = p2eng.body.engagement.id;
  await call(`/api/admin/engagements/${p2engId}/staff`, { method: "POST", master: true, body: { email: "xan@test.dev" } });
  await call(`/api/admin/runs/${run1Id}/attach-engagement`, { method: "POST", master: true, body: { engagementId: p2engId } });
  const outBlind = await call(`/api/admin/engagements/${p2engId}/assessment-outcomes`, adm);
  const blindOutcomeJson = JSON.stringify(outBlind.body.outcomes);
  ok("P2 disclosure: outcome under pseudonym before signing — identity absent",
    outBlind.body.outcomes.length === 1 && outBlind.body.outcomes[0].revealed === false &&
    outBlind.body.outcomes[0].talent === null && outBlind.body.outcomes[0].pseudonym.startsWith("talent-") &&
    !blindOutcomeJson.includes("Cara Candidate") && !blindOutcomeJson.includes("cand1@test.dev"));
  ok("P2 disclosure: the engagement-scoped pseudonym differs from the assessment-scoped one",
    outBlind.body.outcomes[0].pseudonym !== art.pseudonym);
  await call(`/api/admin/engagements/${p2engId}/sign`, { method: "POST", master: true, body: { ref: "sig-p2" } });
  await call(`/api/admin/engagements/${p2engId}/deposit`, { method: "POST", master: true, body: { ref: "dep-p2" } });
  const outShown = await call(`/api/admin/engagements/${p2engId}/assessment-outcomes`, adm);
  ok("P2 disclosure: identity revealed at engagement + deposit, and not before",
    outShown.body.outcomes[0].revealed === true && outShown.body.outcomes[0].talent.name === "Cara Candidate" &&
    outShown.body.outcomes[0].talent.email === "cand1@test.dev");

  // The score seam (MCP score_assessment reads through this):
  const scored = await call(`/api/admin/assessments/${asmId}/score-by-talent`, { method: "POST", master: true, body: { talentDid: cand1Did } });
  ok("P2 seam: score-by-talent returns the scored record for a gate-passed assessment",
    scored.status === 200 && scored.body.score.score === 92 && scored.body.score.talentDid === cand1Did);
  const ungatedCfg = await call("/api/admin/role-configs", { method: "POST", master: true, body: {
    employerRef: "Harbor Hotels (test)", vertical: "CRE_UNDERWRITING", title: "Junior Analyst",
    skills: ["noi"], pairs: [{ role: "DATA_SCIENTIST", realm: "OTHER_REALM" }] } });
  const ungatedGen = await call(`/api/admin/role-configs/${ungatedCfg.body.roleConfig.id}/generate`, { method: "POST", master: true, body: {} });
  const ungatedScore = await call(`/api/admin/assessments/${ungatedGen.body.assessment.id}/score-by-talent`,
    { method: "POST", master: true, body: { talentDid: cand1Did } });
  ok("P2 seam: score-by-talent refuses against a non-gate-passed record",
    ungatedScore.status === 500 && /gates not passed/.test(ungatedScore.body.error || ""));

  const chron3 = await call("/api/admin/chronicle", adm);
  const types3 = chron3.body.entries.map(e => e.type);
  ok("P2 chronicle: every transition emitted an Event",
    ["role-config-created", "assessment-generated", "assessment-gate1-signed", "assessment-gate2-signed",
     "assessment-gate1-returned", "assessment-regenerated", "assessment-approver-set", "assessment-run-scored",
     "assessment-retake-refused", "assessment-quote-locked", "assessment-attached-engagement",
     "assessment-outcome-published"].every(t => types3.includes(t)));

  if (process.env.DATABASE_URL || process.env.POSTGRES_URL) {
    // DB mode: the typed tables carry the taxonomy + engagement facts.
    // The write-through flush completes after each response is sent
    // (the server wrapper awaits it post-response), and the persist
    // chain re-writes whole documents — so poll for the rows, the
    // same discipline phase 2 uses for the mail drain.
    const pg = (await import("pg")).default;
    const pool = new pg.Pool({ connectionString: process.env.DATABASE_URL || process.env.POSTGRES_URL });
    const pollRows = async (sql, params, want) => {
      const t0 = Date.now();
      while (Date.now() - t0 < 20000) {
        const { rows } = await pool.query(sql, params);
        if (want(rows)) return rows;
        await new Promise(r => setTimeout(r, 150));
      }
      return (await pool.query(sql, params)).rows;
    };
    const xp = await pollRows("SELECT role, realm, rank FROM developer_expertise WHERE email='xan@test.dev' ORDER BY ordinal", [], r => r.length === 2);
    ok("M1 DB: developer_expertise rows written through (2 pairs, PRIMARY first)",
      xp.length === 2 && xp[0].role === "SMART_CONTRACT_DEV" && xp[0].rank === "PRIMARY");
    const er = await pollRows("SELECT commercial_model, fee_months, signed_at IS NOT NULL AS s, deposit_at IS NOT NULL AS d FROM engagement WHERE id=$1", [engId], r => r.length === 1);
    ok("M1 DB: engagement row carries fee + signed + deposit facts",
      er.length === 1 && er[0].commercial_model === "PLACEMENT" && Number(er[0].fee_months) === 1.5 && er[0].s && er[0].d);
    const rcRow = await pollRows("SELECT vertical FROM role_config WHERE id=$1", [rcId], r => r.length === 1);
    ok("P2 DB: role_config row written through", rcRow.length === 1 && rcRow[0].vertical === "CRE_UNDERWRITING");
    const aRow = await pollRows("SELECT gate1_at IS NOT NULL AS g1, gate2_at IS NOT NULL AS g2 FROM assessment WHERE id=$1", [asmId], r => r.length === 1 && r[0].g1 && r[0].g2);
    ok("P2 DB: assessment row carries both gate facts (gate2_at set only with gate1_at)",
      aRow.length === 1 && aRow[0].g1 && aRow[0].g2);
    const runRows = await pollRows("SELECT count(*)::int AS n FROM assessment_run WHERE assessment_id=$1", [asmId], r => r[0].n >= 8);
    ok("P2 DB: assessment_run rows written through (cohort + retakes)", runRows[0].n >= 8);
    const pubRow = await pollRows("SELECT cid, pseudonym FROM publication WHERE id=$1", [pub.body.publication.id], r => r.length === 1);
    ok("P2 DB: publication row carries the content address + pseudonym, no identity columns",
      pubRow.length === 1 && pubRow[0].cid === pub.body.publication.cid && pubRow[0].pseudonym.startsWith("talent-"));
    const advRow = await pollRows("SELECT name, title, org, base FROM advisor WHERE email='schmidtcommunications@gmail.com'", [], r => r.length === 1);
    ok("advisors DB: seeded advisor row written through with the roster fields (org carries the registry key)",
      advRow.length === 1 && advRow[0].name === "Jonathan Schmidt" &&
      advRow[0].title === "Creative Intelligence Principal" && advRow[0].org === "L2Launch" && advRow[0].base === "Santo Domingo, DR");
    const joeyRow = await pollRows("SELECT email, org FROM advisor WHERE name='Joey Hunter'", [], r => r.length === 1);
    ok("advisors DB: the email-less seed row carries a NULL email (unique only when present)",
      joeyRow.length === 1 && joeyRow[0].email === null && joeyRow[0].org === "L2Launch");
    const orgRowsDb = await pollRows("SELECT key, name FROM org ORDER BY position", [], r => r.length === 4);
    ok("orgs DB: the registry is written through (four organizations)",
      orgRowsDb.length === 4 && orgRowsDb[0].key === "DFI" && orgRowsDb[3].name === "L2 Launchpad");
    const advGone = await pollRows("SELECT count(*)::int AS n FROM advisor WHERE email='ada@test.dev'", [], r => r[0].n === 0);
    ok("advisors DB: removal deletes the row (no resurrection on hydration)", advGone[0].n === 0);
    await pool.end();
  }
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
  RESEND_API_KEY: "test-key", RESEND_API_URL: `http://127.0.0.1:${stub.address().port}/emails`,
  RESEND_WEBHOOK_SECRET: "whsec_" + Buffer.from("devlib-webhook-test").toString("base64") };
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
    !!inv && inv.html.includes("Dear Development Partner,") && inv.text.includes("Dear Development Partner,") && inv.html.includes("#ff6b00") &&
    inv.html.includes("dev.uzemarkets.com") && inv.html.includes("The UZE Markets Desk") &&
    inv.text.includes("The UZE Markets Desk"));
  ok("house CTAs sit above the signature, logo underneath (James's layout rule)",
    !!inv && inv.html.includes("x.com/UZEmarkets_fyi") && inv.html.includes("podcast.uzemarkets.com") &&
    inv.html.indexOf("UZEmarkets_fyi") < inv.html.indexOf("The UZE Markets Desk") &&
    inv.html.indexOf("The UZE Markets Desk") < inv.html.indexOf("font-size:22px") &&
    inv.text.includes("UZEmarkets_fyi"));
  ok("design system v3: table layout, lang, preheader, dark-mode pack, hosted hero, <95KB",
    !!inv && inv.html.includes('role="presentation"') && inv.html.includes('lang="en"') &&
    inv.html.includes("Your seat in the UZE Dev Library is ready") &&
    inv.html.includes("prefers-color-scheme") && inv.html.includes('name="color-scheme"') &&
    inv.html.includes("https://dev.uzemarkets.com/hero.gif") && inv.html.includes('alt="The UZE Dev Library —') &&
    Buffer.byteLength(inv.html) < 95 * 1024);
  ok("button row: X / Instagram / podcast pills all present, all black (Maple remodel)",
    !!inv && inv.html.includes("Follow us on X") && inv.html.includes("https://instagram.com/uzemarkets") &&
    inv.html.includes("Listen to the podcast") && inv.html.includes('bgcolor="#1a1a1a"') &&
    !inv.html.includes("#b02a8a"));
  ok("lower half in the Maple language: black Enter pill, creamsicle banner, serif headline, no varied colors",
    !!inv && inv.html.includes("Enter the Dev Library") &&
    inv.html.includes("background-color:#1a1a1a;color:#ffffff") &&
    inv.html.includes("#FDEEE2") && inv.html.includes("Georgia") && inv.html.includes("Join the conversation") &&
    !inv.html.includes("#b02a8a") && !inv.html.includes("#25D366"));
  ok("WhatsApp band is the bottom-most card element (after the logo block), black not green",
    !!inv && inv.html.includes("Join us on WhatsApp") && !inv.html.includes("#25D366") &&
    inv.html.indexOf("Join us on WhatsApp") > inv.html.indexOf("font-size:22px"));
  ok("naming rule: no external copy says 'reading room' (James, 2026-11-18)",
    !!inv && !/reading room/i.test(inv.html) && !/reading room/i.test(inv.text) &&
    inv.html.includes(">DEV LIBRARY<") && inv.html.includes(">THE TALENT DESK</a>") && inv.html.includes(">DEV LIBRARY</a>") && inv.html.includes(">BUILDER COLLABORATOR</a>") &&
    inv.html.includes("href=\"https://buildr-eco.uzemarkets.com\"") && !inv.html.includes("desk@uzemarkets.com</a> · <a href=\"https://dev.uzemarkets.com\"") &&
    inv.html.includes("Sign-in is by an"));
  const invLog = await waitFor(() => { const e = comms2().find((s) => s.kind === "invitation" && s.to === "mia@test.dev"); return e && e.status === "sent" ? e : null; });
  ok("log marks the invitation sent with provider id", !!invLog && String(invLog.providerId).startsWith("stub-msg-"));
  ok("BCC rule (James, 2026-11-19): every send BCCs jsondealzapp@gmail.com",
    received.length > 0 && received.every(m => Array.isArray(m.bcc) && m.bcc.includes("jsondealzapp@gmail.com")));

  await call2("/api/request-code", { method: "POST", body: { email: "mia@test.dev" } });
  const otpMail = await waitFor(() => received.filter((x) => (x.subject || "").includes("sign-in code")).pop());
  const delivered = otpMail && otpMail.text.match(/sign-in code for the UZE Dev Library is (\d{6})/)[1];
  ok("sign-in code SENT at the request event", !!delivered);
  ok("code email is branded and shows the code large",
    !!delivered && otpMail.html.includes(delivered) && otpMail.html.includes("Hello Mia,") && otpMail.text.includes("Hello Mia,"));
  ok("code email stays lean: no hero, no button row, no banners",
    !!delivered && !otpMail.html.includes("hero.gif") && !otpMail.html.includes("#25D366") &&
    !otpMail.html.includes("Listen to the podcast") && !otpMail.html.includes("Join the conversation"));
  const v = await call2("/api/verify", { method: "POST", body: { email: "mia@test.dev", code: delivered } });
  ok("the delivered code signs in", v.status === 200 && !!v.cookie);

  // OTP sends synchronously (2026-11-19 fix): the code's send is
  // attempted inside the request-code request and its outcome
  // persisted before the response returns — the general queue can
  // no longer starve it. Proof: with a fresh developer, once the
  // grant's own drain has settled (invitation marked sent), the
  // comms log ALREADY shows the OTP entry sent, with the provider
  // id, at the moment the request-code response returns — this
  // read is deliberately NOT polled.
  await call2("/api/admin/add-developer", { method: "POST", master: true, body: { name: "Ola Ontime", email: "ola@test.dev", track: "EITHER", expertise: ["NEAR_AI"] } });
  await call2("/api/admin/grant-reading-room", { method: "POST", master: true, body: { email: "ola@test.dev" } });
  await waitFor(() => { const e = comms2().find((s) => s.kind === "invitation" && s.to === "ola@test.dev"); return e && e.status === "sent" ? e : null; }, 10000);
  await call2("/api/request-code", { method: "POST", body: { email: "ola@test.dev" } });
  const olaOtp = comms2().filter((s) => s.kind === "otp" && s.to === "ola@test.dev").pop();
  ok("OTP attempted in-request: log shows sent + provider id when the response returns",
    !!olaOtp && olaOtp.status === "sent" && String(olaOtp.providerId || "").startsWith("stub-msg-"));

  await call2("/api/admin/revoke-all", { method: "POST", master: true, body: { email: "mia@test.dev", reason: "stub failure rehearsal" } });
  const revLog = await waitFor(() => { const e = comms2().find((s) => s.kind === "revocation" && s.to === "mia@test.dev"); return e && e.attempts >= 1 ? e : null; });
  ok("failed send stays queued, attempt + error recorded (never dropped)",
    !!revLog && revLog.status === "queued" && !!revLog.lastError);
  ok("failed send records the mail API status + response body (diagnosable evidence)",
    !!revLog && /mail API 500/.test(revLog.lastError || "") && /stub failure/.test(revLog.lastError || ""));

  // Phase 3 — delivery webhooks: a Svix-signed delivered event lands
  // on the comms entry it belongs to; a replay is deduped; a forged
  // signature is refused.
  const whPost = async (payload, { id = "msg_" + Math.random().toString(36).slice(2),
      ts = String(Math.floor(Date.now() / 1000)), bad = false } = {}) => {
    const raw = JSON.stringify(payload);
    const sig = crypto.createHmac("sha256", Buffer.from("devlib-webhook-test"))
      .update(`${id}.${ts}.${raw}`).digest("base64");
    const r = await fetch(B2 + "/api/resend-webhook", { method: "POST",
      headers: { "content-type": "application/json", "svix-id": id, "svix-timestamp": ts,
        "svix-signature": `v1,${bad ? "AAAA" + sig.slice(4) : sig}` }, body: raw });
    return { status: r.status, id };
  };
  const wh = await whPost({ type: "email.delivered", created_at: new Date().toISOString(),
    data: { email_id: invLog.providerId, to: ["mia@test.dev"] } });
  const invAfter = await waitFor(() => { const e = comms2().find((s) => s.kind === "invitation" && s.to === "mia@test.dev"); return e && e.delivery && e.delivery.status === "delivered" ? e : null; });
  ok("webhook: delivered event recorded on the comms entry", wh.status === 200 && !!invAfter);
  const replay = await whPost({ type: "email.delivered", created_at: new Date().toISOString(),
    data: { email_id: invLog.providerId } }, { id: wh.id });
  const invReplay = comms2().find((s) => s.kind === "invitation" && s.to === "mia@test.dev");
  ok("webhook: duplicate delivery deduped on svix id", replay.status === 200 && invReplay.delivery.events.length === 1);
  const forged = await whPost({ type: "email.delivered", created_at: new Date().toISOString(),
    data: { email_id: invLog.providerId } }, { bad: true });
  ok("webhook: forged signature rejected", forged.status === 401);
} finally {
  srv2.kill();
  stub.close();
  fs.rmSync(tmp2, { recursive: true, force: true });
}
// ---- Phase 2b: drain hygiene against a seeded, clogged log ----
// The 2026-11-18/19 production failure, rehearsed: the log holds
// duplicate snapshots of the same entry (the DB write-through
// stores one row per state), stale "queued" snapshots of mail that
// already sent, and more queued entries than one drain may attempt.
// The drain must dedupe (latest state wins), never re-send a stale
// snapshot, take OTP entries before older invitations, cap its
// attempts, and record a timeout distinctly. JSON mode only: in DB
// mode the server hydrates its working set from the shared test DB,
// so a file-seeded log cannot be staged there — the same behaviors
// are covered here, and DB-mode hydration applies the same
// latest-wins dedupe on its read path (lib/store-pg.mjs).
if (process.env.DATABASE_URL || process.env.POSTGRES_URL) {
  console.log("SKIP phase 2b: seeded-log rehearsal runs in JSON mode (DB mode hydrates from the shared test DB)");
} else {
  const received3 = [];
  const stub3 = http.createServer((req, res) => {
    let s = ""; req.on("data", (c) => (s += c)); req.on("end", () => {
      const payload = JSON.parse(s || "{}");
      received3.push(payload);
      if ((payload.subject || "").includes("hang")) {
        // Answer long after the mailer's 8s abort: the send must be
        // recorded as a timeout, distinctly.
        setTimeout(() => { try {
          res.writeHead(200, { "content-type": "application/json" });
          res.end(JSON.stringify({ id: "stub3-late" }));
        } catch { /* the caller long since aborted */ } }, 12000);
        return;
      }
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ id: "stub3-msg-" + received3.length }));
    });
  });
  await new Promise((r) => stub3.listen(0, "127.0.0.1", r));
  const tmp3 = fs.mkdtempSync(path.join(os.tmpdir(), "devlib-test3-"));
  fs.cpSync(path.join(ROOT, "data"), tmp3, { recursive: true });
  const seedEntry = (id, at, kind, subject, extra = {}) => ({ id, at, from: "desk@uzemarkets.com",
    to: `${id}@test.dev`, kind, subject, status: "queued",
    body: kind === "otp" ? "Your one-time sign-in code for the UZE Dev Library is 123456. It expires in 15 minutes." : "Seeded rehearsal entry.", ...extra });
  const T = (h, m = 0) => `2026-11-18T${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:00.000Z`;
  fs.writeFileSync(path.join(tmp3, "comms-log.json"), JSON.stringify({ version: 1, sender: "desk@uzemarkets.com", sends: [
    // dup1: a queued snapshot followed by its sent snapshot — the
    // stale queued row must never be sent again.
    seedEntry("dup1", T(10), "invitation", "seed-dup1"),
    seedEntry("dup1", T(10), "invitation", "seed-dup1", { status: "sent", providerId: "stub-old-1", sentAt: T(10, 1) }),
    // dup2: the same queued OTP snapshot twice — send exactly once.
    seedEntry("dup2", T(9), "otp", "seed-otp-dup"),
    seedEntry("dup2", T(9), "otp", "seed-otp-dup"),
    seedEntry("old1", T(10, 30), "invitation", "seed-inv-old1"),
    seedEntry("old2", T(11, 30), "invitation", "seed-inv-old2"),
    seedEntry("otpnew", T(12), "otp", "seed-otp-new"),
    seedEntry("cap1", T(13, 0), "invitation", "seed-cap1"),
    seedEntry("cap2", T(13, 1), "invitation", "seed-cap2"),
    seedEntry("cap3", T(13, 2), "invitation", "seed-cap3"),
    seedEntry("cap4", T(13, 3), "invitation", "seed-cap4"),
    seedEntry("cap5", T(13, 4), "invitation", "seed-cap5"),
    seedEntry("cap6", T(13, 5), "invitation", "seed-cap6"),
    seedEntry("cap7", T(13, 6), "invitation", "seed-cap7"),
    seedEntry("cap8", T(13, 7), "invitation", "seed-cap8"),
    seedEntry("cap9", T(13, 8), "invitation", "seed-cap9"),
  ] }, null, 1));
  const PORT3 = 18736;
  const env3 = { ...process.env, PORT: String(PORT3), LIBRARY_DATA: tmp3,
    LIBRARY_MASTER_TOKEN: "test-master", LIBRARY_SECRET: "test-secret",
    RESEND_API_KEY: "test-key", RESEND_API_URL: `http://127.0.0.1:${stub3.address().port}/emails` };
  const srv3 = spawn("node", ["server.mjs"], { cwd: ROOT, env: env3, stdio: "pipe" });
  const B3 = `http://127.0.0.1:${PORT3}`;
  const call3 = async (p, { method = "GET", body } = {}) => {
    const r = await fetch(B3 + p, { method, headers: { "content-type": "application/json" },
      body: body ? JSON.stringify(body) : undefined });
    return { status: r.status, body: await r.json().catch(() => ({})) };
  };
  const comms3 = () => JSON.parse(fs.readFileSync(path.join(tmp3, "comms-log.json"), "utf8")).sends;
  const waitFor3 = async (fn, ms = 6000) => {
    const t0 = Date.now();
    while (Date.now() - t0 < ms) { const v = fn(); if (v) return v; await new Promise(r => setTimeout(r, 100)); }
    return fn();
  };
  try {
    for (let i = 0; i < 50; i++) { try { const r = await fetch(B3 + "/"); if (r.ok) break; } catch { await new Promise(r => setTimeout(r, 100)); } }
    await call3("/api/signout", { method: "POST" }); // any POST drains the queue (post-response)
    await waitFor3(() => received3.length >= 10 && comms3().find((s) => s.id === "cap6")?.status === "sent");
    const subjects3 = received3.map((x) => x.subject);
    ok("drain priority: OTP entries send before older invitations, oldest-first within kind",
      JSON.stringify(subjects3.slice(0, 5)) === JSON.stringify(
        ["seed-otp-dup", "seed-otp-new", "seed-inv-old1", "seed-inv-old2", "seed-cap1"]));
    ok("drain dedupe: a duplicated queued snapshot is sent exactly once",
      subjects3.filter((s) => s === "seed-otp-dup").length === 1);
    ok("drain dedupe: a stale queued snapshot of an already-sent entry is never re-sent",
      !subjects3.includes("seed-dup1"));
    const log3 = comms3();
    const dup1Rows = log3.filter((s) => s.id === "dup1");
    ok("drain dedupe: the log heals to one row per entry, latest state wins",
      dup1Rows.length === 1 && dup1Rows[0].status === "sent" && dup1Rows[0].providerId === "stub-old-1" &&
      log3.filter((s) => s.id === "dup2").length === 1 && log3.length === 14);
    ok("drain cap: attempts stop at 10 per drain — the tail stays queued, unattempted",
      received3.length === 10 &&
      ["cap7", "cap8", "cap9"].every((id) => { const e = log3.find((s) => s.id === id);
        return e && e.status === "queued" && !e.attempts; }));

    // A send the API never answers: recorded as a timeout,
    // distinctly, and the drain still works through its cap.
    const clog = JSON.parse(fs.readFileSync(path.join(tmp3, "comms-log.json"), "utf8"));
    clog.sends.push(seedEntry("hang1", T(8), "invitation", "seed-hang"));
    fs.writeFileSync(path.join(tmp3, "comms-log.json"), JSON.stringify(clog, null, 1));
    await call3("/api/signout", { method: "POST" });
    const hang = await waitFor3(() => { const e = comms3().find((s) => s.id === "hang1");
      return e && e.lastError ? e : null; }, 15000);
    ok("timeout recorded distinctly: lastError names the timeout, attempt counted, entry stays queued",
      !!hang && /^timeout:/.test(hang.lastError) && hang.attempts === 1 && hang.status === "queued");
    ok("drain continues past a timed-out send within its attempt cap",
      ["cap7", "cap8", "cap9"].every((id) => comms3().find((s) => s.id === id)?.status === "sent"));
  } finally {
    srv3.kill();
    stub3.close();
    fs.rmSync(tmp3, { recursive: true, force: true });
  }
}

console.log(`\nRESULT: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
