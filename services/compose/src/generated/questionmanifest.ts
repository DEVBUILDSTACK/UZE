/* GENERATED from questionmanifest\_pydantic.py via its JSON Schema (json-schema-to-typescript). Do not edit. Regenerate: make all (source of truth: src/models.py). */

export type Id = string | null;
export type Key = string;
export type Version = number;
export type Title = string;
export type QuestionSlot = EnumQuestionSlot | StandardQuestionSlot;
export type Key1 = string;
export type Type = "ENUM";
export type Required = boolean;
export type Deferrable = boolean;
export type Dependson = QuestionSlotDependency[] | null;
export type Slot = string;
export type Op = string;
export type ModuleType = ModuleType1 | null;
export type ModuleType1 =
  "TICKETS" | "STAY" | "FLIGHT" | "PARKING" | "TRANSIT" | "DINING" | "TRANSFER" | "VIP_CONCIERGE" | "FACILITY";
export type Validation = {
  [k: string]: unknown;
} | null;
export type Prompthuman = string;
export type Promptagent = string;
export type Enumvalues = string[];
export type Key2 = string;
export type QuestionSlotType = "STRING" | "INT" | "DATE" | "BOOL" | "OBJECT" | "ARRAY";
export type Required1 = boolean;
export type Deferrable1 = boolean;
export type Dependson1 = QuestionSlotDependency[] | null;
export type ModuleType2 = ModuleType1 | null;
export type Validation1 = {
  [k: string]: unknown;
} | null;
export type Prompthuman1 = string;
export type Promptagent1 = string;
export type QuestionSlotList = QuestionSlot[];
export type Active = boolean | null;
export type Createdat = string | null;

export interface QuestionManifest {
  id?: Id;
  key: Key;
  version: Version;
  title: Title;
  questions: QuestionSlotList;
  active?: Active;
  createdAt?: Createdat;
}
export interface EnumQuestionSlot {
  key: Key1;
  type: Type;
  required: Required;
  deferrable: Deferrable;
  dependsOn?: Dependson;
  moduleGate?: ModuleType;
  validation?: Validation;
  promptHuman: Prompthuman;
  promptAgent: Promptagent;
  enumValues: Enumvalues;
}
export interface QuestionSlotDependency {
  slot: Slot;
  op: Op;
  value: Value;
}
export interface Value {
  [k: string]: unknown;
}
export interface StandardQuestionSlot {
  key: Key2;
  type: QuestionSlotType;
  required: Required1;
  deferrable: Deferrable1;
  dependsOn?: Dependson1;
  moduleGate?: ModuleType2;
  validation?: Validation1;
  promptHuman: Prompthuman1;
  promptAgent: Promptagent1;
}
