/** Editable-form helpers shared by the editors and panels. */

export type FieldSpec = {
  key: string;
  label: string;
  multiline?: boolean;
  placeholder?: string;
};

export type Draft = Record<string, string>;

export const SCORE_FIELDS: FieldSpec[] = [
  { key: "popularity", label: "Popularity (1–5)", placeholder: "1–5" },
  { key: "difficulty", label: "Difficulty (1–5)", placeholder: "1–5" },
];

export type Picked<T> = { key: string; checked: boolean; data: T };

export function picked<T>(items: T[], checked: boolean): Picked<T>[] {
  return items.map((data) => ({ key: crypto.randomUUID(), checked, data }));
}

export const PATTERN_FIELDS: FieldSpec[] = [
  {
    key: "gap",
    label: "Gap (front)",
    multiline: true,
    placeholder: "Gap sentence — e.g. She (đưa ra quyết định) to quit her job.",
  },
  { key: "vietnamese", label: "Vietnamese", placeholder: "Vietnamese meaning of the pattern" },
  { key: "answer", label: "Answer" },
  { key: "pattern", label: "Pattern" },
  { key: "explanation", label: "Explanation", multiline: true },
  { key: "examples", label: "Examples", multiline: true, placeholder: "one example per line" },
];

export const SENTENCE_FIELDS: FieldSpec[] = [
  { key: "vietnamese", label: "Vietnamese (front)", multiline: true },
  { key: "sentence", label: "English (back)", multiline: true },
];

export const COLLOCATION_FIELDS: FieldSpec[] = [
  { key: "pattern", label: "Pattern", placeholder: "e.g. verb + decision" },
  { key: "collocation", label: "Collocation", placeholder: "e.g. make a decision" },
  {
    key: "gap",
    label: "Gap sentence (front)",
    multiline: true,
    placeholder: "Put ___ where the partner word goes",
  },
  { key: "answer", label: "Answer", placeholder: "Text that fills the ___" },
  { key: "vietnamese", label: "Vietnamese" },
  { key: "usage", label: "Usage note", placeholder: "e.g. formal, written" },
];

export const PHRASE_FIELDS: FieldSpec[] = [
  { key: "structure", label: "Structure", placeholder: "e.g. adjective + noun" },
  {
    key: "definition",
    label: "Definition (front)",
    multiline: true,
    placeholder: "Don't use the phrase's own words",
  },
  { key: "vietnamese", label: "Vietnamese" },
  { key: "examples", label: "Examples", multiline: true, placeholder: "one example per line" },
  { key: "usage", label: "Usage note", placeholder: "e.g. news, business" },
];
