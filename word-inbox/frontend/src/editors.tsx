/** Popup versions of the add-on's DefinitionDetailDialog and FamilyMemberDialog. */

import { useState } from "react";
import {
  COLLOCATION_FIELDS,
  SCORE_FIELDS,
  WORD_FORM_FIELDS,
  wordFormDraft,
  wordFormFromDraft,
  type Draft,
  type FieldSpec,
} from "./forms";
import { Modal } from "./modal";
import { asText, parseScore, scoreText, splitList } from "./text";
import {
  GAP_MARK,
  type CollocationItem,
  type DefinitionResult,
  type VietnameseResult,
  type WordFormItem,
} from "./types";

export function FieldsForm({
  fields,
  draft,
  onChange,
}: {
  fields: FieldSpec[];
  draft: Draft;
  onChange: (next: Draft) => void;
}) {
  return (
    <div className="fields">
      {fields.map((field) => (
        <label key={field.key} className="field">
          <span>{field.label}</span>
          {field.multiline ? (
            <textarea
              rows={3}
              value={draft[field.key]}
              placeholder={field.placeholder}
              onChange={(e) => onChange({ ...draft, [field.key]: e.target.value })}
            />
          ) : (
            <input
              value={draft[field.key]}
              placeholder={field.placeholder}
              onChange={(e) => onChange({ ...draft, [field.key]: e.target.value })}
            />
          )}
        </label>
      ))}
    </div>
  );
}

function EditorShell({
  title,
  children,
  onSave,
  onCancel,
}: {
  title: string;
  children: React.ReactNode;
  onSave: () => void;
  onCancel: () => void;
}) {
  return (
    <Modal
      title={title}
      onClose={onCancel}
      closeOnBackdrop={false}
      footer={
        <>
          <button type="button" className="ghost" onClick={onCancel}>
            Cancel
          </button>
          <button type="button" className="primary" onClick={onSave}>
            Save
          </button>
        </>
      }
    >
      {children}
    </Modal>
  );
}

export function DefinitionEditor<T extends DefinitionResult | VietnameseResult>({
  value,
  editableWord,
  onSave,
  onCancel,
}: {
  value: T;
  editableWord: boolean;
  onSave: (next: T) => void;
  onCancel: () => void;
}) {
  const [draft, setDraft] = useState<Draft>(() => ({
    word: "word" in value ? value.word : "",
    definition: value.definition,
    vietnamese: value.vietnamese,
    partOfSpeech: value.partOfSpeech,
    ipa: value.ipa,
    synonyms: asText(value.synonyms),
    examples: asText(value.examples, true),
    popularity: scoreText(value.popularity),
    difficulty: scoreText(value.difficulty),
  }));
  const fields: FieldSpec[] = [
    ...(editableWord ? [{ key: "word", label: "Word", placeholder: "Required" }] : []),
    { key: "definition", label: "Definition", multiline: true },
    { key: "vietnamese", label: "Vietnamese" },
    { key: "partOfSpeech", label: "Part of speech" },
    { key: "ipa", label: "IPA", placeholder: "/ˈwɜrd/" },
    { key: "synonyms", label: "Synonyms", placeholder: "comma-separated" },
    {
      key: "examples",
      label: "Examples",
      multiline: true,
      placeholder: "one example per line, or comma-separated",
    },
    ...SCORE_FIELDS,
  ];
  function save() {
    onSave({
      ...value,
      ...(editableWord ? { word: draft.word.trim() } : {}),
      definition: draft.definition.trim(),
      vietnamese: draft.vietnamese.trim(),
      partOfSpeech: draft.partOfSpeech.trim(),
      ipa: draft.ipa.trim(),
      synonyms: splitList(draft.synonyms),
      examples: splitList(draft.examples, true),
      popularity: parseScore(draft.popularity),
      difficulty: parseScore(draft.difficulty),
    });
  }
  return (
    <EditorShell
      title={"word" in value && value.word ? `Edit definition — ${value.word}` : "Edit definition"}
      onSave={save}
      onCancel={onCancel}
    >
      <FieldsForm fields={fields} draft={draft} onChange={setDraft} />
    </EditorShell>
  );
}

export function FamilyEditor({
  value,
  onSave,
  onCancel,
}: {
  value: WordFormItem;
  onSave: (next: WordFormItem) => void;
  onCancel: () => void;
}) {
  const [draft, setDraft] = useState<Draft>(() => wordFormDraft(value));
  return (
    <EditorShell
      title={value.word ? `Edit word form — ${value.word}` : "Add word form"}
      onSave={() => onSave(wordFormFromDraft(value, draft))}
      onCancel={onCancel}
    >
      <FieldsForm fields={WORD_FORM_FIELDS} draft={draft} onChange={setDraft} />
    </EditorShell>
  );
}

export function CollocationEditor({
  value,
  onSave,
  onCancel,
}: {
  value: CollocationItem;
  onSave: (next: CollocationItem) => void;
  onCancel: () => void;
}) {
  const [draft, setDraft] = useState<Draft>(() => ({ ...value }));
  const blanks = draft.gap.split(GAP_MARK).length - 1;
  function save() {
    onSave({
      pattern: draft.pattern.trim(),
      collocation: draft.collocation.trim(),
      gap: draft.gap.trim(),
      answer: draft.answer.trim(),
      vietnamese: draft.vietnamese.trim(),
      usage: draft.usage.trim(),
    });
  }
  return (
    <EditorShell
      title={value.collocation ? `Edit collocation — ${value.collocation}` : "Edit collocation"}
      onSave={save}
      onCancel={onCancel}
    >
      <FieldsForm fields={COLLOCATION_FIELDS} draft={draft} onChange={setDraft} />
      {blanks !== 1 ? (
        <p className="error">The gap sentence needs exactly one {GAP_MARK}.</p>
      ) : null}
    </EditorShell>
  );
}
