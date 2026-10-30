/* GENERATED from facilityprofile\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string | null;
export type Geoanchorid = string;
export type Languages = string[];
export type Metroid = string | null;

export interface FacilityProfile {
  id?: Id;
  geoAnchorId: Geoanchorid;
  accreditation: Accreditation;
  languages: Languages;
  metroId?: Metroid;
}
export interface Accreditation {
  [k: string]: unknown;
}
