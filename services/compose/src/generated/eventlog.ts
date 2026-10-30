/* GENERATED from eventlog\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = number;
export type Aggregatetype = string;
export type Aggregateid = string;
export type Eventtype = string;
export type Actor = string;
export type Ts = string | null;

export interface EventLog {
  id: Id;
  aggregateType: Aggregatetype;
  aggregateId: Aggregateid;
  eventType: Eventtype;
  actor: Actor;
  payload: Payload;
  ts?: Ts;
}
export interface Payload {
  [k: string]: unknown;
}
