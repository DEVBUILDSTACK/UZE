// The L2L & Ecosystem Advisors seed roster (James's directive,
// 2026-11-19). Advisors are a distinct roster from the Developer
// List: no tracks, no expertise pairs, no GitHub grants, no sign-in
// lifecycle — they advise the ecosystem. Organizations are
// first-class (db/orgs.mjs): `org` is a registry KEY, never a free
// name. Email is optional — unique only when present; a contact
// with no email on file carries null. Seeding records the roster
// exactly as directed; it changes nothing else. The same records
// are the JSON-mode seed in data/advisors.json — keep them in step.
export const ADVISORS = [
  {
    id: "adv-jonathan-schmidt",
    name: "Jonathan Schmidt",
    email: "schmidtcommunications@gmail.com",
    title: "Creative Intelligence Principal",
    org: "L2Launch",
    base: "Santo Domingo, DR",
    lane: "Creative interface — design evaluation advisory (ecosystem design standard)",
    addedAt: "2026-11-19T00:00:00.000Z",
  },
  {
    id: "adv-william-dugan",
    name: "William Cumberland Dugan",
    email: "dugan.x@gmail.com",
    title: "Launch Principal",
    org: "L2Launch",
    base: "DC–Baltimore",
    lane: "Launch principal — commercial art & identity",
    addedAt: "2026-11-19T00:00:00.000Z",
  },
  {
    id: "adv-joey-hunter",
    name: "Joey Hunter",
    email: null, // not on file — email is optional for advisor contacts
    title: "Launch Principal",
    org: "L2Launch",
    base: "Fort Lauderdale",
    lane: "Launch principal — creator collaborator",
    addedAt: "2026-11-19T00:00:00.000Z",
  },
];
