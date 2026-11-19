import "server-only";
import { createHmac, randomInt, timingSafeEqual } from "node:crypto";

/** C3 Admin Hub gate — corporate-email OTP (James, 2026-11-19).
 *
 *  The hub serves business entity owner partners and their officers,
 *  so the gate accepts corporate domains only: consumer/free mail
 *  (Gmail, Yahoo, and their class) is refused before any code is sent.
 *
 *  Stateless by design: the one-time code is never stored. The
 *  request step signs (email, code, expiry) into an httpOnly cookie;
 *  the verify step recomputes the signature over the submitted code.
 *  A verified sign-in mints a second signed cookie (8 hours).
 *
 *  Secrets arrive via the environment, never the repo:
 *  C3_OTP_SECRET (preferred) — RESEND_API_KEY is the fallback signing
 *  secret, and is always required for the send itself. When neither
 *  is configured the routes answer an honest 503, following the
 *  house pattern set by /api/session. */

const CONSUMER_DOMAINS = new Set([
  "gmail.com", "googlemail.com",
  "yahoo.com", "yahoo.co.uk", "yahoo.ca", "yahoo.com.au", "ymail.com", "rocketmail.com",
  "hotmail.com", "hotmail.co.uk", "outlook.com", "live.com", "msn.com",
  "aol.com", "aim.com",
  "icloud.com", "me.com", "mac.com",
  "proton.me", "protonmail.com", "pm.me",
  "gmx.com", "gmx.net", "mail.com", "inbox.com", "hushmail.com",
  "yandex.com", "yandex.ru", "mail.ru",
  "qq.com", "163.com", "126.com",
  "zoho.com", "zohomail.com", "fastmail.com", "tutanota.com", "tuta.com",
]);

export function isCorporateEmail(email: string): boolean {
  const at = email.lastIndexOf("@");
  if (at < 1) return false;
  const domain = email.slice(at + 1).toLowerCase();
  if (!domain.includes(".")) return false;
  if (CONSUMER_DOMAINS.has(domain)) return false;
  // Subdomains of consumer providers are consumer mail too.
  for (const d of CONSUMER_DOMAINS) {
    if (domain.endsWith("." + d)) return false;
  }
  return true;
}

export function validEmailShape(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) && email.length <= 254;
}

function secret(): string | null {
  return process.env.C3_OTP_SECRET || process.env.RESEND_API_KEY || null;
}

export function gateConfigured(): boolean {
  return Boolean(secret() && process.env.RESEND_API_KEY);
}

function sign(payload: string): string | null {
  const key = secret();
  if (!key) return null;
  return createHmac("sha256", key).update(payload).digest("base64url");
}

function eq(a: string, b: string): boolean {
  const ba = Buffer.from(a);
  const bb = Buffer.from(b);
  return ba.length === bb.length && timingSafeEqual(ba, bb);
}

const b64 = (s: string) => Buffer.from(s, "utf8").toString("base64url");
const unb64 = (s: string) => Buffer.from(s, "base64url").toString("utf8");

export const OTP_COOKIE = "c3_otp";
export const SESSION_COOKIE = "c3_session";
export const OTP_TTL_MS = 10 * 60 * 1000;
export const SESSION_TTL_MS = 8 * 60 * 60 * 1000;

export function newCode(): string {
  return String(randomInt(0, 1_000_000)).padStart(6, "0");
}

export function otpCookieValue(email: string, code: string, now = Date.now()): string | null {
  const exp = now + OTP_TTL_MS;
  const sig = sign(`otp|${email}|${code}|${exp}`);
  if (!sig) return null;
  return `v1.${b64(email)}.${exp}.${sig}`;
}

export function verifyOtpCookie(value: string | undefined, email: string, code: string, now = Date.now()): boolean {
  if (!value) return false;
  const parts = value.split(".");
  if (parts.length !== 4 || parts[0] !== "v1") return false;
  const [, b64email, expStr, sig] = parts;
  const exp = Number(expStr);
  if (!Number.isFinite(exp) || exp < now) return false;
  if (unb64(b64email) !== email) return false;
  const expect = sign(`otp|${email}|${code}|${exp}`);
  return expect !== null && eq(sig, expect);
}

export function sessionCookieValue(email: string, now = Date.now()): string | null {
  const exp = now + SESSION_TTL_MS;
  const sig = sign(`session|${email}|${exp}`);
  if (!sig) return null;
  return `v1.${b64(email)}.${exp}.${sig}`;
}

export function sessionEmail(value: string | undefined, now = Date.now()): string | null {
  if (!value) return null;
  const parts = value.split(".");
  if (parts.length !== 4 || parts[0] !== "v1") return null;
  const [, b64email, expStr, sig] = parts;
  const exp = Number(expStr);
  if (!Number.isFinite(exp) || exp < now) return null;
  const email = unb64(b64email);
  const expect = sign(`session|${email}|${exp}`);
  if (expect === null || !eq(sig, expect)) return null;
  return email;
}
