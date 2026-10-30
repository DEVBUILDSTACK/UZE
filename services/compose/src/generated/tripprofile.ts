/* GENERATED from tripprofile\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string | null;
export type Buyerid = string;
export type Version = number | null;
export type ModuleType =
  "TICKETS" | "STAY" | "FLIGHT" | "PARKING" | "TRANSIT" | "DINING" | "TRANSFER" | "VIP_CONCIERGE" | "FACILITY";
export type Modules = ModuleType[];
export type Tier = string | null;
export type Confirmedat = string | null;
export type Supersededby = string | null;
export type Travelers = Traveler[] | null;
export type Id1 = string | null;
export type Tripprofileid = string;
export type TravelerRole = "PATIENT" | "COMPANION" | "PRIMARY" | "GUEST";
export type Origin = string | null;
export type Nationality = string | null;
export type Stayphases = StayPhase[] | null;
export type Id2 = string | null;
export type Tripprofileid1 = string;
export type StayPhaseKind = "PRE_EVENT" | "EVENT" | "POST_EVENT" | "PRE_OP" | "INPATIENT" | "RECOVERY";
export type Propertyref = string | null;
export type Checkin = string;
export type Checkout = string;
export type Seq = number;

export interface TripProfile {
  id?: Id;
  buyerId: Buyerid;
  version?: Version;
  modules: Modules;
  tier?: Tier;
  authorization: Authorization;
  confirmedAt?: Confirmedat;
  supersededBy?: Supersededby;
  travelers?: Travelers;
  stayPhases?: Stayphases;
}
export interface Authorization {
  [k: string]: unknown;
}
export interface Traveler {
  id?: Id1;
  tripProfileId: Tripprofileid;
  role: TravelerRole;
  origin?: Origin;
  nationality?: Nationality;
  utilityWeights: Utilityweights;
}
export interface Utilityweights {
  [k: string]: unknown;
}
export interface StayPhase {
  id?: Id2;
  tripProfileId: Tripprofileid1;
  kind: StayPhaseKind;
  propertyRef?: Propertyref;
  checkIn: Checkin;
  checkOut: Checkout;
  occupants: Occupants;
  criteria: Criteria;
  seq: Seq;
}
export interface Occupants {
  [k: string]: unknown;
}
export interface Criteria {
  [k: string]: unknown;
}
