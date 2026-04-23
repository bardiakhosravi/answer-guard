import { useCallback, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { submitResponseFeedback } from "../lib/api";
import type { QAPairRecord } from "../types";
import ImprovementFormModal from "./ImprovementFormModal";

interface Props {
  pair: QAPairRecord | null;
}

interface SelectionState {
  start: number;
  end: number;
  excerpt: string;
}

type ModalState =
  | { open: false }
  | { open: true; excerpt: string; spanStart: number | null; spanEnd: number | null };

export default function QAPairDetail({ pair }: Props) {
  const [selection, setSelection] = useState<SelectionState | null>(null);
  const [modalState, setModalState] = useState<ModalState>({ open: false });
  const [toast, setToast] = useState<string | null>(null);
  const answerRef = useRef<HTMLDivElement>(null);

  const mutation = useMutation({
    mutationFn: submitResponseFeedback,
  });

  const handleMouseUp = useCallback(() => {
    if (!pair || !answerRef.current) return;
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || sel.rangeCount === 0) {
      setSelection(null);
      return;
    }
    const range = sel.getRangeAt(0);
    const root = answerRef.current;
    if (!root.contains(range.startContainer) || !root.contains(range.endContainer)) {
      setSelection(null);
      return;
    }
    const start = offsetFromRoot(root, range.startContainer, range.startOffset);
    const end = offsetFromRoot(root, range.endContainer, range.endOffset);
    if (start === null || end === null) return;
    const from = Math.min(start, end);
    const to = Math.max(start, end);
    if (to <= from) return;
    setSelection({ start: from, end: to, excerpt: pair.answerText.slice(from, to) });
  }, [pair]);

  const openModalFromSelection = () => {
    if (!selection) return;
    setModalState({
      open: true,
      excerpt: selection.excerpt,
      spanStart: selection.start,
      spanEnd: selection.end,
    });
  };

  const openModalWhole = () => {
    if (!pair) return;
    setModalState({
      open: true,
      excerpt: pair.answerText,
      spanStart: null,
      spanEnd: null,
    });
  };

  const closeModal = () => setModalState({ open: false });

  const handleSave = async (problem: string, desiredBehavior: string) => {
    if (!pair || !modalState.open) return;
    await mutation.mutateAsync({
      sourceQaPairId: pair.id,
      excerpt: modalState.excerpt,
      problem,
      desiredBehavior,
      spanStart: modalState.spanStart,
      spanEnd: modalState.spanEnd,
    });
    closeModal();
    setSelection(null);
    window.getSelection()?.removeAllRanges();
    setToast("Feedback saved.");
    setTimeout(() => setToast(null), 3000);
  };

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
    <div className="relative h-full overflow-auto p-6">
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
        <div
          ref={answerRef}
          onMouseUp={handleMouseUp}
          className="whitespace-pre-wrap rounded border border-slate-200 bg-white p-3 text-sm text-slate-900 select-text"
        >
          {pair.answerText}
        </div>
        <div className="mt-2 flex items-center gap-2">
          <button
            onClick={openModalFromSelection}
            disabled={!selection}
            className="rounded bg-amber-500 px-3 py-1 text-xs font-semibold text-white hover:bg-amber-600 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Improve selected
          </button>
          <button
            onClick={openModalWhole}
            className="rounded border border-slate-300 bg-white px-3 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            Improve whole response
          </button>
          {selection && (
            <span className="text-xs text-slate-500">
              {selection.end - selection.start} characters selected
            </span>
          )}
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

      <ImprovementFormModal
        open={modalState.open}
        mode="create"
        excerpt={modalState.open ? modalState.excerpt : ""}
        onClose={closeModal}
        onSave={handleSave}
      />

      {toast && (
        <div className="fixed bottom-6 right-6 z-50 rounded bg-slate-900 px-4 py-2 text-sm text-white shadow-lg">
          {toast}
        </div>
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

function offsetFromRoot(root: HTMLElement, node: Node, nodeOffset: number): number | null {
  let offset = 0;
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let current: Node | null = walker.nextNode();
  while (current) {
    if (current === node) return offset + nodeOffset;
    offset += current.textContent?.length ?? 0;
    current = walker.nextNode();
  }
  if (node.nodeType === Node.ELEMENT_NODE && root.contains(node)) return offset;
  return null;
}
