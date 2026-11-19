"use client";

/** C3 Admin Hub shell — the hub is its own site behind the gate
 *  (the DC3 pattern James pointed to: a public front end, and a
 *  whole console site behind one bottom-of-navigation entry).
 *  Unauthenticated visitors get the corporate-email OTP gate;
 *  authenticated partners get the hub frame — its own left
 *  navigation: Talent · Enterprise Services · Treasury. */

import { useCallback, useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Wordmark from "@/components/wordmark";

/* Hub navigation (James, 2026-11-19): the three sections with
 * Treasury at the top; UZE Intelligence (API keys) above Settings;
 * Settings — holding KYC and KYB — is the bottom tab. */
const NAV = [
  { href: "/c3-admin-hub/treasury", label: "Treasury" },
  { href: "/c3-admin-hub/talent", label: "Talent" },
  { href: "/c3-admin-hub/enterprise-services", label: "Enterprise Services" },
];
const NAV_LOWER = [
  { href: "/c3-admin-hub/uze-intelligence", label: "UZE Intelligence" },
  { href: "/c3-admin-hub/settings", label: "Settings" },
];

type GateStep = "email" | "code";

export default function C3Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [domain, setDomain] = useState("");
  const [step, setStep] = useState<GateStep>("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const check = useCallback(async () => {
    try {
      const r = await fetch("/api/c3/session", { cache: "no-store" });
      const d = (await r.json()) as { authed?: boolean; domain?: string };
      setAuthed(Boolean(d.authed));
      if (d.domain) setDomain(d.domain);
    } catch {
      setAuthed(false);
    }
  }, []);

  useEffect(() => {
    void check();
  }, [check]);

  async function requestCode(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const r = await fetch("/api/c3/request-code", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const d = (await r.json()) as { ok?: boolean; message?: string };
      if (!r.ok || !d.ok) {
        setError(d.message ?? "The code could not be sent.");
      } else {
        setStep("code");
        setNotice("Code sent. It expires in 10 minutes.");
      }
    } catch {
      setError("The code could not be sent. Try again.");
    } finally {
      setBusy(false);
    }
  }

  async function verify(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const r = await fetch("/api/c3/verify", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email, code }),
      });
      const d = (await r.json()) as { ok?: boolean; message?: string };
      if (!r.ok || !d.ok) {
        setError(d.message ?? "That code does not match.");
      } else {
        await check();
      }
    } catch {
      setError("Verification failed. Try again.");
    } finally {
      setBusy(false);
    }
  }

  async function signOut() {
    await fetch("/api/c3/signout", { method: "POST" }).catch(() => {});
    setAuthed(false);
    setStep("email");
    setCode("");
  }

  if (authed === null) {
    return (
      <main className="c3-main">
        <p className="c3-muted">Checking your session…</p>
      </main>
    );
  }

  if (!authed) {
    return (
      <main className="c3-gate-wrap">
        <div className="c3-gate">
          <p className="c3-eyebrow">Command &amp; Control Console</p>
          <h1>C3 Admin Hub</h1>
          <p className="c3-muted">
            For business entity owner partners and their officers. Sign in
            with your corporate email — a one-time code gates the hub.
            Consumer mail (Gmail, Yahoo, and similar) is not accepted.
          </p>
          {step === "email" ? (
            <form onSubmit={requestCode} className="c3-form">
              <label htmlFor="c3-email">Corporate email</label>
              <input
                id="c3-email"
                type="email"
                required
                autoComplete="email"
                placeholder="you@yourcompany.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              <button className="c3-btn" type="submit" disabled={busy}>
                {busy ? "Sending…" : "Email me a code"}
              </button>
            </form>
          ) : (
            <form onSubmit={verify} className="c3-form">
              <label htmlFor="c3-code">One-time code</label>
              <input
                id="c3-code"
                inputMode="numeric"
                autoComplete="one-time-code"
                required
                maxLength={6}
                placeholder="123456"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
              />
              <button className="c3-btn" type="submit" disabled={busy}>
                {busy ? "Checking…" : "Enter the hub"}
              </button>
              <button
                type="button"
                className="c3-linkbtn"
                onClick={() => {
                  setStep("email");
                  setError("");
                  setNotice("");
                }}
              >
                Use a different email
              </button>
            </form>
          )}
          {notice && <p className="c3-notice">{notice}</p>}
          {error && <p className="c3-error">{error}</p>}
        </div>
      </main>
    );
  }

  return (
    <div className="c3-wrap">
      <aside className="c3-rail">
        <Link className="c3-rail-brand" href="/c3-admin-hub" aria-label="C3 Admin Hub — home">
          <Wordmark />
        </Link>
        <p className="c3-eyebrow">C3 Admin Hub</p>
        <nav className="c3-nav">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={pathname === item.href ? "active" : undefined}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <nav className="c3-nav c3-nav-lower">
          {NAV_LOWER.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={pathname === item.href ? "active" : undefined}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="c3-rail-foot">
          <p className="c3-muted">Signed in · {domain}</p>
          <button type="button" className="c3-linkbtn" onClick={signOut}>
            Sign out
          </button>
          <p>
            <a href="https://uzemarkets.com">← Back to UZEmarkets</a>
          </p>
        </div>
      </aside>
      <main className="c3-main">{children}</main>
    </div>
  );
}
