/** Result panels mirroring the add-on dialog's stacked panels. */

import { useState } from "react";
import {
  CollocationEditor,
  DefinitionEditor,
  FamilyEditor,
  FieldsForm,
  PhraseEditor,
} from "./editors";
import { WORD_FORM_FIELDS, picked, type Draft, type FieldSpec, type Picked } from "./forms";
import { scoresCompact, wordFormSummaries } from "./text";
import {
  GAP_MARK,
  type CollocationItem,
  type DefinitionResult,
  type PhraseSense,
  type VietnameseResult,
  type WordFormItem,
} from "./types";

function Scores({ item }: { item: { popularity: number | null; difficulty: number | null } }) {
  const text = scoresCompact(item);
  return text ? <div className="scores">{text}</div> : null;
}

function PickList<T>({
  items,
  onChange,
  render,
  editor,
  empty,
}: {
  items: Picked<T>[];
  onChange: (next: Picked<T>[]) => void;
  render: (item: T) => React.ReactNode;
  editor: (item: T, save: (next: T) => void, cancel: () => void) => React.ReactNode;
  empty?: React.ReactNode;
}) {
  const [editing, setEditing] = useState<string | null>(null);
  const update = (key: string, patch: Partial<Picked<T>>) =>
    onChange(items.map((item) => (item.key === key ? { ...item, ...patch } : item)));
  if (items.length === 0) {
    return <>{empty}</>;
  }
  const current = items.find((item) => item.key === editing);
  return (
    <>
      <ul className="picks">
        {items.map((item) => (
          <li key={item.key} className={item.checked ? "pick checked" : "pick"}>
            <label className="pick-main">
              <input
                type="checkbox"
                checked={item.checked}
                onChange={(e) => update(item.key, { checked: e.target.checked })}
              />
              <div className="pick-body">{render(item.data)}</div>
            </label>
            <div className="pick-actions">
              <button type="button" className="ghost small" onClick={() => setEditing(item.key)}>
                Edit
              </button>
            </div>
          </li>
        ))}
      </ul>
      {current
        ? editor(
            current.data,
            (next) => {
              update(current.key, { data: next });
              setEditing(null);
            },
            () => setEditing(null),
          )
        : null}
    </>
  );
}

function Definition({ item, word }: { item: DefinitionResult; word?: string }) {
  return (
    <>
      <Scores item={item} />
      <div className="pick-title">
        {word ? <strong>{word} </strong> : null}
        <span className="badge">{item.partOfSpeech || "?"}</span> {item.definition}
      </div>
      {item.vietnamese ? <div className="vi">{item.vietnamese}</div> : null}
      {item.ipa ? <div className="ipa">{item.ipa}</div> : null}
      {item.synonyms.length ? (
        <div className="meta">Synonyms: {item.synonyms.join(", ")}</div>
      ) : null}
      {item.examples.length ? (
        <ul className="examples">
          {item.examples.map((example, index) => (
            <li key={index}>{example}</li>
          ))}
        </ul>
      ) : null}
    </>
  );
}

export function DefinitionList({
  items,
  onChange,
}: {
  items: Picked<DefinitionResult>[];
  onChange: (next: Picked<DefinitionResult>[]) => void;
}) {
  return (
    <PickList
      items={items}
      onChange={onChange}
      render={(item) => <Definition item={item} />}
      editor={(item, save, cancel) => (
        <DefinitionEditor value={item} editableWord={false} onSave={save} onCancel={cancel} />
      )}
    />
  );
}

export function VietnameseList({
  items,
  onChange,
}: {
  items: Picked<VietnameseResult>[];
  onChange: (next: Picked<VietnameseResult>[]) => void;
}) {
  return (
    <PickList
      items={items}
      onChange={onChange}
      render={(item) => <Definition item={item} word={item.word || "?"} />}
      editor={(item, save, cancel) => (
        <DefinitionEditor value={item} editableWord onSave={save} onCancel={cancel} />
      )}
    />
  );
}

const EMPTY_FORM: WordFormItem = {
  word: "",
  type: "",
  definition: "",
  vietnamese: "",
  examples: [],
  ipa: "",
  popularity: null,
  difficulty: null,
};

const ROOT_FIELDS: FieldSpec[] = WORD_FORM_FIELDS.map((field) => ({
  ...field,
  // "Root word", but "Root IPA" and "Root Vietnamese", as in the add-on.
  label: `Root ${/^(IPA|Vietnamese)/.test(field.label) ? field.label : field.label.toLowerCase()}`,
}));

export function WordFormPanel({
  root,
  onRoot,
  others,
  onOthers,
}: {
  root: Draft;
  onRoot: (next: Draft) => void;
  others: Picked<WordFormItem>[];
  onOthers: (next: Picked<WordFormItem>[]) => void;
}) {
  const [adding, setAdding] = useState(false);
  const cards = wordFormSummaries(
    { ...EMPTY_FORM, word: root.word.trim(), type: root.type.trim() },
    others.filter((item) => item.checked).map((item) => item.data),
  );
  return (
    <div className="stack">
      <div className="summary">
        {cards.length ? (
          <>
            Will create {cards.length} card(s):
            <ul>
              {cards.map((card, index) => (
                <li key={index}>{card}</li>
              ))}
            </ul>
          </>
        ) : (
          "Check at least one related form to create cards."
        )}
      </div>
      <FieldsForm fields={ROOT_FIELDS} draft={root} onChange={onRoot} />
      <div className="row">
        <h3>Related forms</h3>
        {!adding ? (
          <button type="button" className="ghost small" onClick={() => setAdding(true)}>
            Add form
          </button>
        ) : null}
      </div>
      {adding ? (
        <FamilyEditor
          value={EMPTY_FORM}
          onSave={(item) => {
            onOthers([...others, ...picked([item], true)]);
            setAdding(false);
          }}
          onCancel={() => setAdding(false)}
        />
      ) : null}
      <PickList
        items={others}
        onChange={onOthers}
        empty={<p className="muted">No related forms.</p>}
        render={(item) => (
          <>
            <Scores item={item} />
            <div className="pick-title">
              <strong>{item.word || "?"}</strong>{" "}
              <span className="badge">{item.type || "?"}</span> {item.vietnamese}
            </div>
            <div>{item.definition}</div>
            {item.ipa ? <div className="ipa">{item.ipa}</div> : null}
            {item.examples.length ? (
              <ul className="examples">
                {item.examples.map((example, index) => (
                  <li key={index}>{example}</li>
                ))}
              </ul>
            ) : null}
          </>
        )}
        editor={(item, save, cancel) => (
          <FamilyEditor value={item} onSave={save} onCancel={cancel} />
        )}
      />
    </div>
  );
}

function GapWithAnswer({ gap, answer }: { gap: string; answer: string }) {
  const [before, ...rest] = gap.split(GAP_MARK);
  if (rest.length !== 1) {
    return <>{gap}</>;
  }
  return (
    <>
      {before}
      <mark className="answer">{answer || "?"}</mark>
      {rest[0]}
    </>
  );
}

export function CollocationList({
  items,
  onChange,
}: {
  items: Picked<CollocationItem>[];
  onChange: (next: Picked<CollocationItem>[]) => void;
}) {
  return (
    <PickList
      items={items}
      onChange={onChange}
      render={(item) => (
        <>
          <div className="pick-title">
            <span className="badge">{item.pattern || "?"}</span> <strong>{item.collocation}</strong>
          </div>
          {item.vietnamese ? <div className="vi">{item.vietnamese}</div> : null}
          <div className="gap-line">
            <GapWithAnswer gap={item.gap} answer={item.answer} />
          </div>
          {item.usage ? <div className="meta">{item.usage}</div> : null}
        </>
      )}
      editor={(item, save, cancel) => (
        <CollocationEditor value={item} onSave={save} onCancel={cancel} />
      )}
    />
  );
}

export function PhraseList({
  phrase,
  items,
  onChange,
}: {
  phrase: string;
  items: Picked<PhraseSense>[];
  onChange: (next: Picked<PhraseSense>[]) => void;
}) {
  return (
    <PickList
      items={items}
      onChange={onChange}
      render={(item) => (
        <>
          <div className="pick-title">
            <span className="badge">{item.structure || "?"}</span> {item.definition}
          </div>
          {item.vietnamese ? <div className="vi">{item.vietnamese}</div> : null}
          {item.examples.length ? (
            <ul className="examples">
              {item.examples.map((example, index) => (
                <li key={index}>{example}</li>
              ))}
            </ul>
          ) : null}
          {item.usage ? <div className="meta">{item.usage}</div> : null}
        </>
      )}
      editor={(item, save, cancel) => (
        <PhraseEditor value={item} phrase={phrase} onSave={save} onCancel={cancel} />
      )}
    />
  );
}
