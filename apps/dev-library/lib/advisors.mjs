// The L2L & Ecosystem Advisors roster: master-desk operations.
// A roster parallel to the Developer List (lib/lifecycle.mjs) but
// distinct by design — no tracks, no expertise pairs, no GitHub
// grants, no sign-in lifecycle. Advisors advise; the desk keeps the
// list. Every operation writes the chronicle, like the desk's other
// rosters.
import { load, save, chronicle } from "./store.mjs";

export function loadAdvisors() {
  return load("advisors.json").advisors || [];
}
export function addAdvisor({ name, email, title = "", org = "", base = "", lane = "" }) {
  if (!name || !email) throw new Error("advisor needs a name and an email");
  const db = load("advisors.json");
  db.advisors = db.advisors || [];
  if (db.advisors.some(a => a.email.toLowerCase() === String(email).toLowerCase()))
    throw new Error("already listed: " + email);
  const a = { id: `a${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`,
    name: String(name), email: String(email), title: String(title || ""), org: String(org || ""),
    base: String(base || ""), lane: String(lane || ""), addedAt: new Date().toISOString() };
  db.advisors.push(a); save("advisors.json", db);
  chronicle("advisor-added", { email: a.email, name: a.name, title: a.title, org: a.org });
  return a;
}
export function removeAdvisor(email) {
  const db = load("advisors.json");
  db.advisors = db.advisors || [];
  const i = db.advisors.findIndex(a => a.email.toLowerCase() === String(email).toLowerCase());
  if (i < 0) throw new Error("advisor not found: " + email);
  const [a] = db.advisors.splice(i, 1); save("advisors.json", db);
  chronicle("advisor-removed", { email: a.email, name: a.name });
  return a;
}
