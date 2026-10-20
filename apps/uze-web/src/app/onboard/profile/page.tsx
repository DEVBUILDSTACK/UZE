/** Step 4: bio + interests -> create the profile (mints referral code). */
"use client";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { createProfile, loadToken } from "@/lib/onboard";

const SUGGESTED = ["F1", "VIP", "Concerts", "Festivals", "DJ sets", "Football"];

function OnboardProfileForm() {
  const router = useRouter();
  const search = useSearchParams();
  const [bio, setBio] = useState("");
  const [interests, setInterests] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!loadToken()) router.push("/onboard");
  }, [router]);

  function toggle(tag: string) {
    setInterests((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag].slice(0, 10)
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const handle = sessionStorage.getItem("uze_onboard_handle") ?? "";
      const referredBy = search.get("ref") || sessionStorage.getItem("uze_referred_by") || undefined;
      const { referralCode } = await createProfile({
        handle,
        bio,
        interests,
        referredBy,
      });
      sessionStorage.setItem("uze_referral_code", referralCode);
      router.push("/onboard/done");
    } catch {
      setError("Couldn't create the profile — try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <h1>Almost done</h1>
      <p>Add a bio and pick what you&apos;re into.</p>
      <form onSubmit={submit}>
        <textarea
          placeholder="Add a description"
          maxLength={120}
          value={bio}
          onChange={(e) => setBio(e.target.value)}
        />
        <p>{bio.length}/120</p>
        <div>
          {SUGGESTED.map((tag) => (
            <button
              key={tag}
              type="button"
              aria-pressed={interests.includes(tag)}
              onClick={() => toggle(tag)}
            >
              {tag}
            </button>
          ))}
        </div>
        <button type="submit" disabled={busy}>
          {busy ? "Creating…" : "Create profile"}
        </button>
      </form>
      {error && <p role="alert">{error}</p>}
    </main>
  );
}

export default function OnboardProfile() {
  return (
    <Suspense fallback={null}>
      <OnboardProfileForm />
    </Suspense>
  );
}
