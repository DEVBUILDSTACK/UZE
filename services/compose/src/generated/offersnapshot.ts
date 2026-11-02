/* GENERATED from offersnapshot\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string | null;
export type Tripcandidateid = string;
export type Rail =
  "SOLANA_NFT" | "HOTEL_AGGREGATOR" | "FLIGHT_SEARCH" | "FACILITY" | "PARKING" | "TRANSFER" | "DINING_TASK";
export type Sourceref = string;
export type CommitmentClass =
  "IRREVERSIBLE_ON_CHAIN" | "CANCELLABLE_UNTIL_WINDOW" | "CHANGEABLE_WITH_FEE" | "APPOINTMENT" | "MEDICAL_PACKAGE";
export type Amount = number;
export type Currency = "USDC";
export type Taxesincluded = boolean;
export type OfferPayload =
  | TicketOfferDetail
  | StayOfferDetail
  | FlightOfferDetail
  | FacilityOfferDetail
  | ParkingOfferDetail
  | TransferOfferDetail;
export type Kind = "ticket";
export type Seat = string;
export type Tier = string;
export type Gate = string | null;
export type Mintref = string | null;
export type Ticketref = string | null;
export type Listingref = string | null;
export type Kind1 = "stay";
export type Phasekind = string;
export type Nights = number;
export type Propertyref = string | null;
export type Kind2 = "flight";
export type Itineraryref = string;
export type Carrier = string | null;
export type Departat = string | null;
export type Kind3 = "facility";
export type Facilityref = string;
export type Packageref = string;
export type Procedureclassband = string | null;
export type Kind4 = "parking";
export type Anchorref = string;
export type Spotref = string | null;
export type Kind5 = "transfer";
export type Taskref = string;
export type Pickupat = string | null;
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
  payload: OfferPayload;
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
export interface TicketOfferDetail {
  kind: Kind;
  seat: Seat;
  tier: Tier;
  gate?: Gate;
  mintRef?: Mintref;
  ticketRef?: Ticketref;
  listingRef?: Listingref;
}
export interface StayOfferDetail {
  kind: Kind1;
  phaseKind: Phasekind;
  nights: Nights;
  propertyRef?: Propertyref;
}
export interface FlightOfferDetail {
  kind: Kind2;
  itineraryRef: Itineraryref;
  carrier?: Carrier;
  departAt?: Departat;
}
export interface FacilityOfferDetail {
  kind: Kind3;
  facilityRef: Facilityref;
  packageRef: Packageref;
  procedureClassBand?: Procedureclassband;
}
export interface ParkingOfferDetail {
  kind: Kind4;
  anchorRef: Anchorref;
  spotRef?: Spotref;
}
export interface TransferOfferDetail {
  kind: Kind5;
  taskRef: Taskref;
  pickupAt?: Pickupat;
}
