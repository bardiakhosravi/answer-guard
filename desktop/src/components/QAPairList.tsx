import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { listQAPairs } from "../lib/api";
import type { QAPairRecord } from "../types";

interface Props {
  page: number;
  pageSize: number;
  sourceSystemId?: string;
  search?: string;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onPageChange: (page: number) => void;
}

export default function QAPairList({
  page,
  pageSize,
  sourceSystemId,
  search,
  selectedId,
  onSelect,
  onPageChange,
}: Props) {
  const { data, isLoading, isFetching, error } = useQuery({
    queryKey: ["qa-pairs", page, pageSize, sourceSystemId, search],
    queryFn: () => listQAPairs({ page, pageSize, sourceSystemId, search }),
    placeholderData: keepPreviousData,
  });

  if (isLoading) {
    return <div className="p-8 text-center text-sm text-slate-500">Loading records…</div>;
  }
  if (error) {
    return (
      <div className="p-4 rounded border border-rose-300 bg-rose-50 text-sm text-rose-900">
        Failed to load records.
      </div>
    );
  }
  if (!data || data.items.length === 0) {
    return (
      <div className="p-8 text-center text-sm text-slate-500">
        {search ? `No records match "${search}".` : "No records yet."}
      </div>
    );
  }

  const totalPages = Math.max(1, Math.ceil(data.total / pageSize));

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-2 text-xs text-slate-600">
        <span>
          {data.total.toLocaleString()} records
          {isFetching && <span className="ml-2 text-slate-400">refreshing…</span>}
        </span>
        <span>
          Page {page} of {totalPages}
        </span>
      </div>

      <ul className="flex-1 divide-y divide-slate-100 overflow-auto">
        {data.items.map((pair) => (
          <Row key={pair.id} pair={pair} active={pair.id === selectedId} onClick={() => onSelect(pair.id)} />
        ))}
      </ul>

      <div className="flex items-center justify-between border-t border-slate-200 px-4 py-2">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="rounded border border-slate-300 px-3 py-1 text-xs disabled:opacity-40 hover:bg-slate-50"
        >
          ← Prev
        </button>
        <span className="text-xs text-slate-500">
          Showing {(page - 1) * pageSize + 1}–
          {Math.min(page * pageSize, data.total)} of {data.total.toLocaleString()}
        </span>
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="rounded border border-slate-300 px-3 py-1 text-xs disabled:opacity-40 hover:bg-slate-50"
        >
          Next →
        </button>
      </div>
    </div>
  );
}

function Row({
  pair,
  active,
  onClick,
}: {
  pair: QAPairRecord;
  active: boolean;
  onClick: () => void;
}) {
  const capturedDate = new Date(pair.capturedAt).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
  return (
    <li>
      <button
        onClick={onClick}
        className={`w-full px-4 py-3 text-left transition-colors ${
          active ? "bg-slate-900 text-white" : "hover:bg-slate-50"
        }`}
      >
        <div
          className={`text-sm font-medium line-clamp-2 ${active ? "text-white" : "text-slate-900"}`}
        >
          {pair.questionText}
        </div>
        <div
          className={`mt-0.5 text-xs line-clamp-1 ${active ? "text-slate-300" : "text-slate-500"}`}
        >
          {pair.answerText}
        </div>
        <div
          className={`mt-1 flex items-center gap-2 text-[11px] ${
            active ? "text-slate-300" : "text-slate-500"
          }`}
        >
          <span>{capturedDate}</span>
          <span>·</span>
          <span className="truncate">{pair.sourceSystemId}</span>
          <span className="ml-auto rounded px-1.5 py-0.5 text-[10px] font-mono uppercase tracking-wide bg-slate-100 text-slate-700">
            {pair.ingestionMethod === "HISTORICAL_IMPORT" ? "import" : "runtime"}
          </span>
        </div>
      </button>
    </li>
  );
}
