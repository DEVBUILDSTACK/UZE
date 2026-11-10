/** Step 1 of 20-second onboarding: email -> OTP code sent. */
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Wordmark from "@/components/wordmark";
import { requestOtp } from "@/lib/onboard";

export default function OnboardEmail() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await requestOtp(email);
      sessionStorage.setItem("uze_onboard_email", email.trim().toLowerCase());
      router.push("/onboard/verify");
    } catch {
      setError("Couldn't send the code right now. You don't need one to look around — browse the public site below.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <h1>Create your UZE profile in 20 seconds</h1>
      <p>Enter your email — we&apos;ll send a login code. No password, ever.</p>
      <form onSubmit={submit}>
        <input
          type="email"
          required
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <button type="submit" disabled={busy}>
          {busy ? "Sending…" : "Send code"}
        </button>
      </form>
      {error && <p role="alert">{error}</p>}
      <p className="note">
        Questions or team access? Email:{" "}
        <a href="mailto:UZEmarket@uzemarkets.com">
          <span className="addr-ink">UZEmarket@</span>
          <Wordmark />
          <span className="addr-ink">.com</span>
        </a>
      </p>
      <p>
        Just evaluating with the team?{" "}
        <Link href="/">Browse the public site first</Link> — no email
        needed to look around.
      </p>
    </main>
  );
}
