export const WORD_TYPES = [
  "normal",
  "word_form",
  "word_pattern",
  "sentence",
  "vietnamese",
] as const;

export type WordType = (typeof WORD_TYPES)[number];

export type WordInput = {
  input: string;
  type: WordType;
};

/** A word waiting in the local queue until the batch is sent. */
export type PendingWord = WordInput & { key: string };

export type BatchResult = {
  id: string;
  createdAt: string;
  count: number;
};

/** Must match MaxBatchSize in backend/internal/api/handler.go. */
export const MAX_BATCH_SIZE = 200;

export const TYPE_LABELS: Record<WordType, string> = {
  normal: "Normal",
  word_form: "Word form",
  word_pattern: "Word pattern",
  sentence: "Sentence",
  vietnamese: "Vietnamese → English",
};
