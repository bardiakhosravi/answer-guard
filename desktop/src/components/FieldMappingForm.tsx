import { useState } from "react";
import type { DiscoveredColumn, FieldMapping } from "../types";

interface Props {
  columns: DiscoveredColumn[];
  initial?: FieldMapping;
  onSubmit: (mapping: FieldMapping) => void;
  onBack: () => void;
}

export default function FieldMappingForm({ columns, initial, onSubmit, onBack }: Props) {
  const [questionColumn, setQuestionColumn] = useState(initial?.questionColumn ?? "");
  const [answerColumn, setAnswerColumn] = useState(initial?.answerColumn ?? "");
  const [timestampColumn, setTimestampColumn] = useState(initial?.timestampColumn ?? "");
  const [externalIdColumn, setExternalIdColumn] = useState(initial?.externalIdColumn ?? "");
  const [metadataColumns, setMetadataColumns] = useState<{ key: string; column: string }[]>(
    initial ? Object.entries(initial.metadataColumns).map(([key, column]) => ({ key, column })) : [],
  );

  const canSubmit = questionColumn && answerColumn;

  function submit() {
    const metadata: Record<string, string> = {};
    for (const { key, column } of metadataColumns) {
      if (key.trim() && column.trim()) metadata[key.trim()] = column.trim();
    }
    onSubmit({
      questionColumn,
      answerColumn,
      timestampColumn: timestampColumn || undefined,
      externalIdColumn: externalIdColumn || undefined,
      metadataColumns: metadata,
    });
  }

  return (
    <div className="grid grid-cols-[1fr_1.4fr] gap-8">
      {/* Left: discovered columns */}
      <section>
        <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Discovered columns ({columns.length})
        </h3>
        <div className="max-h-[500px] overflow-auto rounded border border-slate-200">
          {columns.map((col) => (
            <div
              key={col.name}
              className="flex items-center justify-between border-b border-slate-100 px-3 py-2 text-sm last:border-b-0"
            >
              <span className="font-mono text-slate-800">{col.name}</span>
              <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                {col.type}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Right: mapping form */}
      <section>
        <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Map to AnswerGuard fields
        </h3>

        <MappingField label="Question column" required>
          <Dropdown value={questionColumn} onChange={setQuestionColumn} columns={columns} />
        </MappingField>

        <MappingField label="Answer column" required>
          <Dropdown value={answerColumn} onChange={setAnswerColumn} columns={columns} />
        </MappingField>

        <MappingField label="Timestamp column">
          <Dropdown value={timestampColumn} onChange={setTimestampColumn} columns={columns} allowNone />
        </MappingField>

        <MappingField label="External ID column">
          <Dropdown value={externalIdColumn} onChange={setExternalIdColumn} columns={columns} allowNone />
        </MappingField>

        <div className="mt-6">
          <h4 className="mb-2 text-sm font-medium text-slate-700">Metadata columns</h4>
          {metadataColumns.map((pair, i) => (
            <div key={i} className="mb-2 flex gap-2">
              <input
                type="text"
                placeholder="Key (e.g. topic)"
                value={pair.key}
                onChange={(e) => {
                  const next = [...metadataColumns];
                  next[i] = { ...next[i], key: e.target.value };
                  setMetadataColumns(next);
                }}
                className="flex-1 rounded border border-slate-300 px-3 py-1.5 text-sm"
              />
              <Dropdown
                value={pair.column}
                onChange={(v) => {
                  const next = [...metadataColumns];
                  next[i] = { ...next[i], column: v };
                  setMetadataColumns(next);
                }}
                columns={columns}
              />
              <button
                type="button"
                onClick={() => setMetadataColumns(metadataColumns.filter((_, idx) => idx !== i))}
                className="rounded border border-slate-300 px-2 text-sm text-slate-600 hover:bg-slate-50"
              >
                ✕
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={() => setMetadataColumns([...metadataColumns, { key: "", column: "" }])}
            className="mt-1 rounded border border-dashed border-slate-300 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-50"
          >
            + Add metadata field
          </button>
        </div>

        <div className="mt-8 flex justify-between">
          <button
            type="button"
            onClick={onBack}
            className="rounded border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50"
          >
            ← Back
          </button>
          <button
            type="button"
            disabled={!canSubmit}
            onClick={submit}
            className="rounded bg-slate-900 px-6 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50 hover:bg-slate-800"
          >
            Review Mapping →
          </button>
        </div>
      </section>
    </div>
  );
}

function MappingField({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div className="mb-4">
      <label className="mb-1 block text-sm font-medium text-slate-700">
        {label}
        {required && <span className="ml-1 text-rose-600">*</span>}
      </label>
      {children}
    </div>
  );
}

function Dropdown({
  value,
  onChange,
  columns,
  allowNone,
}: {
  value: string;
  onChange: (v: string) => void;
  columns: DiscoveredColumn[];
  allowNone?: boolean;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full rounded border border-slate-300 px-3 py-1.5 text-sm bg-white"
    >
      <option value="">{allowNone ? "(none)" : "Select a column…"}</option>
      {columns.map((col) => (
        <option key={col.name} value={col.name}>
          {col.name} ({col.type})
        </option>
      ))}
    </select>
  );
}
