// app/api/c3/signout/route.ts — clears the C3 Admin Hub session.
import "server-only";
import { NextResponse } from "next/server";
import { OTP_COOKIE, SESSION_COOKIE } from "@/lib/c3";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST() {
  const out = NextResponse.json({ ok: true });
  for (const name of [SESSION_COOKIE, OTP_COOKIE]) {
    out.cookies.set(name, "", { httpOnly: true, secure: true, sameSite: "lax", path: "/", maxAge: 0 });
  }
  return out;
}
