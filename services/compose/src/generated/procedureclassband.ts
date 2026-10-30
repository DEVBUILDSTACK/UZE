/* GENERATED from procedureclassband\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string | null;
export type Band = string;
export type Mindayspostopbeforereturn = number;
export type Cabincomfortmin = string | null;

export interface ProcedureClassBand {
  id?: Id;
  band: Band;
  minDaysPostOpBeforeReturn: Mindayspostopbeforereturn;
  cabinComfortMin?: Cabincomfortmin;
}
