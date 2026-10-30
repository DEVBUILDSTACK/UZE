/* GENERATED from metroprofile\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string | null;
export type Metrocode = string;
export type Splitstaydefault = boolean | null;

export interface MetroProfile {
  id?: Id;
  metroCode: Metrocode;
  facilityClusters: Facilityclusters;
  resortClusters: Resortclusters;
  splitStayDefault?: Splitstaydefault;
  safetyWeights: Safetyweights;
}
export interface Facilityclusters {
  [k: string]: unknown;
}
export interface Resortclusters {
  [k: string]: unknown;
}
export interface Safetyweights {
  [k: string]: unknown;
}
