// The UZE Buildr Team seed roster (James's directive, 2026-11-19).
// Contributors are principals and ecosystem contributors who do NOT
// use GitHub: the surface at buildr-eco.uzemarkets.com is email +
// one-time code only. Visibility model: the Ecosystem top level is
// visible to EVERY signed-in contributor; the four org sections
// beneath it (keys from db/orgs.mjs: UZE, L2Launch, DFI, FVC) are
// granted per contributor and enforced server-side. Email is
// optional — unique only when present; a contributor with no email
// on file carries null and cannot sign in until one is supplied.
// Seeding records the roster exactly as directed; it sends nothing.
// The same records are the JSON-mode seed in
// data/eco-contributors.json — keep them in step.
export const ALL_ORGS = ["UZE", "L2Launch", "DFI", "FVC"];
export const ECO_CONTRIBUTORS = [
  {
    id: "eco-james-dugan",
    name: "James Dugan (D5)",
    email: "james@decensat.org",
    role: "Launch Principal",
    orgs: ALL_ORGS.slice(),
    sessionEpoch: 0,
    stage: "seeded",
    addedAt: "2026-11-19T00:00:00.000Z",
  },
  {
    id: "eco-william-dugan",
    name: "William Cumberland Dugan (WCD)",
    email: "william@decensat.org",
    role: "Launch Principal",
    orgs: ALL_ORGS.slice(),
    sessionEpoch: 0,
    stage: "seeded",
    addedAt: "2026-11-19T00:00:00.000Z",
  },
  {
    id: "eco-jonathan-schmidt",
    name: "Jonathan Schmidt",
    email: "schmidtcommunications@gmail.com",
    role: "Creative Intelligence Principal, L2Launch",
    orgs: ALL_ORGS.slice(),
    sessionEpoch: 0,
    stage: "seeded",
    addedAt: "2026-11-19T00:00:00.000Z",
  },
  {
    id: "eco-shradesh-jodawat",
    name: "Shradesh Jodawat (SJ)",
    email: null, // not on file — the record exists; sign-in activates when an email is supplied
    role: "Ecosystem Contributor (Gradify; attestation design)",
    orgs: ALL_ORGS.slice(),
    sessionEpoch: 0,
    stage: "seeded",
    addedAt: "2026-11-19T00:00:00.000Z",
  },
  {
    id: "eco-dipanshu-singh",
    name: "Dipanshu Singh",
    email: "dipanshuhappy@gmail.com",
    role: "Ecosystem Contributor",
    // James's segmentation ruling (2026-11-19): Dipanshu sees the
    // Ecosystem top level and FVC only — not UZE, not L2Launch, not DFI.
    orgs: ["FVC"],
    sessionEpoch: 0,
    stage: "seeded",
    addedAt: "2026-11-19T00:00:00.000Z",
  },
];
