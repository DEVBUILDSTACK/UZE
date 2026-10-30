/* GENERATED from servicetask\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string | null;
export type Tripprofileid = string;
export type Kind = string;
export type TaskState = "REQUESTED" | "QUOTED" | "DEPOSIT_PENDING" | "CONFIRMED" | "FAILED" | "CANCELLED";
export type Createdat = string | null;
export type Updatedat = string | null;

export interface ServiceTask {
  id?: Id;
  tripProfileId: Tripprofileid;
  kind: Kind;
  state: TaskState;
  details: Details;
  createdAt?: Createdat;
  updatedAt?: Updatedat;
}
export interface Details {
  [k: string]: unknown;
}
