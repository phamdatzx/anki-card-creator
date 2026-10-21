/** Editable-form helpers shared by the editors and panels. */

import { asText, parseScore, scoreText, splitList } from "./text";
import type { WordFormItem } from "./types";

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

export function wordFormDraft(item: WordFormItem): Draft {
  return {
    word: item.word,
    type: item.type,
    ipa: item.ipa,
    vietnamese: item.vietnamese,
    definition: item.definition,
    examples: asText(item.examples, true),
    popularity: scoreText(item.popularity),
    difficulty: scoreText(item.difficulty),
  };
}

export function wordFormFromDraft(original: WordFormItem, draft: Draft): WordFormItem {
  return {
    ...original,
    word: draft.word.trim(),
    type: draft.type.trim(),
    ipa: draft.ipa.trim(),
    vietnamese: draft.vietnamese.trim(),
    definition: draft.definition.trim(),
    examples: splitList(draft.examples, true),
    popularity: parseScore(draft.popularity),
    difficulty: parseScore(draft.difficulty),
  };
}

export const WORD_FORM_FIELDS: FieldSpec[] = [
  { key: "word", label: "Word" },
  { key: "type", label: "Type" },
  { key: "ipa", label: "IPA", placeholder: "/ˈwɜrd/" },
  { key: "vietnamese", label: "Vietnamese", placeholder: "Required" },
  { key: "definition", label: "Definition", multiline: true, placeholder: "Required" },
  {
    key: "examples",
    label: "Examples",
    multiline: true,
    placeholder: "Required; one example per line",
  },
  ...SCORE_FIELDS,
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
