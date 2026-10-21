/** Mirrors anki_card_creator/lookups/contracts.py. */

export const CARD_TYPES = [
  "normal",
  "word_form",
  "word_pattern",
  "sentence",
  "vietnamese",
  "collocation",
] as const;

export type CardType = (typeof CARD_TYPES)[number];

export const TYPE_LABELS: Record<CardType, string> = {
  normal: "Normal",
  word_form: "Word form",
  word_pattern: "Word pattern",
  sentence: "Sentence",
  vietnamese: "Vietnamese → English",
  collocation: "Collocation",
};

export const PLACEHOLDERS: Record<CardType, string> = {
  normal: "Enter a word or phrasal verb…",
  word_form: "Enter a word (any form)…",
  word_pattern: "Enter a pattern (e.g. make a decision)…",
  sentence: "Enter an English sentence…",
  vietnamese: "Enter a Vietnamese word or meaning (e.g. quyết định)…",
  collocation: "Enter a keyword (e.g. decision)…",
};

export const HINTS: Record<CardType, string> = {
  normal: "Normal: look up senses and select definitions.",
  word_form: "Word form: find a root and related forms.",
  word_pattern: "Word pattern: create a contextual gap fill.",
  sentence: "Sentence: translate an English sentence into Vietnamese.",
  vietnamese:
    "Vietnamese → English: find matching English words for a Vietnamese meaning.",
  collocation:
    "Collocation: find a keyword's common partner words; each ticked one becomes a gap card.",
};

export type Score = number | null;

export type DefinitionResult = {
  definition: string;
  vietnamese: string;
  partOfSpeech: string;
  ipa: string;
  synonyms: string[];
  examples: string[];
  popularity: Score;
  difficulty: Score;
};

export type VietnameseResult = DefinitionResult & { word: string };

export type NormalPayload = { word: string; results: DefinitionResult[] };

export type VietnamesePayload = { query: string; results: VietnameseResult[] };

export type WordFormItem = {
  word: string;
  type: string;
  definition: string;
  vietnamese: string;
  examples: string[];
  ipa: string;
  popularity: Score;
  difficulty: Score;
};

export type WordFormPayload = { rootWord: WordFormItem; other: WordFormItem[] };

export type WordPatternPayload = {
  gap: string;
  vietnamese: string;
  answer: string;
  pattern: string;
  explanation: string;
  examples: string[];
};

/** The server adds the looked-up English sentence to the translation. */
export type SentencePayload = { vietnamese: string; sentence: string };

/** The blank the partner word goes in; `gap` must contain exactly one. */
export const GAP_MARK = "___";

export type CollocationItem = {
  pattern: string;
  collocation: string;
  gap: string;
  answer: string;
  vietnamese: string;
  usage: string;
};

export type CollocationPayload = { keyword: string; items: CollocationItem[] };

export type LookupResponse =
  | { type: "normal"; payload: NormalPayload }
  | { type: "vietnamese"; payload: VietnamesePayload }
  | { type: "word_form"; payload: WordFormPayload }
  | { type: "word_pattern"; payload: WordPatternPayload }
  | { type: "sentence"; payload: SentencePayload }
  | { type: "collocation"; payload: CollocationPayload };

/** `cards` includes subdecks' cards, as deleting a deck removes those too. */
export type Deck = { id: number; name: string; cards: number };

export type SyncState = {
  enabled: boolean;
  at: number | null;
  ok: boolean | null;
  message: string;
  needs_forced_download: boolean;
};

export type CreateResponse = { added: number; deck: string; sync: SyncState };
