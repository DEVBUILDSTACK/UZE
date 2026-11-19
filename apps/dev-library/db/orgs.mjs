// The organization registry (James's steering, 2026-11-19):
// organizations are first-class — contacts attach to organizations.
// Advisor records carry an org KEY referencing this registry; names
// and acronyms live here alone. The same registry is the JSON-mode
// seed in data/orgs.json — keep the two in step.
export const ORGS = [
  { key: "DFI", name: "DealFi", acronym: "DFI", position: 1 },
  { key: "FVC", name: "Fundio", acronym: "FVC", position: 2 },
  { key: "UZE", name: "UZEmarkets", acronym: "UZE", position: 3 },
  { key: "L2Launch", name: "L2 Launchpad", acronym: "L2Launch", position: 4 },
];
