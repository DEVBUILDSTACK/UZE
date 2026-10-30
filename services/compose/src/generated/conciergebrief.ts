/* GENERATED from conciergebrief\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string | null;
export type Tripprofileid = string;
export type TaskState = "REQUESTED" | "QUOTED" | "DEPOSIT_PENDING" | "CONFIRMED" | "FAILED" | "CANCELLED";
export type Trigger = string;
export type Meteringratecents = number | null;
export type Meteringcapcents = number | null;
export type Meteringexpiresat = string | null;
export type Createdat = string | null;

export interface ConciergeBrief {
  id?: Id;
  tripProfileId: Tripprofileid;
  state: TaskState;
  trigger: Trigger;
  brief: Brief;
  meteringRateCents?: Meteringratecents;
  meteringCapCents?: Meteringcapcents;
  meteringExpiresAt?: Meteringexpiresat;
  createdAt?: Createdat;
}
export interface Brief {
  [k: string]: unknown;
}
