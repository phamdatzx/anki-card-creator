export const WORD_TYPES = [
  "normal",
  "word_form",
  "word_pattern",
  "sentence",
  "vietnamese",
] as const;

export type WordType = (typeof WORD_TYPES)[number];

export type Word = {
  id: string;
  input: string;
  type: WordType;
  createdAt: string;
  syncedAt: string | null;
};

export const TYPE_LABELS: Record<WordType, string> = {
  normal: "Normal",
  word_form: "Word form",
  word_pattern: "Word pattern",
  sentence: "Sentence",
  vietnamese: "Vietnamese → English",
};
