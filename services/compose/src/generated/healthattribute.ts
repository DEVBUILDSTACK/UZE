/* GENERATED from healthattribute\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string | null;
export type Subjectid = string;
export type Consentid = string;
export type Attrkey = string;
export type Retentionuntil = string;

export interface HealthAttribute {
  id?: Id;
  subjectId: Subjectid;
  consentId: Consentid;
  attrKey: Attrkey;
  attrValue: Attrvalue;
  retentionUntil: Retentionuntil;
}
export interface Attrvalue {
  [k: string]: unknown;
}
