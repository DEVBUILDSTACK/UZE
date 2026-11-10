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
/** Host discipline for the dev docs (James, 2026-11-10): the
 *  DevPartner portal lives ONLY on devpartner.uzemarkets.com (and
 *  its stable Vercel alias). The same paths on the blog host or the
 *  main organizational domain redirect there permanently - "blog"
 *  never appears in a dev-docs URL, and uzemarkets.com stays the
 *  default organizational page and app. */
const DEV_DOCS_REDIRECT_HOSTS = new Set([
  "uzemarkets.com",
  "www.uzemarkets.com",
  "uze-web-uze2.vercel.app",
]);

export function middleware(request: NextRequest) {
  const host = (request.headers.get("host") ?? "").toLowerCase();
  const { pathname, search } = request.nextUrl;

  if (
    (host.startsWith("blog.") || DEV_DOCS_REDIRECT_HOSTS.has(host)) &&
    (pathname === "/devpartner" || pathname.startsWith("/devpartner/"))
  ) {
    return NextResponse.redirect(
      new URL(pathname + search, "https://devpartner.uzemarkets.com"),
      308,
    );
  }

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
