/* GENERATED from transfertask\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string;
export type Tripprofileid = string;
export type Kind = string;
export type TaskState = "REQUESTED" | "QUOTED" | "DEPOSIT_PENDING" | "CONFIRMED" | "FAILED" | "CANCELLED";
export type Createdat = string | null;
export type Updatedat = string | null;
export type Fromanchorref = string | null;
export type Toanchorref = string | null;
export type Pickupat = string | null;
export type Vehicleclass = string | null;

export interface TransferTask {
  id: Id;
  tripProfileId: Tripprofileid;
  kind: Kind;
  state: TaskState;
  details: Details;
  createdAt?: Createdat;
  updatedAt?: Updatedat;
  fromAnchorRef?: Fromanchorref;
  toAnchorRef?: Toanchorref;
  pickupAt?: Pickupat;
  vehicleClass?: Vehicleclass;
}
export interface Details {
  [k: string]: unknown;
}
