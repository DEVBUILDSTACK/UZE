/* GENERATED from consentrecord\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string | null;
export type Subjectid = string;
export type Purpose = string;
export type Version = string;
export type Grantedat = string;
export type Revokedat = string | null;
export type Healthattributes = HealthAttribute[] | null;
export type Id1 = string | null;
export type Subjectid1 = string;
export type Consentid = string;
export type Attrkey = string;
export type Retentionuntil = string;

export interface ConsentRecord {
  id?: Id;
  subjectId: Subjectid;
  purpose: Purpose;
  version: Version;
  grantedAt: Grantedat;
  revokedAt?: Revokedat;
  healthAttributes?: Healthattributes;
}
export interface HealthAttribute {
  id?: Id1;
  subjectId: Subjectid1;
  consentId: Consentid;
  attrKey: Attrkey;
  attrValue: Attrvalue;
  retentionUntil: Retentionuntil;
}
export interface Attrvalue {
  [k: string]: unknown;
}
