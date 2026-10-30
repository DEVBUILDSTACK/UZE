/* GENERATED from payloadowner_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: fidelity_models.py). */

export type Id = string | null;
export type Label = string;
export type RailPayload = RailPayload1 | RailPayload2;
export type Rail = "ticket";
export type Seat = string;
export type Tier = string;
export type Gate = string | null;
export type Rail1 = "stay";
export type Phasekind = string;
export type Nights = number;
export type Note = string | null;
export type Createdat = string | null;

export interface PayloadOwner {
  id?: Id;
  label: Label;
  payload: RailPayload;
  note?: Note;
  createdAt?: Createdat;
}
export interface RailPayload1 {
  rail: Rail;
  seat: Seat;
  tier: Tier;
  gate?: Gate;
}
export interface RailPayload2 {
  rail: Rail1;
  phaseKind: Phasekind;
  nights: Nights;
}
