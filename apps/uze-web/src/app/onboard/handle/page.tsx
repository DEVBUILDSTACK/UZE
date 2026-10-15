/** Step 3: pick a handle — inline availability check. */
"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { checkHandle, loadToken } from "@/lib/onboard";

export default function OnboardHandle() {
  const router = useRouter();
  const [handle, setHandle] = useState("");
  const [state, setState] = useState<"idle" | "checking" | "ok" | "taken" | "invalid">("idle");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!loadToken()) router.push("/onboard");
  }, [router]);

  useEffect(() => {
    const h = handle.trim().toLowerCase();
    if (timer.current) clearTimeout(timer.current);
    if (!h) {
      setState("idle");
      return;
    }
    setState("checking");
    timer.current = setTimeout(async () => {
      try {
        const { available } = await checkHandle(h);
        setState(available ? "ok" : "taken");
      } catch {
        setState("invalid");
      }
    }, 400);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [handle]);

  function next(e: React.FormEvent) {
    e.preventDefault();
    if (state !== "ok") return;
    sessionStorage.setItem("uze_onboard_handle", handle.trim().toLowerCase());
    router.push("/onboard/profile");
  }

  return (
    <main>
      <h1>Pick your handle</h1>
      <p>3–30 characters: lowercase letters, numbers, underscore.</p>
      <form onSubmit={next}>
        <input
          required
          placeholder="yourhandle"
          value={handle}
          onChange={(e) => setHandle(e.target.value.toLowerCase())}
        />
        <button type="submit" disabled={state !== "ok"}>
          Continue
        </button>
      </form>
      {state === "checking" && <p>Checking…</p>}
      {state === "ok" && <p>@{handle.trim()} is available.</p>}
      {state === "taken" && <p role="alert">That handle is taken — try another.</p>}
      {state === "invalid" && <p role="alert">Invalid handle format.</p>}
    </main>
  );
}
