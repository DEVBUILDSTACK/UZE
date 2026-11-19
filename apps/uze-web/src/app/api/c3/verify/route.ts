// app/api/c3/verify/route.ts
// C3 Admin Hub — step 2 of the gate: check the submitted code
// against the signed cookie from step 1; on success, mint the
// 8-hour session cookie and clear the OTP cookie.
import "server-only";
import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import {
  OTP_COOKIE,
  SESSION_COOKIE,
  SESSION_TTL_MS,
  sessionCookieValue,
  verifyOtpCookie,
} from "@/lib/c3";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  let email = "";
  let code = "";
  try {
    const body = (await req.json()) as { email?: unknown; code?: unknown };
    email = String(body.email ?? "").trim().toLowerCase();
    code = String(body.code ?? "").trim();
  } catch {
    return NextResponse.json({ ok: false, error: "bad_request" }, { status: 400 });
  }
  if (!/^\d{6}$/.test(code)) {
    return NextResponse.json(
      { ok: false, error: "invalid_code", message: "Enter the 6-digit code from the email." },
      { status: 400 },
    );
  }
  const jar = await cookies();
  const otp = jar.get(OTP_COOKIE)?.value;
  if (!verifyOtpCookie(otp, email, code)) {
    return NextResponse.json(
      { ok: false, error: "code_mismatch", message: "That code does not match, or it has expired. Request a new one." },
      { status: 401 },
    );
  }
  const session = sessionCookieValue(email);
  if (!session) {
    return NextResponse.json({ ok: false, error: "not_configured" }, { status: 503 });
  }
  const out = NextResponse.json({ ok: true });
  out.cookies.set(SESSION_COOKIE, session, {
    httpOnly: true,
    secure: true,
    sameSite: "lax",
    path: "/",
    maxAge: Math.floor(SESSION_TTL_MS / 1000),
  });
  out.cookies.set(OTP_COOKIE, "", { httpOnly: true, secure: true, sameSite: "lax", path: "/", maxAge: 0 });
  return out;
}
