/** Step 5: the share card — referral code + copy link.
 *  Team TODO: render the QR (qrcode npm package) encoding the referral URL. */
"use client";
import { useEffect, useState } from "react";
import { loadToken } from "@/lib/onboard";

export default function OnboardDone() {
  const [handle, setHandle] = useState("");
  const [code, setCode] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadToken();
    setHandle(sessionStorage.getItem("uze_onboard_handle") ?? "");
    setCode(sessionStorage.getItem("uze_referral_code") ?? "");
  }, []);

  const referralUrl =
    typeof window !== "undefined" && code
      ? `${window.location.origin}/onboard/profile?ref=${code}`
      : "";

  async function copy() {
    if (!referralUrl) return;
    await navigator.clipboard.writeText(referralUrl);
    setCopied(true);
  }

  return (
    <main>
      <h1>You&apos;re in{handle ? `, @${handle}` : ""}.</h1>
      {/* TODO: QR code rendering the referralUrl (qrcode package) */}
      <div>
        <p>Your referral code</p>
        <strong>{code}</strong>
      </div>
      <p>Share your profile — every signup with your code earns you rewards.</p>
      <button onClick={copy}>{copied ? "Copied!" : "Copy link"}</button>
    </main>
  );
}
