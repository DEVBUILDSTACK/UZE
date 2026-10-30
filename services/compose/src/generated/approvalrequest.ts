/* GENERATED from approvalrequest\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string | null;
export type Tripprofileid = string;
export type CommitmentClass =
  "IRREVERSIBLE_ON_CHAIN" | "CANCELLABLE_UNTIL_WINDOW" | "CHANGEABLE_WITH_FEE" | "APPOINTMENT" | "MEDICAL_PACKAGE";
export type Status = string | null;
export type Signedby = string | null;
export type Resolvedat = string | null;
export type Commitments = Commitment[] | null;
export type Id1 = string | null;
export type Approvalrequestid = string;
export type Offersnapshotid = string;
export type State = string;
export type Settledat = string | null;
export type Chaintxref = string | null;

export interface ApprovalRequest {
  id?: Id;
  tripProfileId: Tripprofileid;
  commitmentClass: CommitmentClass;
  summary: Summary;
  status?: Status;
  signedBy?: Signedby;
  resolvedAt?: Resolvedat;
  commitments?: Commitments;
}
export interface Summary {
  [k: string]: unknown;
}
export interface Commitment {
  id?: Id1;
  approvalRequestId: Approvalrequestid;
  offerSnapshotId: Offersnapshotid;
  state: State;
  settledAt?: Settledat;
  chainTxRef?: Chaintxref;
}
