import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { listResponseFeedback } from "../lib/api";
import type { ResponseFeedback } from "../types";

interface Props {
  page: number;
  pageSize: number;
  search?: string;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onPageChange: (page: number) => void;
}

export default function ResponseFeedbackList({
  page,
  pageSize,
  search,
  selectedId,
  onSelect,
  onPageChange,
}: Props) {
  const { data, isLoading, isFetching, error } = useQuery({
    queryKey: ["response-feedback", page, pageSize, search],
    queryFn: () => listResponseFeedback({ page, pageSize, search }),
    placeholderData: keepPreviousData,
  });

  if (isLoading) {
    return <div className="p-8 text-center text-sm text-slate-500">Loading feedback…</div>;
  }
  if (error) {
    return (
      <div className="m-4 rounded border border-rose-300 bg-rose-50 p-3 text-sm text-rose-900">
        Failed to load feedback.
      </div>
    );
  }
  if (!data || data.items.length === 0) {
    return (
      <div className="p-8 text-center text-sm text-slate-500">
        {search ? `No feedback matches "${search}".` : "No feedback captured yet."}
      </div>
    );
  }

  const totalPages = Math.max(1, Math.ceil(data.total / pageSize));

  return (
    <div className="flex h-full flex-col">
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
        {data.items.map((fb) => (
          <Row
            key={fb.id}
            feedback={fb}
            active={fb.id === selectedId}
            onClick={() => onSelect(fb.id)}
          />
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
  feedback,
  active,
  onClick,
}: {
  feedback: ResponseFeedback;
  active: boolean;
  onClick: () => void;
}) {
  const createdDate = new Date(feedback.createdAt).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
  const isWhole = feedback.spanStart === null;
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
          {feedback.problem}
        </div>
        <div
          className={`mt-0.5 text-xs line-clamp-1 italic font-mono ${
            active ? "text-slate-300" : "text-slate-500"
          }`}
        >
          "{feedback.excerpt}"
        </div>
        <div
          className={`mt-1 flex items-center gap-2 text-[11px] ${
            active ? "text-slate-300" : "text-slate-500"
          }`}
        >
          <span>{createdDate}</span>
          <span className="ml-auto rounded px-1.5 py-0.5 text-[10px] font-mono uppercase tracking-wide bg-slate-100 text-slate-700">
            {isWhole ? "whole" : "selection"}
          </span>
        </div>
      </button>
    </li>
  );
}
