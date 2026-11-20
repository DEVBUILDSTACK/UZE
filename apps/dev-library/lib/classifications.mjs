// The classification layer (James, 2026-11-19): the desk's map of
// who is who, above the operational rosters. Six classes —
//   owner        the family: D4, D5, WCD (name + email of record)
//   principal    Jonathan Schmidt, with Learn2Launch — the only one
//   advisor      visibility into the repo, but NO code access unless
//                granted by OTP — and an advisor's OTP expires at
//                the 24-hour mark (Hammond, 2026-11-20). Currently
//                unoccupied.
//   mentor       Bruno Salles, Learn2Launch (moved from advisor by
//                Hammond, 2026-11-20: no productization experience;
//                the mentor seat fits). Mentors have NO repo
//                visibility and NO code access — presented material
//                only (renders, briefings).
//   dev-internal Shradesh Jain, Rohan Singla — trusted internals
//   dev-external Dipanshu Singh, Nithin Mengani — recruiting targets
// OTP persistence by class (Hammond, 2026-11-20): developer OTPs do
// not expire until revoked; advisor OTPs expire at 24 hours.
// The layer carries each person's greeting name (the Hello "First
// Name" rule resolves here first). Rosters grant access; this layer
// says what a person IS.
import { load } from "./store.mjs";

export const CLASS_LABELS = {
  "owner": "Owners — the family",
  "principal": "Principals",
  "advisor": "Advisors",
  "mentor": "Mentors",
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
