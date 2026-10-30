/* GENERATED from searchsession\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string | null;
export type Tripprofileid = string;
export type Createdat = string | null;
export type Candidates = TripCandidate[] | null;
export type Id1 = string | null;
export type Searchsessionid = string;
export type Status = string | null;
export type Rankingscore = number | null;

export interface SearchSession {
  id?: Id;
  tripProfileId: Tripprofileid;
  query: Query;
  createdAt?: Createdat;
  candidates?: Candidates;
}
export interface Query {
  [k: string]: unknown;
}
export interface TripCandidate {
  id?: Id1;
  searchSessionId: Searchsessionid;
  status?: Status;
  rankingScore?: Rankingscore;
  constraints: Constraints;
}
export interface Constraints {
  [k: string]: unknown;
}
