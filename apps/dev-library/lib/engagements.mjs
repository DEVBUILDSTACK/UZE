// Track B engagements — desk-mediated placement (merged program M1;
// amendment S1: until the separated P2 track lands, the DESK makes the
// staffing call; platform data is supporting evidence, never a gating
// signal). Engagements run on invoice through M3 (amendment C2) — no
// settlement machinery lives here.
//
// The record stores FACTS only (who is staffed, signedAt, depositAt,
// closedAt, cancelledAt). The engagement state is DERIVED from those
// facts at read time — never written (invariant I7's discipline,
// applied to engagements). Every transition appends to the record's
// history AND emits a chronicle Event (I13), in the house order:
// mutate + save first, chronicle after.
//
// Confidentiality doctrine (commercial-models addendum, James
// 2026-11-18): the talent is NEVER exposed to the client — no name, no
// email, no contact — until BOTH a signed engagement AND a deposit are
// in hand. clientView() below is the only client-facing projection and
// it is blind by construction until revealed() is true; the API serves
// no other client view of an engagement.
import { load, save, chronicle } from "./store.mjs";
import { findDeveloper } from "./gate.mjs";
import { SERVICES, DEPLOYMENTS, COMMERCIAL_MODELS } from "./taxonomy.mjs";

const now = () => new Date().toISOString();
const newId = () => `eng_${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`;

export function engagementState(e) {
  if (e.cancelledAt) return "CANCELLED";
  if (e.closedAt) return "CLOSED";
  if (e.signedAt && e.depositAt) return "ACTIVE";
  if (e.signedAt) return "SIGNED";
  if (e.developerEmail) return "STAFFED";
  return "OPEN";
}
export function revealed(e) { return !!(e.signedAt && e.depositAt); }

export function loadEngagements() { return load("engagements.json").engagements; }
export function findEngagement(id) { return loadEngagements().find(e => e.id === id) || null; }

function mutate(id, fn) {
  const db = load("engagements.json");
  const e = db.engagements.find(x => x.id === id);
  if (!e) throw new Error("engagement not found: " + id);
  fn(e); save("engagements.json", db); return e;
}
const note = (e, event, fields = {}) => e.history.push({ at: now(), event, ...fields });

// The desk's own view: the full record + derived state. Internal only.
export function deskView(e) { return { ...e, state: engagementState(e), revealed: revealed(e) }; }

// The client-facing projection — BLIND until signed + deposit.
// Pre-reveal the talent appears as skills only (Role×Realm pairs and
// realm list): no name, no email, no contact channels, no source
// grants. Post-reveal the identity is the name + email of record.
export function clientView(e) {
  const d = e.developerEmail ? findDeveloper(e.developerEmail) : null;
  const view = {
    id: e.id, title: e.title, service: e.service, deployment: e.deployment,
    commercialModel: e.commercialModel, state: engagementState(e),
    staffed: !!e.developerEmail, revealed: revealed(e), talent: null,
  };
  if (e.commercialModel === "PLACEMENT") view.feeMonths = e.feeMonths;
  if (e.developerEmail && d) {
    view.talent = revealed(e)
      ? { name: d.name, email: d.email, pairs: d.pairs || [], expertise: d.expertise || [] }
      : { pairs: d.pairs || [], expertise: d.expertise || [] };
  }
  return view;
}

export function openEngagement({ title, clientName, clientRef = null, service, deployment, commercialModel, feeMonths = null, salaryBasis = null }) {
  if (!title || !String(title).trim()) throw new Error("engagement title is required");
  if (!clientName || !String(clientName).trim()) throw new Error("client name is required");
  if (!SERVICES.includes(service)) throw new Error("invalid service: " + service);
  if (!DEPLOYMENTS.includes(deployment)) throw new Error("invalid deployment: " + deployment);
  if (!COMMERCIAL_MODELS.includes(commercialModel)) throw new Error("invalid commercial model: " + commercialModel);
  // The two money models are distinct, never blended (addendum): the
  // placement fee — at least one month (30 days) of salary — exists
  // only under PLACEMENT; under OUTSTAFFING UZE pays the talent and
  // bills the client, and no placement fee is recorded.
  if (commercialModel === "PLACEMENT") {
    if (!(Number(feeMonths) >= 1)) throw new Error("PLACEMENT requires a fee of at least 1 month of salary (feeMonths >= 1)");
  } else if (feeMonths !== null && feeMonths !== undefined) {
    throw new Error("feeMonths belongs to the PLACEMENT model only");
  }
  const e = { id: newId(), title: String(title), clientName: String(clientName), clientRef,
    service, deployment, commercialModel,
    feeMonths: commercialModel === "PLACEMENT" ? Number(feeMonths) : null,
    salaryBasis: salaryBasis === null || salaryBasis === undefined ? null : Number(salaryBasis),
    developerEmail: null, staffedAt: null,
    signedAt: null, signedRef: null, depositAt: null, depositRef: null,
    closedAt: null, cancelledAt: null, cancelReason: "",
    createdAt: now(), createdBy: "desk", history: [] };
  note(e, "engagement-opened", { service, deployment, commercialModel, clientName: e.clientName });
  const db = load("engagements.json");
  db.engagements.push(e); save("engagements.json", db);
  chronicle("engagement-opened", { id: e.id, service, deployment, commercialModel, clientName: e.clientName });
  return e;
}

// Desk-mediated staffing (S1): the desk's call. The only hard rules
// are the track rule — Track A (INTERNAL_ONLY) talent is never placed
// (BUILD-SCOPE §A.2) — and that a revoked record cannot be staffed.
export function staffEngagement(id, email) {
  const d = findDeveloper(email);
  if (!d) throw new Error("developer not found: " + email);
  if (d.stage === "revoked") throw new Error("a revoked developer cannot be staffed");
  if ((d.track || "EITHER") === "INTERNAL_ONLY") throw new Error("Track A (INTERNAL_ONLY) talent is never placed");
  const e = mutate(id, (x) => {
    const st = engagementState(x);
    if (st !== "OPEN") throw new Error("engagement is not open for staffing (state: " + st + ")");
    x.developerEmail = d.email; x.staffedAt = now();
    note(x, "engagement-staffed", { developerEmail: d.email });
  });
  chronicle("engagement-staffed", { id, developerEmail: d.email });
  return e;
}
export function unstaffEngagement(id) {
  let prev = null;
  const e = mutate(id, (x) => {
    if (engagementState(x) !== "STAFFED") throw new Error("only a staffed (unsigned) engagement can be unstaffed");
    prev = x.developerEmail;
    x.developerEmail = null; x.staffedAt = null;
    note(x, "engagement-unstaffed", { developerEmail: prev });
  });
  chronicle("engagement-unstaffed", { id, developerEmail: prev });
  return e;
}
export function recordSigned(id, ref = null) {
  const e = mutate(id, (x) => {
    if (engagementState(x) !== "STAFFED") throw new Error("only a staffed engagement can be signed");
    x.signedAt = now(); x.signedRef = ref;
    note(x, "engagement-signed", { ref });
  });
  chronicle("engagement-signed", { id, ref });
  return e;
}
export function recordDeposit(id, ref = null) {
  const e = mutate(id, (x) => {
    if (engagementState(x) !== "SIGNED") throw new Error("a deposit is recorded only after the engagement is signed");
    x.depositAt = now(); x.depositRef = ref;
    note(x, "engagement-deposit", { ref });
    note(x, "engagement-revealed", { developerEmail: x.developerEmail });
  });
  chronicle("engagement-deposit", { id, ref });
  // Signed + deposit in hand: the reveal point of the doctrine.
  chronicle("engagement-revealed", { id, developerEmail: e.developerEmail });
  return e;
}
export function closeEngagement(id) {
  const e = mutate(id, (x) => {
    if (engagementState(x) !== "ACTIVE") throw new Error("only an active (signed + deposit) engagement can be closed");
    x.closedAt = now();
    note(x, "engagement-closed", {});
  });
  chronicle("engagement-closed", { id });
  return e;
}
export function cancelEngagement(id, reason = "") {
  const e = mutate(id, (x) => {
    const st = engagementState(x);
    if (st === "CLOSED" || st === "CANCELLED") throw new Error("engagement is already " + st.toLowerCase());
    x.cancelledAt = now(); x.cancelReason = reason;
    note(x, "engagement-cancelled", { reason });
  });
  chronicle("engagement-cancelled", { id, reason });
  return e;
}
