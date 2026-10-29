/** Mirrors anki_card_creator/lookups/contracts.py. */

export const CARD_TYPES = [
  "normal",
  "word_pattern",
  "sentence",
  "vietnamese",
  "collocation",
  "phrase",
] as const;

export type CardType = (typeof CARD_TYPES)[number];

export const TYPE_LABELS: Record<CardType, string> = {
  normal: "Normal",
  word_pattern: "Word pattern",
  sentence: "Sentence",
  vietnamese: "Vietnamese → English",
  collocation: "Collocation",
  phrase: "Phrase",
};

export const PLACEHOLDERS: Record<CardType, string> = {
  normal: "Enter a word in any form (e.g. deciding)…",
  word_pattern: "Enter a pattern (e.g. make a decision)…",
  sentence: "Enter an English sentence…",
  vietnamese: "Enter a Vietnamese word or meaning (e.g. quyết định)…",
  collocation: "Enter a keyword (e.g. decision)…",
  phrase: "Enter a phrase (e.g. sharp fall)…",
};

export const HINTS: Record<CardType, string> = {
  normal: "Normal: finds the root word, its meanings and its word family.",
  word_pattern: "Word pattern: create a contextual gap fill.",
  sentence: "Sentence: translate an English sentence into Vietnamese.",
  vietnamese:
    "Vietnamese → English: find matching English words for a Vietnamese meaning.",
  collocation:
    "Collocation: find a keyword's common partner words; each ticked one becomes a gap card.",
  phrase: "Phrase: look up a phrase's meanings; each ticked one becomes a recall card.",
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

/**
 * Word Inbox's Normal lookup: `input` is reduced to its root `word`; related
 * senses share a group (one card each); `family` lists other words of the
 * same root, each of which can become its own card.
 */
export type NormalGroupedPayload = {
  input: string;
  word: string;
  inputNote: string;
  groups: DefinitionResult[][];
  family: VietnameseResult[];
};

export type VietnamesePayload = { query: string; results: VietnameseResult[] };

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

export type PhraseSense = {
  structure: string;
  definition: string;
  vietnamese: string;
  examples: string[];
  usage: string;
};

export type PhrasePayload = { phrase: string; results: PhraseSense[] };

export type LookupResponse =
  | { type: "normal"; payload: NormalGroupedPayload }
  | { type: "vietnamese"; payload: VietnamesePayload }
  | { type: "word_pattern"; payload: WordPatternPayload }
  | { type: "sentence"; payload: SentencePayload }
  | { type: "collocation"; payload: CollocationPayload }
  | { type: "phrase"; payload: PhrasePayload };

/** `cards` includes subdecks' cards, as deleting a deck removes those too. */
export type Deck = { id: number; name: string; cards: number };

/** The server keeps `model` in memory; a restart goes back to `default`. */
export type ModelState = { model: string; default: string; choices: string[] };

export type SyncState = {
  enabled: boolean;
  at: number | null;
  ok: boolean | null;
  message: string;
  needs_forced_download: boolean;
};

export type CreateResponse = { added: number; deck: string; sync: SyncState };
