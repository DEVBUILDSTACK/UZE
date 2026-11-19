// The UZE Buildr Team contributor registry (buildr-team.uzemarkets.com).
// A distinct roster from the Developer List: contributors are
// principals and ecosystem contributors who do NOT use GitHub —
// email + one-time code only. Visibility model (James, 2026-11-19):
// the Ecosystem top level is visible to every signed-in contributor;
// the four org sections beneath it are granted per contributor in
// the record's `orgs` (org-registry keys: UZE, L2Launch, DFI, FVC)
// and enforced server-side — the nav hides what a contributor cannot
// see, and a direct URL to an ungranted section returns 403.
import { load, save, chronicle } from "./store.mjs";

export function loadContributors() { return load("eco-contributors.json").contributors; }
export function findContributor(email) {
  if (!email) return null;
  return loadContributors().find(c => c.email && c.email.toLowerCase() === String(email).toLowerCase()) || null;
}
export function findContributorById(id) { return loadContributors().find(c => c.id === id) || null; }
export function canSeeOrg(contributor, orgKey) { return !!contributor && (contributor.orgs || []).includes(orgKey); }
export function publicView(c) {
  return { id: c.id, name: c.name, email: c.email, role: c.role, stage: c.stage, orgs: (c.orgs || []).slice() };
}
// Master-side add (the desk seeds a contributor record; sign-in
// activates when the record carries an email). Idempotent by email.
export function addContributor({ name, email = null, role = "Ecosystem Contributor", orgs = [] }) {
  const db = load("eco-contributors.json");
  if (email) {
    const existing = db.contributors.find(c => c.email && c.email.toLowerCase() === String(email).toLowerCase());
    if (existing) return existing;
  }
  const slug = String(name).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  const c = { id: `eco-${slug}-${Date.now().toString(36)}`, name, email: email ? String(email).toLowerCase() : null,
    role, orgs: orgs.slice(), sessionEpoch: 0, stage: "seeded", addedAt: new Date().toISOString() };
  db.contributors.push(c); save("eco-contributors.json", db);
  chronicle("eco-contributor-added", { email: c.email, name, orgs: c.orgs });
  return c;
}
