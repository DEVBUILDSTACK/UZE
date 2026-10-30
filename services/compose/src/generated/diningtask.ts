/* GENERATED from diningtask\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string;
export type Tripprofileid = string;
export type Kind = string;
export type TaskState = "REQUESTED" | "QUOTED" | "DEPOSIT_PENDING" | "CONFIRMED" | "FAILED" | "CANCELLED";
export type Createdat = string | null;
export type Updatedat = string | null;
export type Geoanchorref = string | null;
export type Requestedfor = string | null;
export type Partytravelerrefs = {
  [k: string]: unknown;
} | null;

export interface DiningTask {
  id: Id;
  tripProfileId: Tripprofileid;
  kind: Kind;
  state: TaskState;
  details: Details;
  createdAt?: Createdat;
  updatedAt?: Updatedat;
  geoAnchorRef?: Geoanchorref;
  requestedFor?: Requestedfor;
  partyTravelerRefs?: Partytravelerrefs;
}
export interface Details {
  [k: string]: unknown;
}
