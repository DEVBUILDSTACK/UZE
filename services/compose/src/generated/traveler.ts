/* GENERATED from traveler\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string | null;
export type Tripprofileid = string;
export type TravelerRole = "PATIENT" | "COMPANION" | "PRIMARY" | "GUEST";
export type Origin = string | null;
export type Nationality = string | null;

export interface Traveler {
  id?: Id;
  tripProfileId: Tripprofileid;
  role: TravelerRole;
  origin?: Origin;
  nationality?: Nationality;
  utilityWeights: Utilityweights;
}
export interface Utilityweights {
  [k: string]: unknown;
}
