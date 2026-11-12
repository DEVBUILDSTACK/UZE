import type { Metadata } from "next";
import VenueSelector from "@/components/venue-selector";
import { VENUE } from "@/lib/venue-data";

export const metadata: Metadata = {
  title: "Venue Tickets | UZEmarkets",
  description:
    "UZE Venue Ticketing (demo): a venue-as-data 3D seat selector for sports, music, and large spectator events. Barcelona pilot venue. Mock-up — no live inventory, no real settlement.",
};

export default function VenuePage() {
  return (
    <main style={{ maxWidth: 1060, margin: "0 auto", padding: "28px 20px 48px" }}>
      <p style={{ fontFamily: "Helvetica, Arial, sans-serif", fontSize: 11, letterSpacing: ".14em", textTransform: "uppercase", opacity: 0.65 }}>
        Tickets · B2C demo
      </p>
      <h1 style={{ margin: "6px 0 8px" }}>
        <span style={{ color: "#ff6b00" }}>UZE</span> Venue Ticketing
      </h1>
      <p style={{ maxWidth: 720, lineHeight: 1.55 }}>
        A seat selector where the venue is <strong>data, not a model</strong>: sectors and rings
        are small tables, and the stadium is generated from them — so the same selector serves a
        football stadium, an arena, or a concert bowl. Pilot venue: {VENUE.name}, {VENUE.city}.
      </p>
      <p style={{ fontFamily: "Helvetica, Arial, sans-serif", fontSize: 12, background: "#1a1a1a", color: "#f5f2ee", display: "inline-block", padding: "6px 11px", borderRadius: 999, letterSpacing: ".1em" }}>
        🟡 DEMO — MOCK INVENTORY · MOCK PRICES · NO REAL SETTLEMENT
      </p>
      <VenueSelector />
    </main>
  );
}
