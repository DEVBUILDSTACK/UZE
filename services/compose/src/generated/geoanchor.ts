/* GENERATED from geoanchor\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string | null;
export type GeoAnchorType = "VENUE" | "FACILITY" | "ADDRESS" | "METRO";
export type Refid = string | null;
export type Label = string;
export type Lat = number;
export type Lng = number;
export type Radiuskm = number | null;
export type Metroid = string | null;

export interface GeoAnchor {
  id?: Id;
  type: GeoAnchorType;
  refId?: Refid;
  label: Label;
  lat: Lat;
  lng: Lng;
  radiusKm?: Radiuskm;
  metroId?: Metroid;
}
