// app/api/c3/request-code/route.ts
// C3 Admin Hub — step 1 of the corporate-email OTP gate.
// Validates the address (corporate domains only), emails a 6-digit
// code via Resend, and signs (email, code, expiry) into an httpOnly
// cookie. The code itself is never stored server-side.
// House rules carried in: the mandatory Resend user-agent (without
// it the API answers 403 error 1010), and the standing BCC to
// James's Gmail of record on every send.
import "server-only";
import { NextResponse } from "next/server";
import {
  OTP_COOKIE,
  OTP_TTL_MS,
  gateConfigured,
  isCorporateEmail,
  newCode,
  otpCookieValue,
  validEmailShape,
} from "@/lib/c3";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const FROM = "UZE Markets Desk <desk@uzemarkets.com>";
const BCC = "jsondealzapp@gmail.com";

export async function POST(req: Request) {
  if (!gateConfigured()) {
    return NextResponse.json(
      { ok: false, error: "not_configured", message: "The C3 Admin Hub gate is not configured yet." },
      { status: 503 },
    );
  }
  let email = "";
  try {
    const body = (await req.json()) as { email?: unknown };
    email = String(body.email ?? "").trim().toLowerCase();
  } catch {
    return NextResponse.json({ ok: false, error: "bad_request" }, { status: 400 });
  }
  if (!validEmailShape(email)) {
    return NextResponse.json(
      { ok: false, error: "invalid_email", message: "Enter a valid email address." },
      { status: 400 },
    );
  }
  if (!isCorporateEmail(email)) {
    return NextResponse.json(
      {
        ok: false,
        error: "consumer_domain",
        message:
          "The C3 Admin Hub is for business entity owner partners and their officers. Use your corporate email — consumer mail (Gmail, Yahoo, and similar) is not accepted.",
      },
      { status: 400 },
    );
  }

  const code = newCode();
  const cookie = otpCookieValue(email, code);
  if (!cookie) {
    return NextResponse.json({ ok: false, error: "not_configured" }, { status: 503 });
  }

  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      authorization: `Bearer ${process.env.RESEND_API_KEY}`,
      "content-type": "application/json",
      "user-agent": "uze-web-c3-hub/1.0",
    },
    body: JSON.stringify({
      from: FROM,
      to: [email],
      bcc: [BCC],
      subject: "Your C3 Admin Hub code",
      text: `Your one-time code for the C3 Admin Hub is ${code}.\n\nIt expires in 10 minutes. If you did not request it, ignore this email.\n\nUZEmarkets`,
      html: `<div style="font-family:Georgia,serif;color:#1a1a1a;background:#f5f2ee;padding:28px">
  <p style="font-size:13px;letter-spacing:2px;margin:0 0 14px"><span style="color:#ff6b00;font-weight:700">UZE</span>markets · C3 ADMIN HUB</p>
  <p style="font-size:16px;margin:0 0 10px">Your one-time code is</p>
  <p style="font-size:34px;letter-spacing:8px;margin:0 0 14px"><strong>${code}</strong></p>
  <p style="font-size:14px;color:#6b655e;margin:0">It expires in 10 minutes. If you did not request it, ignore this email.</p>
</div>`,
    }),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    return NextResponse.json(
      { ok: false, error: "send_failed", message: "The code could not be sent. Try again.", detail: detail.slice(0, 200) },
      { status: 502 },
    );
  }

  const out = NextResponse.json({ ok: true, email });
  out.cookies.set(OTP_COOKIE, cookie, {
    httpOnly: true,
    secure: true,
    sameSite: "lax",
    path: "/",
    maxAge: Math.floor(OTP_TTL_MS / 1000),
  });
  return out;
}
