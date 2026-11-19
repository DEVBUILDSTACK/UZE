// Flow-completion tracking for the UZE Buildr Team surface
// (James, 2026-11-19). Principle: completion is proven by the UI
// flow itself, never by self-report — the contributor advances by
// clicking the step's Next action, and the click IS the record.
// Events are append-only (eco-flow.json / eco_flow_event); a
// contributor's current step is DERIVED from their events, never a
// hand-set flag.
//
// Scoping (James, 2026-11-19): the REQUIRED tracked step-through
// binds only DUAL-HOLDERS — people whose email holds grants on both
// surfaces (eco contributor + Dev Library). Single-surface
// contributors browse freely after OTP: events may be recorded when
// they click through, but nothing is required of them, they get no
// resume lead, and they are NEVER flagged stalled.
import { load, save, chronicle } from "./store.mjs";
import { findContributor } from "./eco-contributors.mjs";
import { findDeveloper } from "./gate.mjs";

export const ECO_STEPS = ["signed_in", "overview_viewed", "overview_completed", "advanced_to_library", "library_signed_in"];
export const STALL_MS = 72 * 3600 * 1000;

export function isDualHolder(email) {
  if (!findContributor(email)) return false;
  const d = findDeveloper(email);
  return !!(d && d.readingRoom?.active);
}
export function loadFlowEvents() { return load("eco-flow.json").events; }
export function eventsFor(contributorId) { return loadFlowEvents().filter(e => e.contributorId === contributorId); }
// One row per transition: a step already recorded for a contributor
// is not recorded twice. Every transition also writes a chronicle
// entry so the master can see it.
export function recordFlowEvent(contributor, step) {
  if (!ECO_STEPS.includes(step)) throw new Error("unknown eco flow step: " + step);
  const doc = load("eco-flow.json");
  if (doc.events.some(e => e.contributorId === contributor.id && e.step === step)) return null;
  const ev = { id: `f${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`,
    contributorId: contributor.id, step, at: new Date().toISOString() };
  doc.events.push(ev); save("eco-flow.json", doc);
  chronicle("eco-flow-step", { email: contributor.email, contributor: contributor.name, step });
  return ev;
}
// The library side of the dual sequence: when a dual-holder signs in
// to the Dev Library under the same email, the sequence completes.
export function noteLibrarySignIn(email) {
  const c = findContributor(email);
  if (!c || !isDualHolder(email)) return null;
  return recordFlowEvent(c, "library_signed_in");
}
export function deriveProgress(contributor, now = Date.now()) {
  const evs = eventsFor(contributor.id);
  const steps = {};
  for (const e of evs) steps[e.step] = e.at;
  let current = null;
  for (const s of ECO_STEPS) if (steps[s]) current = s; // furthest step reached
  const dual = isDualHolder(contributor.email);
  const finalStep = dual ? "library_signed_in" : "overview_completed";
  const completed = !!steps[finalStep];
  const started = evs.length > 0;
  const lastMs = started ? Math.max(...evs.map(e => Date.parse(e.at))) : null;
  // No requirement → no stall: only a dual-holder can stall.
  const stalled = dual && started && !completed && (now - lastMs > STALL_MS);
  const limit = ECO_STEPS.indexOf(finalStep);
  const next = completed ? null : (ECO_STEPS.find(s => !steps[s] && ECO_STEPS.indexOf(s) <= limit) || null);
  return { contributorId: contributor.id, name: contributor.name, email: contributor.email,
    dual, steps, current, next, completed, stalled,
    lastEventAt: lastMs ? new Date(lastMs).toISOString() : null };
}
export function progressForAll(now = Date.now()) {
  return load("eco-contributors.json").contributors.map(c => deriveProgress(c, now));
}
