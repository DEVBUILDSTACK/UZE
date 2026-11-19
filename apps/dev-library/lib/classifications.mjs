// The classification layer (James, 2026-11-19): the desk's map of
// who is who, above the operational rosters. Five classes —
//   owner        the family: D4, D5, WCD (name + email of record)
//   principal    Jonathan Schmidt, with Learn2Launch — the only one
//   advisor      Bruno Salles, Learn2Launch only (the layer that
//                did not exist before him: not a dev partner, not
//                a principal; no code, no GitHub, no sign-in)
//   dev-internal Shradesh Jain, Rohan Singla — trusted internals
//   dev-external Dipanshu Singh, Nithin Mengani — recruiting targets
// The layer carries each person's greeting name (the Hello "First
// Name" rule resolves here first). Rosters grant access; this layer
// says what a person IS.
import { load } from "./store.mjs";

export const CLASS_LABELS = {
  "owner": "Owners — the family",
  "principal": "Principals",
  "advisor": "Advisors",
  "dev-internal": "Developers — internal",
  "dev-external": "Developers — external (recruiting targets)",
};

export function loadClassifications() {
  try { return load("classifications.json").people || []; } catch { return []; }
}
export function classificationFor(email) {
  const em = String(email || "").toLowerCase();
  return loadClassifications().find((p) => (p.email || "").toLowerCase() === em) || null;
}
export function greetingNameFor(email) {
  const c = classificationFor(email);
  return c && c.greeting ? c.greeting : null;
}
