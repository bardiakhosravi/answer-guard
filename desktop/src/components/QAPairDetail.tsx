import type { QAPairRecord } from "../types";

interface Props {
  pair: QAPairRecord | null;
}

export default function QAPairDetail({ pair }: Props) {
  if (!pair) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-sm text-slate-500">
        Select a record on the left to view its details.
      </div>
    );
  }

  const methodLabel =
    pair.ingestionMethod === "HISTORICAL_IMPORT" ? "Historical Import" : "Runtime Capture";

  return (
    <div className="h-full overflow-auto p-6">
      <div className="mb-4 flex flex-wrap items-center gap-2 text-xs">
        <span className="inline-block rounded-full bg-slate-900 px-2.5 py-0.5 text-white font-semibold uppercase tracking-wide">
          {methodLabel}
        </span>
        <span className="text-slate-500">
          Captured {new Date(pair.capturedAt).toLocaleString()}
        </span>
        {pair.sourceTimestamp && (
          <span className="text-slate-500">
            · Source ts {new Date(pair.sourceTimestamp).toLocaleString()}
          </span>
        )}
      </div>

      <dl className="mb-6 grid grid-cols-[140px_1fr] gap-y-2 text-xs">
        <dt className="text-slate-500">Record ID</dt>
        <dd className="font-mono text-slate-700 break-all">{pair.id}</dd>
        <dt className="text-slate-500">Source system</dt>
        <dd className="font-mono text-slate-700">{pair.sourceSystemId}</dd>
        {pair.externalId && (
          <>
            <dt className="text-slate-500">External ID</dt>
            <dd className="font-mono text-slate-700 break-all">{pair.externalId}</dd>
          </>
        )}
      </dl>

      <Section label="Question">
        <div className="whitespace-pre-wrap rounded border border-slate-200 bg-slate-50 p-3 text-sm text-slate-900">
          {pair.questionText}
        </div>
      </Section>

      <Section label="Answer">
        <div className="whitespace-pre-wrap rounded border border-slate-200 bg-white p-3 text-sm text-slate-900">
          {pair.answerText}
        </div>
      </Section>

      {pair.metadata && Object.keys(pair.metadata).length > 0 && (
        <Section label="Metadata">
          <dl className="grid grid-cols-[140px_1fr] gap-y-1 rounded border border-slate-200 bg-slate-50 p-3 text-xs">
            {Object.entries(pair.metadata).map(([key, value]) => (
              <div key={key} className="contents">
                <dt className="text-slate-500 font-mono">{key}</dt>
                <dd className="text-slate-800 font-mono break-all">{String(value)}</dd>
              </div>
            ))}
          </dl>
        </Section>
      )}
    </div>
  );
}

function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="mb-4">
      <div className="mb-1 text-[11px] uppercase tracking-wider text-slate-500 font-semibold">
        {label}
      </div>
      {children}
    </div>
  );
}
