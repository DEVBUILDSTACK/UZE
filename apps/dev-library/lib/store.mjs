// JSON data store. Data dir defaults to ../data, overridable with
// LIBRARY_DATA (tests run against a temp copy — the real chronicle
// is never touched by a test run).
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const DATA = process.env.LIBRARY_DATA || path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "data");
export function load(name) { return JSON.parse(fs.readFileSync(path.join(DATA, name), "utf8")); }
// Write-through persistence (lib/store-pg.mjs registers here in DB
// mode): the JSON documents are the working set; Postgres is the
// durable record. In JSON mode no persister is registered.
let persister = null;
export function setPersister(fn) { persister = fn; }
export function save(name, obj) {
  fs.writeFileSync(path.join(DATA, name), JSON.stringify(obj, null, 1) + "\n");
  if (persister) persister(name, obj);
}
export function chronicle(type, fields) {
  const c = load("chronicle.json");
  c.entries.push({ at: new Date().toISOString(), type, ...fields });
  save("chronicle.json", c);
}
// The greeting rule (James, 2026-11-19): an email always addresses
// the recipient as Hello "First Name". The name resolves from the
// rosters — the eco contributor record first (it carries the
// settled spellings), then the developer record — with any
// parenthetical dropped ("James Dugan (D5)" -> "James"). No name
// on file: the mailer's kind default stands; a name is never
// invented.
// Address-name rulings (James, 2026-11-19): the greeting name is
// not always the display name's first token. D4 — Hammond James
// Dugan IV, the founder SoSem deals with — is addressed "Hammond",
// never "James" (that is his son, D5). The classification layer
// (lib/classifications.mjs) carries each person's greeting name
// and is consulted first; the rosters resolve everyone else.
function firstNameFor(email) {
  const em = String(email || "").toLowerCase();
  try {
    const people = load("classifications.json").people || [];
    const c = people.find((p) => (p.email || "").toLowerCase() === em);
    if (c && c.greeting) return c.greeting;
  } catch { /* no classification layer in this data dir */ }
  const clean = (n) => String(n || "").replace(/\([^)]*\)/g, "").trim().split(/\s+/)[0] || null;
  try {
    const c = (load("eco-contributors.json").contributors || []).find((x) => (x.email || "").toLowerCase() === em);
    if (c && clean(c.name)) return clean(c.name);
  } catch { /* no eco roster in this data dir */ }
  try {
    const d = (load("developers.json").developers || []).find((x) => (x.email || "").toLowerCase() === em);
    if (d && clean(d.name)) return clean(d.name);
  } catch { /* no developer roster in this data dir */ }
  return null;
}
export function commsSend(to, kind, subject, body, extra = {}) {
  const log = load("comms-log.json");
  const entry = { id: `c${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`,
    at: new Date().toISOString(), from: log.sender, to, kind, subject, body, status: "queued", ...extra };
  // The exception (James, 2026-11-19): the development-partner
  // kinds keep "Dear Development Partner," — the Dev Library grant
  // correspondence addresses the partnership, not the person. All
  // other kinds carry Hello "First Name".
  const DEV_PARTNER_KINDS = ["invitation", "source-grant", "change-notice", "revocation"];
  if (!entry.greetingText && !DEV_PARTNER_KINDS.includes(kind)) {
    const first = firstNameFor(to);
    if (first) entry.greetingText = `Hello ${first},`;
  }
  log.sends.push(entry); save("comms-log.json", log);
  chronicle("comms-send", { to, kind, subject });
  return entry;
}
