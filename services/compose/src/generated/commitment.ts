/* GENERATED from commitment\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string | null;
export type Approvalrequestid = string;
export type Offersnapshotid = string;
export type State = string;
export type Settledat = string | null;
export type Chaintxref = string | null;

export interface Commitment {
  id?: Id;
  approvalRequestId: Approvalrequestid;
  offerSnapshotId: Offersnapshotid;
  state: State;
  settledAt?: Settledat;
  chainTxRef?: Chaintxref;
}
