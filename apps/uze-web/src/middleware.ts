import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/** Subdomain routing for uzemarkets.com (DevPartner directive,
 *  Phase 2). Inert until GoDaddy DNS points the subdomains at this
 *  deployment and the domains are added to the Vercel project —
 *  every other host passes through untouched.
 *
 *    devpartner.uzemarkets.com  -> the DevPartner portal
 *                                  (/devpartner, locale-aware root)
 *    blog.uzemarkets.com        -> the HIADR Content Desk surface
 *                                  (micro-region pulses)
 *    demo.uzemarkets.com        -> the demo / sandbox environment
 *    uzemarkets.com / anything  -> the primary marketplace UI
 */
export function middleware(request: NextRequest) {
  const host = (request.headers.get("host") ?? "").toLowerCase();
  const { pathname } = request.nextUrl;

  if (host.startsWith("devpartner.")) {
    if (pathname === "/") {
      const url = request.nextUrl.clone();
      url.pathname = "/devpartner";
      return NextResponse.rewrite(url);
    }
    return NextResponse.next();
  }

  if (host.startsWith("blog.")) {
    if (pathname === "/") {
      const url = request.nextUrl.clone();
      url.pathname = "/micro-regions";
      return NextResponse.rewrite(url);
    }
    return NextResponse.next();
  }

  if (host.startsWith("demo.")) {
    if (pathname === "/") {
      const url = request.nextUrl.clone();
      url.pathname = "/demo";
      return NextResponse.rewrite(url);
    }
    return NextResponse.next();
  }

  return NextResponse.next();
}

export const config = {
  // Run on page routes only — never on static assets or the API.
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api/).*)"],
};
