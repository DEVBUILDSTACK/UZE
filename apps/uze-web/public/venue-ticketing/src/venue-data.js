// Venue-as-data — the whole pattern in one table.
//
// A venue is NOT a 3D model. It is two small tables:
//   Sector { id, name, a0, a1, base }  — angular span around the bowl + base price
//   Ring   { id, name, d0, d1, h0, h1, factor, open }
//          — radial span, height span, price factor, roof/open flag
// Any stadium, arena or concert bowl is instantiated by entering its
// sector survey here. Sector price = base × ring factor.
//
// Pilot data below is a MOCK survey in the shape of a large Brazilian
// football stadium (Tribuna / Lateral / Gol stand nomenclature). Prices are
// illustrative mock values, not live inventory.

export const VENUE = {
  id: "bcn-pilot-01",
  name: "Estádio Beira-Rio — Demo Survey",
  city: "Porto Alegre",
  eventTypes: ["football", "concert", "spectator-events"],
  currency: "EUR",
};

export const SECTORS = [
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

export const RINGS = [
  { id: "ring-1", name: "Lower Ring",  d0: 30, d1: 48, h0: 1,  h1: 13, factor: 1.15, open: true },
  { id: "ring-2", name: "Middle Ring", d0: 50, d1: 66, h0: 15, h1: 29, factor: 1.0,  open: true },
  { id: "ring-3", name: "Upper Ring",  d0: 68, d1: 84, h0: 31, h1: 46, factor: 0.8,  open: false },
];

export function sectorPrice(sector, ring) {
  return Math.round(sector.base * ring.factor);
}

export function fromPrice(sector, rings = RINGS) {
  return Math.min(...rings.map((r) => sectorPrice(sector, r)));
}

// ---------------------------------------------------------------------------
// EVENTS — the Brazil play-market demo set: soccer, music, tech convention.
// Each event swaps the sector table (and optionally rings/currency/venue);
// the selector machinery is identical. Prices are mock.
// ---------------------------------------------------------------------------
export const EVENTS = [
  {
    id: "soccer", tab: "⚽ Soccer", kind: "soccer", currency: "R$",
    venue: "Estádio Beira-Rio — Demo Survey", city: "Porto Alegre",
    ringLabel: "Ring", centerColor: 0x2f7d32,
    banner: "<strong>Internacional</strong> (Porto Alegre) vs <strong>São Paulo FC</strong> · January 2027 · Venue selector demo for the Brazil focus",
    receipt: "Internacional vs São Paulo FC · January 2027 (demo fixture)",
    emName: "Internacional vs São Paulo FC", emFocus: { sector: "Tribuna Central", ring: "Lower Ring" },
    sectors: SECTORS, rings: null,
    card: `<div class="team home"><span class="abbr">INTER</span><span class="tname">Internacional</span><span class="tcity">Porto Alegre</span></div>
      <div class="vs">VS<br><span>JAN<br>2027</span></div>
      <div class="team away"><span class="abbr">SPFC</span><span class="tname">São Paulo FC</span><span class="tcity">São Paulo</span></div>`,
  },
  {
    id: "music", tab: "🎵 Music", kind: "music", currency: "R$",
    venue: "Arena Bowl — Demo Survey", city: "Porto Alegre",
    ringLabel: "Tier", centerColor: 0x1c1c22,
    banner: "🎵 <strong>Porto Alegre Music Nights</strong> · May 2027 · Arena bowl selector — music &amp; large spectator events",
    receipt: "Porto Alegre Music Nights · May 2027 (demo event)",
    emName: "Porto Alegre Music Nights",
    sectors: [
      { id: "front-stage", name: "Palco — Front Stage", a0: 70, a1: 110, base: 690, color: 0x7a3fa0 },
      { id: "pista-prem-a", name: "Pista Premium · North", a0: 40, a1: 70, base: 420, color: 0x9a5fc0 },
      { id: "pista-prem-b", name: "Pista Premium · South", a0: 110, a1: 140, base: 420, color: 0x9a5fc0 },
      { id: "arq-a", name: "Arquibancada · North", a0: 22, a1: 40, base: 240, color: 0xb08fd0 },
      { id: "arq-b", name: "Arquibancada · South", a0: 140, a1: 158, base: 240, color: 0xb08fd0 },
      { id: "camarote", name: "Camarote VIP", a0: 250, a1: 290, base: 890, color: 0xc9a227 },
      { id: "pista-a", name: "Pista · North", a0: 202, a1: 220, base: 290, color: 0x5f7fc0 },
      { id: "pista-b", name: "Pista · South", a0: 320, a1: 338, base: 290, color: 0x5f7fc0 },
      { id: "fundo-a", name: "Fundo — Back Bowl · North", a0: 158, a1: 202, base: 210, color: 0x4a9e6d },
      { id: "fundo-b", name: "Fundo — Back Bowl · South", a0: 338, a1: 382, base: 210, color: 0x4a9e6d },
    ],
    rings: null,
    card: `<div class="team home" style="background:#7a3fa0"><span class="abbr">MUSIC</span><span class="tname">Porto Alegre Music Nights</span><span class="tcity">Arena Bowl</span></div>
      <div class="vs">LIVE<br><span>MAY<br>2027</span></div>
      <div class="team away"><span class="abbr">🎵</span><span class="tname">Headliner TBA</span><span class="tcity">Porto Alegre</span></div>`,
  },
  {
    id: "summit", tab: "🎤 Tech Convention", kind: "summit", currency: "R$",
    venue: "Cais Embarcadero — Demo Survey", city: "Porto Alegre",
    ringLabel: "Pass tier", centerColor: 0x9aa0a8,
    banner: "🎤 <strong>South Summit Brazil 2027</strong> · April 14–16, 2027 · Cais Embarcadero, Porto Alegre — the spring tech convention in Bruno's home city",
    receipt: "South Summit Brazil 2027 · April 14–16, 2027 (demo event)",
    emName: "South Summit Brazil 2027",
    sectors: [
      { id: "plenary", name: "Plenary — Main Stage", a0: 70, a1: 110, base: 1490, color: 0xd94f04 },
      { id: "comp-a", name: "Startup Competition Arena · North", a0: 40, a1: 70, base: 990, color: 0xe86a1c },
      { id: "comp-b", name: "Startup Competition Arena · South", a0: 110, a1: 140, base: 990, color: 0xe86a1c },
      { id: "expo-a", name: "Expo Floor · North", a0: 22, a1: 40, base: 490, color: 0x2e6fb7 },
      { id: "expo-b", name: "Expo Floor · South", a0: 140, a1: 158, base: 490, color: 0x2e6fb7 },
      { id: "investor", name: "Investor Lounge", a0: 250, a1: 290, base: 2990, color: 0xc9a227 },
      { id: "work-a", name: "Workshop Wing · North", a0: 220, a1: 250, base: 790, color: 0x4a8ac4 },
      { id: "work-b", name: "Workshop Wing · South", a0: 290, a1: 320, base: 790, color: 0x4a8ac4 },
      { id: "net-a", name: "Networking Terrace · North", a0: 158, a1: 202, base: 590, color: 0x3f9e4d },
      { id: "net-b", name: "Networking Terrace · South", a0: 338, a1: 382, base: 590, color: 0x3f9e4d },
    ],
    rings: [
      { id: "t1", name: "Attendee Pass", d0: 30, d1: 48, h0: 1, h1: 13, factor: 1.0, open: true },
      { id: "t2", name: "Startup Pass", d0: 50, d1: 66, h0: 15, h1: 29, factor: 1.35, open: true },
      { id: "t3", name: "Executive Pass", d0: 68, d1: 84, h0: 31, h1: 46, factor: 2.1, open: false },
    ],
    card: `<div class="team home" style="background:#1a1a1a"><span class="abbr">SOUTH</span><span class="tname">Summit Brazil 2027</span><span class="tcity">Cais Embarcadero</span></div>
      <div class="vs">TECH<br><span>APR 14–16<br>2027</span></div>
      <div class="team away"><span class="abbr">POA</span><span class="tname">Porto Alegre</span><span class="tcity">Rio Grande do Sul</span></div>`,
  },
];

// --- F1 North America trio + LA28 (forward-looking) --------------------------
// F1 sourcing model (James, 2026-11-12): street circuits have no venue box
// office — grandstand inventory comes via the production company that manages
// the event. LA28 is forward-looking; key sports per James: Lacrosse Sixes,
// Surfing, Basketball, Swimming & Diving (aquatics — natural seat selection).
const F1RINGS = null; // share the stadium ring bands as grandstand row bands
EVENTS.push(
  {
    id: "f1-miami", tab: "🏎 F1 Miami", kind: "f1", currency: "$",
    venue: "Miami International Autodrome — Demo Survey", city: "Miami Gardens",
    ringLabel: "Row band", centerColor: 0x3a3f45,
    banner: "🏎 <strong>Formula 1 — Miami Grand Prix</strong> · May 2027 · Street circuit: grandstand inventory via the event's production company — location choice is the premium product",
    receipt: "F1 Miami Grand Prix · May 2027 (demo event)",
    emName: "F1 Miami Grand Prix 2027",
    sectors: [
      { id: "sf", name: "Start/Finish Grandstand", a0: 70, a1: 110, base: 890, color: 0xd94f04 },
      { id: "t1g", name: "Turn 1 Grandstand · North", a0: 40, a1: 70, base: 640, color: 0xe86a1c },
      { id: "t1b", name: "Turn 1 Grandstand · South", a0: 110, a1: 140, base: 640, color: 0xe86a1c },
      { id: "marina-a", name: "Marina Grandstand · North", a0: 22, a1: 40, base: 720, color: 0x2e6fb7 },
      { id: "marina-b", name: "Marina Grandstand · South", a0: 140, a1: 158, base: 720, color: 0x2e6fb7 },
      { id: "paddock", name: "Paddock Club Hospitality", a0: 250, a1: 290, base: 4900, color: 0xc9a227 },
      { id: "beach-a", name: "Beach Grandstand · North", a0: 220, a1: 250, base: 560, color: 0x4a8ac4 },
      { id: "beach-b", name: "Beach Grandstand · South", a0: 290, a1: 320, base: 560, color: 0x4a8ac4 },
      { id: "campus-a", name: "Campus Pass — GA · North", a0: 158, a1: 202, base: 290, color: 0x3f9e4d },
      { id: "campus-b", name: "Campus Pass — GA · South", a0: 338, a1: 382, base: 290, color: 0x3f9e4d },
    ],
    rings: F1RINGS,
    card: `<div class="team home" style="background:#d94f04"><span class="abbr">MIA</span><span class="tname">Miami Grand Prix</span><span class="tcity">Street Circuit</span></div>
      <div class="vs">F1<br><span>MAY<br>2027</span></div>
      <div class="team away"><span class="abbr">USA</span><span class="tname">North America Leg</span><span class="tcity">1 of 3</span></div>`,
  },
  {
    id: "f1-vegas", tab: "🏎 F1 Las Vegas", kind: "f1", currency: "$",
    venue: "Las Vegas Strip Circuit — Demo Survey", city: "Las Vegas",
    ringLabel: "Row band", centerColor: 0x2b2b33,
    banner: "🏎 <strong>Formula 1 — Las Vegas Grand Prix</strong> · November 2027 · Night race on the Strip — grandstands via the event production company",
    receipt: "F1 Las Vegas Grand Prix · November 2027 (demo event)",
    emName: "F1 Las Vegas Grand Prix 2027",
    sectors: [
      { id: "main-g", name: "Main Grandstand", a0: 70, a1: 110, base: 1050, color: 0x7a3fa0 },
      { id: "eh-a", name: "East Harmon Grandstand · North", a0: 40, a1: 70, base: 780, color: 0x9a5fc0 },
      { id: "eh-b", name: "East Harmon Grandstand · South", a0: 110, a1: 140, base: 780, color: 0x9a5fc0 },
      { id: "sphere-a", name: "Sphere Zone — GA · North", a0: 22, a1: 40, base: 520, color: 0xb08fd0 },
      { id: "sphere-b", name: "Sphere Zone — GA · South", a0: 140, a1: 158, base: 520, color: 0xb08fd0 },
      { id: "fountain", name: "Bellagio Fountain Club", a0: 250, a1: 290, base: 3900, color: 0xc9a227 },
      { id: "wh-a", name: "West Harmon Grandstand · North", a0: 220, a1: 250, base: 720, color: 0x5f7fc0 },
      { id: "wh-b", name: "West Harmon Grandstand · South", a0: 290, a1: 320, base: 720, color: 0x5f7fc0 },
      { id: "t3-a", name: "Turn 3 Grandstand · North", a0: 158, a1: 202, base: 690, color: 0x4a9e6d },
      { id: "t3-b", name: "Turn 3 Grandstand · South", a0: 338, a1: 382, base: 690, color: 0x4a9e6d },
    ],
    rings: F1RINGS,
    card: `<div class="team home" style="background:#7a3fa0"><span class="abbr">LV</span><span class="tname">Las Vegas Grand Prix</span><span class="tcity">Strip Circuit · Night</span></div>
      <div class="vs">F1<br><span>NOV<br>2027</span></div>
      <div class="team away"><span class="abbr">USA</span><span class="tname">North America Leg</span><span class="tcity">2 of 3</span></div>`,
  },
  {
    id: "f1-austin", tab: "🏎 F1 Austin", kind: "f1", currency: "$", emName: "F1 Austin Grand Prix 2027",
    venue: "Circuit of the Americas — Demo Survey", city: "Austin, Texas",
    ringLabel: "Row band", centerColor: 0x44503f,
    banner: "🏎 <strong>Formula 1 — United States Grand Prix, Austin</strong> · October 2027 · COTA — the third North American leg",
    receipt: "F1 US Grand Prix — Austin · October 2027 (demo event)",
    sectors: [
      { id: "cota-main", name: "Main Grandstand", a0: 70, a1: 110, base: 620, color: 0xb03a2e },
      { id: "cota-t1a", name: "Turn 1 Grandstand · North", a0: 40, a1: 70, base: 540, color: 0xc05040 },
      { id: "cota-t1b", name: "Turn 1 Grandstand · South", a0: 110, a1: 140, base: 540, color: 0xc05040 },
      { id: "cota-t15a", name: "Turn 15 Grandstand · North", a0: 22, a1: 40, base: 480, color: 0x2e6fb7 },
      { id: "cota-t15b", name: "Turn 15 Grandstand · South", a0: 140, a1: 158, base: 480, color: 0x2e6fb7 },
      { id: "cota-club", name: "COTA Club Hospitality", a0: 250, a1: 290, base: 2600, color: 0xc9a227 },
      { id: "cota-t12a", name: "Turn 12 Grandstand · North", a0: 220, a1: 250, base: 450, color: 0x4a8ac4 },
      { id: "cota-t12b", name: "Turn 12 Grandstand · South", a0: 290, a1: 320, base: 450, color: 0x4a8ac4 },
      { id: "cota-ga-a", name: "GA Hill · North", a0: 158, a1: 202, base: 210, color: 0x3f9e4d },
      { id: "cota-ga-b", name: "GA Hill · South", a0: 338, a1: 382, base: 210, color: 0x3f9e4d },
    ],
    rings: F1RINGS,
    card: `<div class="team home" style="background:#b03a2e"><span class="abbr">ATX</span><span class="tname">US Grand Prix</span><span class="tcity">COTA · Austin</span></div>
      <div class="vs">F1<br><span>OCT<br>2027</span></div>
      <div class="team away"><span class="abbr">USA</span><span class="tname">North America Leg</span><span class="tcity">3 of 3</span></div>`,
  },
  {
    id: "la28", tab: "🏅 LA28", kind: "la28", currency: "$", emName: "LA28 Olympics", emFocus: { sector: "Basketball — Lower Bowl · North", ring: "Lower Ring" },
    venue: "LA28 Showcase — Demo Survey", city: "Los Angeles",
    ringLabel: "Tier", centerColor: 0x2e6fb7,
    banner: "🏅 <strong>LA28 Olympics — FORWARD-LOOKING</strong> · July 2028 · Our key sports: Lacrosse Sixes · Surfing · Basketball · Swimming &amp; Diving — seat selection built in from the start",
    receipt: "LA28 Olympics · July 2028 (forward-looking demo)",
    sectors: [
      { id: "lax-g", name: "Lacrosse Sixes — Grandstand", a0: 70, a1: 110, base: 320, color: 0x3f9e4d },
      { id: "lax-p-a", name: "Lacrosse Sixes — Premium · North", a0: 40, a1: 70, base: 480, color: 0x57b368 },
      { id: "lax-p-b", name: "Lacrosse Sixes — Premium · South", a0: 110, a1: 140, base: 480, color: 0x57b368 },
      { id: "swim-a", name: "Swimming — Finals Grandstand", a0: 22, a1: 40, base: 540, color: 0x2e6fb7 },
      { id: "swim-b", name: "Diving — Tower View", a0: 140, a1: 158, base: 460, color: 0x2e8fb7 },
      { id: "aqua", name: "Aquatics — Pool Deck Premium", a0: 250, a1: 290, base: 890, color: 0x27a3c4 },
      { id: "bb-a", name: "Basketball — Lower Bowl · North", a0: 220, a1: 250, base: 650, color: 0xd94f04 },
      { id: "bb-b", name: "Basketball — Lower Bowl · South", a0: 290, a1: 320, base: 650, color: 0xd94f04 },
      { id: "surf-a", name: "Surfing — Trestles Premium · North", a0: 158, a1: 202, base: 210, color: 0xe0a51c },
      { id: "surf-b", name: "Surfing — Trestles Premium · South", a0: 338, a1: 382, base: 210, color: 0xe0a51c },
    ],
    rings: null,
    card: `<div class="team home" style="background:#1a1a1a"><span class="abbr">LA28</span><span class="tname">Olympic Games</span><span class="tcity">Los Angeles</span></div>
      <div class="vs">2028<br><span>JUL<br>2028</span></div>
      <div class="team away"><span class="abbr">🏅</span><span class="tname">Key Sports</span><span class="tcity">Sixes · Surf · Hoops · Aquatics</span></div>`,
  }
);
