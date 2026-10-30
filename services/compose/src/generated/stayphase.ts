/* GENERATED from stayphase\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string | null;
export type Tripprofileid = string;
export type StayPhaseKind = "PRE_EVENT" | "EVENT" | "POST_EVENT" | "PRE_OP" | "INPATIENT" | "RECOVERY";
export type Propertyref = string | null;
export type Checkin = string;
export type Checkout = string;
export type Seq = number;

export interface StayPhase {
  id?: Id;
  tripProfileId: Tripprofileid;
  kind: StayPhaseKind;
  propertyRef?: Propertyref;
  checkIn: Checkin;
  checkOut: Checkout;
  occupants: Occupants;
  criteria: Criteria;
  seq: Seq;
}
export interface Occupants {
  [k: string]: unknown;
}
export interface Criteria {
  [k: string]: unknown;
}
