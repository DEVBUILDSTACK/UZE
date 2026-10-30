/* GENERATED from intakedraft\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string | null;
export type Token = string;
export type Missingslots = string[];
export type Expiresat = string;
export type Createdat = string | null;

export interface IntakeDraft {
  id?: Id;
  token: Token;
  answers: Answers;
  missingSlots: Missingslots;
  invalidSlots: Invalidslots;
  expiresAt: Expiresat;
  createdAt?: Createdat;
}
export interface Answers {
  [k: string]: unknown;
}
export interface Invalidslots {
  [k: string]: unknown;
}
