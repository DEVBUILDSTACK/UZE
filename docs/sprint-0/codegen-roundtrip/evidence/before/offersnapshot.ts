/* GENERATED from offersnapshot_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: models.py). */

export type Id = string | null;
export type Tripcandidateid = string;
export type Rail =
  "SOLANA_NFT" | "HOTEL_AGGREGATOR" | "FLIGHT_SEARCH" | "FACILITY" | "PARKING" | "TRANSFER" | "DINING_TASK";
export type Sourceref = string;
export type CommitmentClass =
  "IRREVERSIBLE_ON_CHAIN" | "CANCELLABLE_UNTIL_WINDOW" | "CHANGEABLE_WITH_FEE" | "APPOINTMENT" | "MEDICAL_PACKAGE";
export type Amount = number;
export type Currency = string;
export type Taxesincluded = boolean;
export type Expiresat = string;
export type Createdat = string | null;

export interface OfferSnapshot {
  id?: Id;
  tripCandidateId: Tripcandidateid;
  rail: Rail;
  sourceRef: Sourceref;
  commitmentClass: CommitmentClass;
  price: Price;
  terms: Terms;
  payload: Payload;
  expiresAt: Expiresat;
  createdAt?: Createdat;
}
export interface Price {
  amount: Amount;
  currency: Currency;
  taxesIncluded: Taxesincluded;
}
export interface Terms {
  [k: string]: unknown;
}
export interface Payload {
  [k: string]: unknown;
}
