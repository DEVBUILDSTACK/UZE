// app/api/c3/session/route.ts
// C3 Admin Hub — session check for the hub shell. Answers only
// whether the signed session cookie is valid (and its domain, for
// display); the email itself never leaves the server otherwise.
import "server-only";
import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { SESSION_COOKIE, sessionEmail } from "@/lib/c3";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const jar = await cookies();
  const email = sessionEmail(jar.get(SESSION_COOKIE)?.value);
  if (!email) return NextResponse.json({ authed: false });
  return NextResponse.json({ authed: true, domain: email.slice(email.lastIndexOf("@") + 1) });
}
