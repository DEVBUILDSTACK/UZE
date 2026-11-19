// The Developer List: lifecycle operations by the master agent.
// Every operation writes the chronicle. Revocation resets access to
// zero and preserves the history — the chronicle is never rewritten.
import { load, save, chronicle, commsSend } from "./store.mjs";
import { validatePairs, TRACKS } from "./taxonomy.mjs";
import { composeInvitation } from "./invitations.mjs";

const STAGES = ["prospect", "contacted", "recruiting", "reading-room", "source-access", "revoked"];
function mutate(email, fn) {
  const db = load("developers.json");
  const d = db.developers.find(x => x.email.toLowerCase() === String(email).toLowerCase());
  if (!d) throw new Error("developer not found: " + email);
  fn(d, db); save("developers.json", db); return d;
}
function setStage(d, stage) {
  d.stage = stage; d.stageHistory = d.stageHistory || [];
  d.stageHistory.push({ stage, at: new Date().toISOString() });
}
export function addDeveloper({ name, email, expertise = [], pairs = null, roadmapExempt = false, track = "EITHER" }) {
  const db = load("developers.json");
  if (db.developers.some(x => x.email.toLowerCase() === email.toLowerCase())) throw new Error("already listed: " + email);
  const normPairs = pairs ? validatePairs(pairs) : [];
  const d = { name, email, expertise: normPairs.length ? [...new Set(normPairs.map(p => p.realm))] : expertise.slice(0, 5),
    pairs: normPairs, roadmapExempt, track,
    contact: { email: { done: false, at: null }, whatsapp: { done: false, at: null } },
    readingRoom: { active: false, grantedAt: null, revokedAt: null },
    source: [], sessionEpoch: 0, roadmap: null, stage: "prospect", stageHistory: [{ stage: "prospect", at: new Date().toISOString() }] };
  db.developers.push(d); save("developers.json", db);
  chronicle("developer-added", { email, name, expertise: d.expertise, pairs: d.pairs });
  return d;
}
// Role × Realm taxonomy (I1): up to five pairs, PRIMARY → QUINARY by
// position, no duplicate (role, realm). The realm list (`expertise`)
// is kept as the derived mirror of the pairs so the existing filters
// and UI keep reading one shape.
export function setExpertise(email, pairsInput) {
  const pairs = validatePairs(pairsInput);
  const d = mutate(email, (x) => { x.pairs = pairs; x.expertise = [...new Set(pairs.map(p => p.realm))]; });
  chronicle("expertise-set", { email, pairs }); return d;
}
// Track transitions are routine by the desk and logged (BUILD-SCOPE
// §A.7 item 2): INTERNAL_ONLY = Track A (never placed), EXTERNAL_PLACED
// = Track B, EITHER = available to both.
export function setTrack(email, track) {
  if (!TRACKS.includes(track)) throw new Error("invalid track: " + track);
  let from = null;
  const d = mutate(email, (x) => { from = x.track || "EITHER"; x.track = track; });
  chronicle("track-set", { email, from, to: track }); return d;
}
export function markContact(email, channel) { // channel: "email" | "whatsapp" — the only two doors
  if (!["email", "whatsapp"].includes(channel)) throw new Error("contact channel must be email or whatsapp");
  const d = mutate(email, (x) => { x.contact[channel] = { done: true, at: new Date().toISOString() };
    if (x.stage === "prospect") setStage(x, "contacted"); });
  chronicle("contact", { email, channel }); return d;
}
export function grantReadingRoom(email) {
  const d = mutate(email, (x) => { x.readingRoom = { active: true, grantedAt: new Date().toISOString(), revokedAt: null };
    if (["prospect", "contacted", "recruiting"].includes(x.stage)) setStage(x, "reading-room"); });
  // Dual-surface rule (James, 2026-11-19): an email that ALSO holds
  // an eco contributor grant receives ONE combined invitation —
  // ecosystem first, library second — never two competing emails.
  // composeInvitation returns null for library-only emails, and the
  // library invitation below stands unchanged for them.
  if (!composeInvitation(email)) {
    commsSend(email, "invitation", "You have access to the UZE Dev Library",
      "You have been granted access to the UZE Dev Library. Sign in with this email address to receive a one-time code.");
  }
  chronicle("grant-reading-room", { email }); return d;
}
export function grantSource(email, repo, roadmap = null) {
  const d = mutate(email, (x) => { x.source.push({ repo, grantedAt: new Date().toISOString(), revokedAt: null });
    if (roadmap) x.roadmap = roadmap; setStage(x, "source-access"); });
  commsSend(email, "source-grant", `Your GitHub access to ${repo} is active`,
    `You have been granted source access to ${repo} on GitHub.${roadmap ? " Your work is bound to this roadmap: " + roadmap : ""}`);
  chronicle("grant-source", { email, repo, roadmap }); return d;
}
// Reset to zero: no reading room, no source, no live sessions
// (epoch bump kills them). The chronicle keeps everything.
export function revokeAll(email, reason = "") {
  const d = mutate(email, (x) => {
    x.readingRoom.active = false; x.readingRoom.revokedAt = new Date().toISOString();
    for (const s of x.source) if (!s.revokedAt) s.revokedAt = new Date().toISOString();
    x.sessionEpoch = (x.sessionEpoch || 0) + 1; setStage(x, "revoked"); });
  commsSend(email, "revocation", "Your Dev Library access has been reset",
    "Your reading-room and source access have been reset to zero. Your involvement history is retained in the project chronicle.");
  chronicle("revoke-all", { email, reason }); return d;
}
// Access-affecting change for one developer (e.g. clearance change):
// end their sessions and let the desk send a fresh link the same day.
export function reprompt(email, note = "There's been a change.") {
  const d = mutate(email, (x) => { x.sessionEpoch = (x.sessionEpoch || 0) + 1; });
  commsSend(email, "change-notice", "Dev Library — new sign-in link",
    `You were in the Dev Library recently. ${note} Sign in again with this email address to receive a fresh one-time code.`);
  chronicle("reprompt", { email, note }); return d;
}
// Naming synchronization: one edit in the manifest adjusts the
// whole room; the old name stays as an alias (redirect, never 404).
export function renameMock(oldSlug, { slug, title, note }) {
  const db = load("mocks.json");
  const m = db.mocks.find(x => x.slug === oldSlug || (x.aliases || []).includes(oldSlug));
  if (!m) throw new Error("mock not found: " + oldSlug);
  if (slug && slug !== m.slug) { m.aliases = [...(m.aliases || []), m.slug]; m.slug = slug; }
  if (title) m.title = title;
  m.version += 1; m.changelog.push(`v${m.version} — ${new Date().toISOString().slice(0, 10)}: ${note}`);
  save("mocks.json", db);
  chronicle("mock-renamed", { from: oldSlug, to: m.slug, version: m.version, note });
  return m;
}
export { STAGES };
