/** GIRA concierge guidance — evaluation preview.
 *
 * Runs entirely in the browser so the GIRA path can be clicked through
 * end to end today: browse by category, look at experiences, ask GIRA.
 * The experiences below are SAMPLES for evaluation. At full launch this
 * surface wires to the live service (GET /events/, GET /listings/) and
 * GIRA answers over real listings. */
"use client";

import { useMemo, useState } from "react";
import Link from "next/link";

const CATEGORIES = ["All", "Talent", "Tickets", "Touring", "Stay"] as const;

interface Experience {
  title: string;
  category: (typeof CATEGORIES)[number];
  city: string;
  blurb: string;
}

const EXPERIENCES: Experience[] = [
  {
    title: "Rooftop Cinema Night",
    category: "Tickets",
    city: "Miami",
    blurb: "Open-air screening above the city, doors at sunset.",
  },
  {
    title: "Open Mic & Producers Showcase",
    category: "Talent",
    city: "Washington DC",
    blurb: "New artists on a real stage, scouted by local bookers.",
  },
  {
    title: "Old Town Walking Tour with a Local Host",
    category: "Touring",
    city: "Barcelona",
    blurb: "Two hours, small group, the streets the guidebooks skip.",
  },
  {
    title: "Beachfront Stay — 2 Nights",
    category: "Stay",
    city: "Rio de Janeiro",
    blurb: "Wake up on the sand, breakfast included.",
  },
  {
    title: "Sunrise Surf Session (All Levels)",
    category: "Tickets",
    city: "Costa Rica",
    blurb: "Board, instructor, and the best hour of the day.",
  },
  {
    title: "Boutique Stay near the Venue District",
    category: "Stay",
    city: "Ibiza",
    blurb: "Walk to the show, sleep somewhere quiet afterwards.",
  },
  {
    title: "Gallery Night: Local Artists",
    category: "Talent",
    city: "Miami",
    blurb: "Meet the artists, see new work first.",
  },
  {
    title: "Food Market Crawl with a Chef",
    category: "Touring",
    city: "São Paulo",
    blurb: "Eat your way through the market with someone who knows it.",
  },
];

const SUGGESTIONS = [
  "What's on in Miami?",
  "Find me a stay near the beach",
  "I want live music and new artists",
  "Something for surfers",
];

function giraAnswer(q: string): string {
  const s = q.toLowerCase();
  const names = (list: Experience[]) =>
    list.map((e) => `${e.title} (${e.city})`).join("; ");
  if (s.includes("miami")) {
    return `In Miami on this preview: ${names(
      EXPERIENCES.filter((e) => e.city === "Miami"),
    )}. At launch I'll search live Miami listings the same way.`;
  }
  if (s.includes("stay") || s.includes("hotel") || s.includes("beach")) {
    return `For stays, look at: ${names(
      EXPERIENCES.filter((e) => e.category === "Stay"),
    )}. Tell me a city and dates at launch and I'll hold real options.`;
  }
  if (s.includes("music") || s.includes("artist") || s.includes("concert")) {
    return `For music and artists: ${names(
      EXPERIENCES.filter((e) => e.category === "Talent"),
    )}. That's the Talent side of UZE — artists, showcases, galleries.`;
  }
  if (s.includes("surf")) {
    return `For surfers: ${names(
      EXPERIENCES.filter((e) => e.title.toLowerCase().includes("surf")),
    )}. Surf is one of our lead sports — sessions, viewing, and stays near the break.`;
  }
  if (s.includes("tour") || s.includes("walk") || s.includes("food")) {
    return `For touring: ${names(
      EXPERIENCES.filter((e) => e.category === "Touring"),
    )}. Local hosts, small groups, real neighborhoods.`;
  }
  return "I'm GIRA, your UZE concierge. In this preview I can point you to sample experiences by city or category — try a suggestion below. At full launch I'll answer over live events, tickets, touring and stays, and book with your profile.";
}

export default function GuidancePage() {
  const [category, setCategory] =
    useState<(typeof CATEGORIES)[number]>("All");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(
    "Ask me what's on, where to stay, or what fits your night — or tap a suggestion.",
  );

  const shown = useMemo(
    () =>
      category === "All"
        ? EXPERIENCES
        : EXPERIENCES.filter((e) => e.category === category),
    [category],
  );

  function ask(e?: React.FormEvent, preset?: string) {
    e?.preventDefault();
    const q = (preset ?? question).trim();
    if (!q) return;
    setAnswer(giraAnswer(q));
    if (preset) setQuestion(preset);
  }

  return (
    <main>
      <h1>GIRA Guidance</h1>
      <p>
        Concierge guidance for your next experience — talent, tickets,
        touring and stay, in one place.
      </p>
      <p className="note">
        Preview for evaluation: the experiences below are samples. Live
        listings arrive with the full service launch.
      </p>

      <div className="chips" role="group" aria-label="Filter by category">
        {CATEGORIES.map((c) => (
          <button
            key={c}
            className="chip"
            aria-pressed={category === c}
            onClick={() => setCategory(c)}
          >
            {c}
          </button>
        ))}
      </div>

      <ul className="cards">
        {shown.map((e) => (
          <li key={e.title} className="card">
            <h3>{e.title}</h3>
            <p className="meta">
              {e.category} · {e.city}
            </p>
            <p>{e.blurb}</p>
          </li>
        ))}
      </ul>

      <section aria-label="UZEguidance priced markets">
        <h2>UZEguidance priced markets</h2>
        <p>
          No posted prices — not here, not anywhere on UZEmarkets. The
          levels for <strong>UZEBuilder</strong>, <strong>UZEaffiliate</strong>{" "}
          and <strong>UZEaffiliate actively onramped uzing TradeLayer or
          SigLayer</strong> are set by an autonomous guidance market: the
          market bids the levels, and we honor them prospectively — only
          for KYB entities and KYC partner agents, and only for signups
          between <strong>November 15, 2026</strong> and{" "}
          <strong>January 12, 2027 at 10:59 PM PST</strong>.
        </p>
        <p>
          Signing up whitelists one self-custodial wallet — Solana, NEAR,
          Robinhood, Ink or LightLink — for the 2027 B2B and B2C event
          offerings, the secondary UZEticket tech offerings, and the
          music festival Frontier NFT collectibles paired as payment tech
          innovation from the L2Launch Launchpad.{" "}
          <Link href="/alpha">Join the alpha signup list</Link>.
        </p>
      </section>

      <section className="ask" aria-label="Ask GIRA">
        <h2>Ask GIRA</h2>
        <p>{answer}</p>
        <form onSubmit={(e) => ask(e)}>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Try: What's on in Miami?"
            aria-label="Ask GIRA a question"
          />
          <button type="submit">Ask</button>
        </form>
        <div className="chips">
          {SUGGESTIONS.map((s) => (
            <button key={s} className="chip" onClick={() => ask(undefined, s)}>
              {s}
            </button>
          ))}
        </div>
      </section>

      <p>
        Like what you see? <Link href="/onboard">Create your UZE profile</Link>{" "}
        — or head back <Link href="/">home</Link>.
      </p>
    </main>
  );
}
