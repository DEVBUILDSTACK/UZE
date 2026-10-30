/* GENERATED from packagetemplate\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string | null;
export type Facilityid = string;
export type Procedureclassband = string;

export interface PackageTemplate {
  id?: Id;
  facilityId: Facilityid;
  procedureClassBand: Procedureclassband;
  phaseTemplate: Phasetemplate;
  inclusions: Inclusions;
  depositTerms: Depositterms;
}
export interface Phasetemplate {
  [k: string]: unknown;
}
export interface Inclusions {
  [k: string]: unknown;
}
export interface Depositterms {
  [k: string]: unknown;
}
