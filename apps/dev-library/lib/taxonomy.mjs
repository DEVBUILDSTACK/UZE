// Role × Realm taxonomy (directive v3.1 §3; BUILD-SCOPE v1.0 §A.3).
// The single source for the enum sets in the app: 11 Roles × 6 Realms,
// up to five pairs per developer ranked PRIMARY → QUINARY (invariant
// I1: 1–5 pairs, no duplicate (role, realm), first pair is PRIMARY).
// The core-side mirror is the talent schema (migration d1ce7a1e5001:
// talent.role / talent.realm / talent.proficiency enums + the
// talent_expertise table with the same checks).
export const ROLES = [
  "DIGITAL_DESIGN_DEV", "FULL_STACK_DEV", "FRONT_END_DEV", "BLOCKCHAIN_DEV",
  "SMART_CONTRACT_DEV", "BLOCKCHAIN_CTO", "DEVELOPER_ADVOCATE",
  "TALENT_HR_SPECIALIST", "DATA_SCIENTIST", "AI_SI_SPECIALIST", "OTHER_ROLE",
];
export const REALMS = ["LIGHTNING", "NFT_WALLETS", "NEAR_AI", "CROSS_CHAIN", "LIGHTER", "OTHER_REALM"];
export const RANKS = ["PRIMARY", "SECONDARY", "TERTIARY", "QUATERNARY", "QUINARY"];
export const TRACKS = ["INTERNAL_ONLY", "EXTERNAL_PLACED", "EITHER"];

// Placement shapes (BUILD-SCOPE §A.2 / commercial-models addendum):
// service = the engagement mode, deployment = the work mode, and the
// commercial model is the money model — distinct, never blended.
export const SERVICES = ["AUG", "OUTSTAFF", "PLACE", "PROJECT"];
export const DEPLOYMENTS = ["REMOTE", "HYBRID", "MIXED", "ONSITE"];
export const COMMERCIAL_MODELS = ["OUTSTAFFING", "PLACEMENT"];

// Validate + normalize a pairs list: [{role, realm}] in rank order →
// [{ordinal, role, realm, rank}]. An empty list clears the pairs.
// Throws on an invalid role/realm, a duplicate pair, or a 6th pair.
export function validatePairs(input) {
  if (!Array.isArray(input)) throw new Error("pairs must be an array of {role, realm}");
  if (input.length > 5) throw new Error(`expertise ceiling is 5 pairs (I1); got ${input.length}`);
  const seen = new Set();
  return input.map((p, i) => {
    const role = String(p?.role || "").toUpperCase();
    const realm = String(p?.realm || "").toUpperCase();
    if (!ROLES.includes(role)) throw new Error("invalid role: " + (p?.role ?? ""));
    if (!REALMS.includes(realm)) throw new Error("invalid realm: " + (p?.realm ?? ""));
    const key = role + "×" + realm;
    if (seen.has(key)) throw new Error("duplicate pair: " + key);
    seen.add(key);
    return { ordinal: i + 1, role, realm, rank: RANKS[i] };
  });
}
