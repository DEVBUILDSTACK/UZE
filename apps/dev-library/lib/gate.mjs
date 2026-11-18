// The door of the reading room: email allowlist, one-time codes,
// signed sessions. Server-side only — nothing is served before this
// check passes. The allowlist IS the developer list: a developer
// whose readingRoom.active is true may sign in.
import { createHash, createHmac, randomInt, timingSafeEqual } from "node:crypto";
import { load, commsSend } from "./store.mjs";

const SECRET = process.env.LIBRARY_SECRET || "dev-secret-change-at-go-live";
const codes = new Map(); // email -> { hash, expires }
const sha = (s) => createHash("sha256").update(s).digest("hex");

export function findDeveloper(email) {
  return load("developers.json").developers.find(d => d.email.toLowerCase() === String(email).toLowerCase()) || null;
}
export function isAllowlisted(email) { const d = findDeveloper(email); return !!(d && d.readingRoom?.active); }

export function requestCode(email) {
  if (!isAllowlisted(email)) return { sent: false }; // generic answer; nothing issued, nothing logged as sent
  const code = String(randomInt(0, 1000000)).padStart(6, "0");
  codes.set(email.toLowerCase(), { hash: sha(code), expires: Date.now() + 15 * 60 * 1000 });
  commsSend(email, "otp", "Your Dev Library sign-in code",
    `Your one-time sign-in code for the UZE Dev Library is ${code}. It expires in 15 minutes. If you were not expecting this, ignore this email.`);
  return { sent: true };
}
export function verifyCode(email, code) {
  const rec = codes.get(String(email).toLowerCase());
  if (!rec || rec.expires < Date.now() || rec.hash !== sha(String(code))) return false;
  codes.delete(String(email).toLowerCase()); return true;
}
// Sessions carry the developer's sessionEpoch: any access-affecting
// change (revocation, clearance change) bumps the epoch and every
// live session for that developer dies — the re-prompt behavior.
export function signSession(email) {
  const d = findDeveloper(email); if (!d) return null;
  const payload = Buffer.from(JSON.stringify({ email: d.email, epoch: d.sessionEpoch || 0 })).toString("base64url");
  const sig = createHmac("sha256", SECRET).update(payload).digest("base64url");
  return `${payload}.${sig}`;
}
export function readSession(token) {
  if (!token || !token.includes(".")) return null;
  const [payload, sig] = token.split(".");
  const expect = createHmac("sha256", SECRET).update(payload).digest("base64url");
  if (!timingSafeEqual(Buffer.from(sig), Buffer.from(expect))) return null;
  const { email, epoch } = JSON.parse(Buffer.from(payload, "base64url").toString());
  const d = findDeveloper(email);
  if (!d || !d.readingRoom?.active || (d.sessionEpoch || 0) !== epoch) return null;
  return d;
}
export function visibleMocks(developer) {
  // Clearance is the access control; the track rule keeps internal-only
  // material out of external flows and vice versa (directive I4/I5).
  const trackOk = (m) => {
    const t = m.track || "BOTH";
    if (t === "BOTH") return true;
    if (t === "INTERNAL_ONLY") return developer.track !== "EXTERNAL_PLACED";
    if (t === "EXTERNAL_VISIBLE") return developer.track !== "INTERNAL_ONLY";
    return true;
  };
  return load("mocks.json").mocks.filter(m => trackOk(m) &&
    (!m.clearance?.length || m.clearance.map(e => e.toLowerCase()).includes(developer.email.toLowerCase())));
}
