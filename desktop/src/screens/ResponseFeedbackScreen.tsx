import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  deleteResponseFeedback,
  listResponseFeedback,
  updateResponseFeedback,
} from "../lib/api";
import ResponseFeedbackList from "../components/ResponseFeedbackList";
import ImprovementFormModal from "../components/ImprovementFormModal";
import type { ResponseFeedback } from "../types";

const PAGE_SIZE = 50;

export default function ResponseFeedbackScreen() {
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const navigate = useNavigate();
  const queryClient = useQueryClient();

  useEffect(() => {
    const id = setTimeout(() => {
      setSearch(searchInput.trim());
      setPage(1);
    }, 300);
    return () => clearTimeout(id);
  }, [searchInput]);

  const { data: currentPage } = useQuery({
    queryKey: ["response-feedback", page, PAGE_SIZE, search],
    queryFn: () => listResponseFeedback({ page, pageSize: PAGE_SIZE, search }),
  });

  const selected: ResponseFeedback | null = useMemo(() => {
    if (!selectedId || !currentPage) return null;
    return currentPage.items.find((f) => f.id === selectedId) ?? null;
  }, [selectedId, currentPage]);

  const updateMutation = useMutation({
    mutationFn: ({ id, problem, desiredBehavior }: { id: string; problem: string; desiredBehavior: string }) =>
      updateResponseFeedback(id, { problem, desiredBehavior }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["response-feedback"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteResponseFeedback(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["response-feedback"] });
    },
  });

  const handleEdit = async (problem: string, desiredBehavior: string) => {
    if (!selected) return;
    await updateMutation.mutateAsync({ id: selected.id, problem, desiredBehavior });
    setEditOpen(false);
    setToast("Feedback updated.");
    setTimeout(() => setToast(null), 3000);
  };

  const handleDelete = async () => {
    if (!selected) return;
    const deletedId = selected.id;
    await deleteMutation.mutateAsync(deletedId);
    setConfirmDeleteOpen(false);
    setSelectedId(null);
    setToast("Feedback deleted.");
    setTimeout(() => setToast(null), 3000);
  };

  const totalCount = currentPage?.total ?? 0;

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-200 bg-slate-50 px-6 py-3">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-bold text-slate-900">Response Feedback</h1>
          <span className="text-xs text-slate-600">
            <strong className="text-slate-900">{totalCount.toLocaleString()}</strong> total records
          </span>
        </div>

        <div className="mt-3">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search problem, desired behavior, or excerpt…"
            className="w-full rounded border border-slate-300 bg-white px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-slate-300"
          />
        </div>
      </div>

      <div className="grid grid-cols-[420px_1fr] flex-1 overflow-hidden">
        <div className="border-r border-slate-200 overflow-hidden">
          <ResponseFeedbackList
            page={page}
            pageSize={PAGE_SIZE}
            search={search}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onPageChange={(p) => {
              setPage(p);
              setSelectedId(null);
            }}
          />
        </div>
        <Detail
          feedback={selected}
          onOpenSource={(qaPairId) =>
            navigate("/data", { state: { openQAPairId: qaPairId } })
          }
          onEdit={() => setEditOpen(true)}
          onDelete={() => setConfirmDeleteOpen(true)}
        />
      </div>

      {selected && (
        <ImprovementFormModal
          open={editOpen}
          mode="edit"
          excerpt={selected.excerpt}
          initialProblem={selected.problem}
          initialDesiredBehavior={selected.desiredBehavior}
          onClose={() => setEditOpen(false)}
          onSave={handleEdit}
        />
      )}

      {confirmDeleteOpen && selected && (
        <ConfirmDeleteDialog
          onCancel={() => setConfirmDeleteOpen(false)}
          onConfirm={handleDelete}
          busy={deleteMutation.isPending}
        />
      )}

      {toast && (
        <div className="fixed bottom-6 right-6 z-50 rounded bg-slate-900 px-4 py-2 text-sm text-white shadow-lg">
          {toast}
        </div>
      )}
    </div>
  );
}

function Detail({
  feedback,
  onOpenSource,
  onEdit,
  onDelete,
}: {
  feedback: ResponseFeedback | null;
  onOpenSource: (qaPairId: string) => void;
  onEdit: () => void;
  onDelete: () => void;
}) {
  if (!feedback) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-sm text-slate-500">
        Select a feedback record on the left to view its details.
      </div>
    );
  }

  const isWhole = feedback.spanStart === null;

  return (
    <div className="h-full overflow-auto p-6">
      <div className="mb-4 flex flex-wrap items-center gap-2 text-xs">
        <span className="inline-block rounded-full bg-slate-900 px-2.5 py-0.5 text-white font-semibold uppercase tracking-wide">
          {isWhole ? "Whole response" : "Selection"}
        </span>
        <span className="text-slate-500">
          Captured {new Date(feedback.createdAt).toLocaleString()}
        </span>
        {feedback.createdAt !== feedback.updatedAt && (
          <span className="text-slate-500">
            · Updated {new Date(feedback.updatedAt).toLocaleString()}
          </span>
        )}
        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={onEdit}
            className="rounded border border-slate-300 bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            Edit
          </button>
          <button
            onClick={onDelete}
            className="rounded border border-rose-300 bg-white px-2.5 py-1 text-xs font-semibold text-rose-700 hover:bg-rose-50"
          >
            Delete
          </button>
        </div>
      </div>

      <dl className="mb-6 grid grid-cols-[160px_1fr] gap-y-2 text-xs">
        <dt className="text-slate-500">Feedback ID</dt>
        <dd className="font-mono text-slate-700 break-all">{feedback.id}</dd>
        <dt className="text-slate-500">Source Q&A ID</dt>
        <dd className="font-mono text-slate-700 break-all">
          {feedback.sourceQaPairId}
          <button
            onClick={() => onOpenSource(feedback.sourceQaPairId)}
            className="ml-2 text-slate-900 underline hover:text-slate-600"
          >
            View source record →
          </button>
        </dd>
        {!isWhole && (
          <>
            <dt className="text-slate-500">Selection range</dt>
            <dd className="font-mono text-slate-700">
              chars {feedback.spanStart}–{feedback.spanEnd}
            </dd>
          </>
        )}
      </dl>

      <Section label="What's wrong">
        <div className="whitespace-pre-wrap rounded border border-slate-200 bg-white p-3 text-sm text-slate-900">
          {feedback.problem}
        </div>
      </Section>

      <Section label="Desired behavior">
        <div className="whitespace-pre-wrap rounded border border-slate-200 bg-white p-3 text-sm text-slate-900">
          {feedback.desiredBehavior}
        </div>
      </Section>

      <Section label="Highlighted excerpt">
        <div className="max-h-80 overflow-auto whitespace-pre-wrap rounded border border-slate-200 bg-amber-50 p-3 font-mono text-xs text-slate-800">
          {feedback.excerpt}
        </div>
      </Section>
    </div>
  );
}

function ConfirmDeleteDialog({
  onCancel,
  onConfirm,
  busy,
}: {
  onCancel: () => void;
  onConfirm: () => void;
  busy: boolean;
}) {
  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/40 p-4"
      onClick={onCancel}
    >
      <div
        className="w-full max-w-md rounded-lg bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-5 py-4">
          <h3 className="text-base font-semibold text-slate-900">Delete this feedback?</h3>
          <p className="mt-2 text-sm text-slate-600">This cannot be undone.</p>
        </div>
        <div className="flex items-center justify-end gap-2 border-t border-slate-200 px-5 py-3">
          <button
            onClick={onCancel}
            disabled={busy}
            className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={busy}
            className="rounded bg-rose-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-rose-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {busy ? "Deleting…" : "Delete"}
          </button>
        </div>
      </div>
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
