// Venue-as-data — the whole pattern in one table.
//
// A venue is NOT a 3D model. It is two small tables:
//   Sector { id, name, a0, a1, base }  — angular span around the bowl + base price
//   Ring   { id, name, d0, d1, h0, h1, factor, open }
//          — radial span, height span, price factor, roof/open flag
// Any stadium, arena or concert bowl is instantiated by entering its
// sector survey here. Sector price = base × ring factor.
//
// Pilot data below is a MOCK survey in the shape of a large Barcelona
// football stadium (generic Spanish stand nomenclature). Prices are
// illustrative mock values, not live inventory.

export interface Sector { id: string; name: string; a0: number; a1: number; base: number; color: number }
export interface Ring { id: string; name: string; d0: number; d1: number; h0: number; h1: number; factor: number; open: boolean }

export const VENUE = {
  id: "bcn-pilot-01",
  name: "Barcelona Pilot Venue",
  city: "Barcelona",
  eventTypes: ["football", "concert", "spectator-events"],
  currency: "EUR",
};

export const SECTORS: Sector[] = [
  { id: "tribuna-central", name: "Tribuna Central", a0: 70,  a1: 110, base: 420, color: 0xd94f04 },
  { id: "tribuna-nord",    name: "Tribuna Nord",    a0: 40,  a1: 70,  base: 290, color: 0xe86a1c },
  { id: "tribuna-sud",     name: "Tribuna Sud",     a0: 110, a1: 140, base: 290, color: 0xe86a1c },
  { id: "tribuna-a",       name: "Tribuna",         a0: 22,  a1: 40,  base: 190, color: 0xf08a3c },
  { id: "tribuna-b",       name: "Tribuna",         a0: 140, a1: 158, base: 190, color: 0xf08a3c },
  { id: "lateral-central", name: "Lateral Central", a0: 250, a1: 290, base: 330, color: 0x2e6fb7 },
  { id: "lateral-nord",    name: "Lateral Nord",    a0: 290, a1: 320, base: 240, color: 0x4a8ac4 },
  { id: "lateral-sud",     name: "Lateral Sud",     a0: 220, a1: 250, base: 240, color: 0x4a8ac4 },
  { id: "lateral-a",       name: "Lateral",         a0: 202, a1: 220, base: 180, color: 0x74a8d4 },
  { id: "lateral-b",       name: "Lateral",         a0: 320, a1: 338, base: 180, color: 0x74a8d4 },
  { id: "gol-nord",        name: "Gol Nord",        a0: 338, a1: 382, base: 150, color: 0x3f9e4d },
  { id: "gol-sud",         name: "Gol Sud",         a0: 158, a1: 202, base: 150, color: 0x3f9e4d },
];

export const RINGS: Ring[] = [
  { id: "ring-1", name: "Lower Ring",  d0: 30, d1: 48, h0: 1,  h1: 13, factor: 1.15, open: true },
  { id: "ring-2", name: "Middle Ring", d0: 50, d1: 66, h0: 15, h1: 29, factor: 1.0,  open: true },
  { id: "ring-3", name: "Upper Ring",  d0: 68, d1: 84, h0: 31, h1: 46, factor: 0.8,  open: false },
];

export function sectorPrice(sector: Sector, ring: Ring) {
  return Math.round(sector.base * ring.factor);
}

export function fromPrice(sector: Sector) {
  return Math.min(...RINGS.map((r) => sectorPrice(sector, r)));
}
