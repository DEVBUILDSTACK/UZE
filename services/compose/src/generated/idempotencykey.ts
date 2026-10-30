/* GENERATED from idempotencykey\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Key = string;
export type Scope = string;
export type Requesthash = string;
export type Responsejson = {
  [k: string]: unknown;
} | null;
export type Status = string | null;
export type Createdat = string | null;

export interface IdempotencyKey {
  key: Key;
  scope: Scope;
  requestHash: Requesthash;
  responseJson?: Responsejson;
  status?: Status;
  createdAt?: Createdat;
}
