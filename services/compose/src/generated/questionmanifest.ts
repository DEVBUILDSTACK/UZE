/* GENERATED from questionmanifest\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string | null;
export type Key = string;
export type Version = number;
export type Title = string;
export type Active = boolean | null;
export type Createdat = string | null;

export interface QuestionManifest {
  id?: Id;
  key: Key;
  version: Version;
  title: Title;
  questions: Questions;
  active?: Active;
  createdAt?: Createdat;
}
export interface Questions {
  [k: string]: unknown;
}
