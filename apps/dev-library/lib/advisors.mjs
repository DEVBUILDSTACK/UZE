// The L2L & Ecosystem Advisors roster: master-desk operations.
// A roster parallel to the Developer List (lib/lifecycle.mjs) but
// distinct by design — no tracks, no expertise pairs, no GitHub
// grants, no sign-in lifecycle. Advisors advise; the desk keeps the
// list. Every operation writes the chronicle, like the desk's other
// rosters.
//
// Organizations are first-class (lib/orgs.mjs): an advisor record
// carries an org KEY referencing the registry, validated on write.
// Email is OPTIONAL for advisor contacts — unique only when
// present; a contact with no email on file carries null.
import { load, save, chronicle } from "./store.mjs";
import { findOrg } from "./orgs.mjs";

export function loadAdvisors() {
  return load("advisors.json").advisors || [];
}
export function addAdvisor({ name, email = null, title = "", org = "", base = "", lane = "" }) {
  if (!name) throw new Error("advisor needs a name");
  if (!org || !findOrg(String(org))) throw new Error("unknown org: " + org);
  const db = load("advisors.json");
  db.advisors = db.advisors || [];
  const em = email ? String(email) : null;
  if (em && db.advisors.some(a => a.email && a.email.toLowerCase() === em.toLowerCase()))
    throw new Error("already listed: " + em);
  const a = { id: `a${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`,
    name: String(name), email: em, title: String(title || ""), org: String(org),
    base: String(base || ""), lane: String(lane || ""), addedAt: new Date().toISOString() };
  db.advisors.push(a); save("advisors.json", db);
  chronicle("advisor-added", { email: a.email, name: a.name, title: a.title, org: a.org });
  return a;
}
// Removal takes an email or — for contacts with no email on file —
// the record id; either identifies the record.
export function removeAdvisor(identifier) {
  const db = load("advisors.json");
  db.advisors = db.advisors || [];
  const needle = String(identifier || "");
  const i = db.advisors.findIndex(a => a.id === needle ||
    (a.email && needle && a.email.toLowerCase() === needle.toLowerCase()));
  if (i < 0) throw new Error("advisor not found: " + identifier);
  const [a] = db.advisors.splice(i, 1); save("advisors.json", db);
  chronicle("advisor-removed", { email: a.email, name: a.name });
  return a;
}
