/** Step 1 of 20-second onboarding: email -> OTP code sent. */
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
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
      setError("Couldn't send the code — check the email and try again.");
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
    </main>
  );
}
