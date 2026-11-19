// The door of the UZE Buildr Team surface: contributor registry,
// one-time codes, signed sessions. Modeled on lib/gate.mjs (the Dev
// Library door) with two deliberate separations: the session cookie
// is `eco_session`, and eco codes live in their own namespace
// (eco_otp_code in DB mode, a separate map in JSON mode) so Dev
// Library codes and eco codes never mix — even for an email that
// holds grants on both surfaces.
import { createHash, createHmac, randomInt, timingSafeEqual } from "node:crypto";
import { commsSend } from "./store.mjs";
import { findContributor } from "./eco-contributors.mjs";

const SECRET = process.env.LIBRARY_SECRET || "dev-secret-change-at-go-live";
const codes = new Map(); // email -> { hash, expires } (eco namespace only)
const sha = (s) => createHash("sha256").update(s).digest("hex");

let pgOtp = null;
async function otpStore() {
  if (!process.env.DATABASE_URL && !process.env.POSTGRES_URL) return null;
  if (!pgOtp) pgOtp = await import("./store-pg.mjs");
  return pgOtp;
}
export async function requestEcoCode(email) {
  const c = findContributor(email);
  // Generic answer for unknown addresses and for records that carry
  // no email yet: nothing issued, nothing logged as sent.
  if (!c || !c.email) return { sent: false };
  const code = String(randomInt(0, 1000000)).padStart(6, "0");
  const pg = await otpStore();
  if (pg) await pg.setEcoOtp(c.email.toLowerCase(), sha(code), Date.now() + 15 * 60 * 1000);
  else codes.set(c.email.toLowerCase(), { hash: sha(code), expires: Date.now() + 15 * 60 * 1000 });
  const entry = commsSend(c.email, "eco-otp", "Your UZE Buildr Team sign-in code",
    `Your one-time sign-in code for the UZE Buildr Team is ${code}. It expires in 15 minutes. If you were not expecting this, ignore this email.`,
    { app: "eco" });
  // entryId lets the caller attempt this entry's send synchronously,
  // inside the request — the same discipline as the Dev Library door.
  return { sent: true, entryId: entry.id };
}
export async function verifyEcoCode(email, code) {
  const c = findContributor(email);
  if (!c || !c.email) return false;
  const pg = await otpStore();
  if (pg) {
    const rec = await pg.getEcoOtp(c.email.toLowerCase());
    if (!rec || rec.expires < Date.now() || rec.hash !== sha(String(code))) return false;
    await pg.delEcoOtp(c.email.toLowerCase()); return true;
  }
  const rec = codes.get(c.email.toLowerCase());
  if (!rec || rec.expires < Date.now() || rec.hash !== sha(String(code))) return false;
  codes.delete(c.email.toLowerCase()); return true;
}
// Sessions carry the contributor's sessionEpoch: an access-affecting
// change bumps the epoch and every live eco session dies.
export function signEcoSession(email) {
  const c = findContributor(email); if (!c) return null;
  const payload = Buffer.from(JSON.stringify({ email: c.email, epoch: c.sessionEpoch || 0, eco: 1 })).toString("base64url");
  const sig = createHmac("sha256", SECRET).update(payload).digest("base64url");
  return `${payload}.${sig}`;
}
export function readEcoSession(token) {
  if (!token || !token.includes(".")) return null;
  const [payload, sig] = token.split(".");
  const expect = createHmac("sha256", SECRET).update(payload).digest("base64url");
  if (sig.length !== expect.length || !timingSafeEqual(Buffer.from(sig), Buffer.from(expect))) return null;
  let parsed;
  try { parsed = JSON.parse(Buffer.from(payload, "base64url").toString()); } catch { return null; }
  if (!parsed.eco) return null; // a Dev Library session is not an eco session
  const c = findContributor(parsed.email);
  if (!c || (c.sessionEpoch || 0) !== parsed.epoch) return null;
  return c;
}
