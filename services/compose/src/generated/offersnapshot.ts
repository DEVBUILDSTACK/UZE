/* GENERATED from offersnapshot\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

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
export type RailPayload =
  RailPayload1 | RailPayload2 | RailPayload3 | RailPayload4 | RailPayload5 | RailPayload6 | RailPayload7;
export type Rail1 = "ticket";
export type Seat = string;
export type Tier = string;
export type Gate = string | null;
export type Mintref = string | null;
export type Ticketref = string | null;
export type Listingref = string | null;
export type Rail2 = "stay";
export type Phasekind = string;
export type Nights = number;
export type Propertyref = string | null;
export type Rail3 = "flight";
export type Itineraryref = string;
export type Carrier = string | null;
export type Departat = string | null;
export type Rail4 = "facility";
export type Facilityref = string;
export type Packageref = string;
export type Procedureclassband = string | null;
export type Rail5 = "parking";
export type Anchorref = string;
export type Spotref = string | null;
export type Rail6 = "transfer";
export type Taskref = string;
export type Pickupat = string | null;
export type Rail7 = "dining";
export type Taskref1 = string;
export type Reservationat = string | null;
export type DivergenceCode =
  | "SNAPSHOT_EXPIRED"
  | "SOURCE_NOT_FOUND"
  | "LISTING_GONE"
  | "TICKET_TRANSFERRED"
  | "TICKET_REDEEMED"
  | "SEAT_TAKEN"
  | "PRICE_MOVED"
  | "UPSTREAM_UNAVAILABLE";
export type Divergenceat = string | null;
export type Expiresat = string;
export type Createdat = string | null;
export type Retentionuntil = string | null;

export interface OfferSnapshot {
  id?: Id;
  tripCandidateId: Tripcandidateid;
  rail: Rail;
  sourceRef: Sourceref;
  commitmentClass: CommitmentClass;
  price: Price;
  terms: Terms;
  payload: RailPayload;
  divergenceCode?: DivergenceCode | null;
  divergenceAt?: Divergenceat;
  expiresAt: Expiresat;
  createdAt?: Createdat;
  retentionUntil?: Retentionuntil;
}
export interface Price {
  amount: Amount;
  currency: Currency;
  taxesIncluded: Taxesincluded;
}
export interface Terms {
  [k: string]: unknown;
}
export interface RailPayload1 {
  rail: Rail1;
  seat: Seat;
  tier: Tier;
  gate?: Gate;
  mintRef?: Mintref;
  ticketRef?: Ticketref;
  listingRef?: Listingref;
}
export interface RailPayload2 {
  rail: Rail2;
  phaseKind: Phasekind;
  nights: Nights;
  propertyRef?: Propertyref;
}
export interface RailPayload3 {
  rail: Rail3;
  itineraryRef: Itineraryref;
  carrier?: Carrier;
  departAt?: Departat;
}
export interface RailPayload4 {
  rail: Rail4;
  facilityRef: Facilityref;
  packageRef: Packageref;
  procedureClassBand?: Procedureclassband;
}
export interface RailPayload5 {
  rail: Rail5;
  anchorRef: Anchorref;
  spotRef?: Spotref;
}
export interface RailPayload6 {
  rail: Rail6;
  taskRef: Taskref;
  pickupAt?: Pickupat;
}
export interface RailPayload7 {
  rail: Rail7;
  taskRef: Taskref1;
  reservationAt?: Reservationat;
}
