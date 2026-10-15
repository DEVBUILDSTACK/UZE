/** Step 2: enter the 6-digit OTP code -> JWT session. */
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { verifyOtp } from "@/lib/onboard";

export default function OnboardVerify() {
  const router = useRouter();
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const email = sessionStorage.getItem("uze_onboard_email") ?? "";
      await verifyOtp(email, code);
      router.push("/onboard/handle");
    } catch {
      setError("Invalid or expired code — try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <h1>Check your email</h1>
      <p>Enter the 6-digit code. It expires in 5 minutes.</p>
      <form onSubmit={submit}>
        <input
          inputMode="numeric"
          required
          minLength={6}
          maxLength={6}
          placeholder="123456"
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
        />
        <button type="submit" disabled={busy}>
          {busy ? "Verifying…" : "Verify"}
        </button>
      </form>
      {error && <p role="alert">{error}</p>}
    </main>
  );
}
