/** Result panels mirroring the add-on dialog's stacked panels. */

import { useState } from "react";
import {
  CollocationEditor,
  DefinitionEditor,
  PhraseEditor,
} from "./editors";
import { type Picked } from "./forms";
import { scoresCompact } from "./text";
import {
  GAP_MARK,
  type CollocationItem,
  type DefinitionResult,
  type PhraseSense,
  type VietnameseResult,
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

/** One Normal card per group; related parts of speech share a group. */
export type DefinitionGroup = Picked<Picked<DefinitionResult>[]>;

export function DefinitionGroupList({
  groups,
  onChange,
}: {
  groups: DefinitionGroup[];
  onChange: (next: DefinitionGroup[]) => void;
}) {
  const [editing, setEditing] = useState<{ group: string; part: string } | null>(null);
  const setGroup = (key: string, patch: Partial<DefinitionGroup>) =>
    onChange(groups.map((group) => (group.key === key ? { ...group, ...patch } : group)));
  const setPart = (groupKey: string, partKey: string, patch: Partial<Picked<DefinitionResult>>) =>
    onChange(
      groups.map((group) =>
        group.key === groupKey
          ? {
              ...group,
              data: group.data.map((part) => (part.key === partKey ? { ...part, ...patch } : part)),
            }
          : group,
      ),
    );
  const split = (key: string) =>
    onChange(
      groups.flatMap((group) =>
        group.key === key
          ? group.data.map((part) => ({
              key: crypto.randomUUID(),
              checked: group.checked,
              data: [{ ...part, checked: true }],
            }))
          : [group],
      ),
    );
  const current = editing
    ? groups
        .find((group) => group.key === editing.group)
        ?.data.find((part) => part.key === editing.part)
    : undefined;
  return (
    <>
      <ul className="picks">
        {groups.map((group) => {
          const parts = group.data.filter((part) => part.checked);
          const label = parts.map((part) => part.data.partOfSpeech || "?").join(" + ");
          return (
            <li key={group.key} className={group.checked ? "pick group checked" : "pick group"}>
              <div className="group-head">
                <label className="pick-main">
                  <input
                    type="checkbox"
                    checked={group.checked}
                    onChange={(e) => setGroup(group.key, { checked: e.target.checked })}
                    aria-label={`Create card: ${label || "no parts"}`}
                  />
                  <span className="group-label">
                    1 card · {label || "no part ticked"}
                  </span>
                </label>
                {group.data.length > 1 ? (
                  <button type="button" className="ghost small" onClick={() => split(group.key)}>
                    Split
                  </button>
                ) : null}
              </div>
              <ul className="parts">
                {group.data.map((part) => (
                  <li key={part.key} className={part.checked ? "part" : "part off"}>
                    <label className="pick-main">
                      {group.data.length > 1 ? (
                        <input
                          type="checkbox"
                          checked={part.checked}
                          onChange={(e) =>
                            setPart(group.key, part.key, { checked: e.target.checked })
                          }
                          aria-label={`Include ${part.data.partOfSpeech || "this part"}`}
                        />
                      ) : null}
                      <div className="pick-body">
                        <Definition item={part.data} />
                      </div>
                    </label>
                    <button
                      type="button"
                      className="ghost small"
                      onClick={() => setEditing({ group: group.key, part: part.key })}
                    >
                      Edit
                    </button>
                  </li>
                ))}
              </ul>
            </li>
          );
        })}
      </ul>
      {editing && current ? (
        <DefinitionEditor
          value={current.data}
          editableWord={false}
          onSave={(next) => {
            setPart(editing.group, editing.part, { data: next });
            setEditing(null);
          }}
          onCancel={() => setEditing(null)}
        />
      ) : null}
    </>
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
