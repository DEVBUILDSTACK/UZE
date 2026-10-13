import { NextResponse } from "next/server";

/** Container health endpoint — target of the Dockerfile HEALTHCHECK. */
export async function GET() {
  return NextResponse.json({ status: "ok", service: "uze-web" });
}
