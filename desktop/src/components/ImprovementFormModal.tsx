import { useEffect, useState } from "react";

interface Props {
  open: boolean;
  mode: "create" | "edit";
  excerpt: string;
  initialProblem?: string;
  initialDesiredBehavior?: string;
  onClose: () => void;
  onSave: (problem: string, desiredBehavior: string) => Promise<void>;
}

const MIN_LENGTH = 3;

export default function ImprovementFormModal({
  open,
  mode,
  excerpt,
  initialProblem = "",
  initialDesiredBehavior = "",
  onClose,
  onSave,
}: Props) {
  const [problem, setProblem] = useState(initialProblem);
  const [desiredBehavior, setDesiredBehavior] = useState(initialDesiredBehavior);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setProblem(initialProblem);
      setDesiredBehavior(initialDesiredBehavior);
      setError(null);
    }
  }, [open, initialProblem, initialDesiredBehavior]);

  if (!open) return null;

  const problemValid = problem.trim().length >= MIN_LENGTH;
  const desiredValid = desiredBehavior.trim().length >= MIN_LENGTH;
  const canSave = problemValid && desiredValid && !saving;

  const title = mode === "create" ? "Improve this response" : "Edit guideline";
  const saveLabel = mode === "create" ? "Save guideline" : "Save changes";

  const handleSave = async () => {
    if (!canSave) return;
    setSaving(true);
    setError(null);
    try {
      await onSave(problem.trim(), desiredBehavior.trim());
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(`Could not save: ${message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/40 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl rounded-lg bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="border-b border-slate-200 px-5 py-3">
          <h2 className="text-base font-semibold text-slate-900">{title}</h2>
        </div>

        <div className="space-y-4 px-5 py-4">
          {error && (
            <div className="rounded border border-rose-300 bg-rose-50 p-3 text-sm text-rose-900">
              {error}
            </div>
          )}

          <div>
            <div className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              Highlighted excerpt
            </div>
            <div className="max-h-32 overflow-auto whitespace-pre-wrap rounded border border-slate-200 bg-amber-50 p-2 font-mono text-xs text-slate-800">
              {excerpt}
            </div>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">
              What's wrong with this response?
            </label>
            <textarea
              value={problem}
              onChange={(e) => setProblem(e.target.value)}
              rows={3}
              placeholder="Describe the problem a PM would want fixed."
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-300"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-700">
              How should the agent behave instead?
            </label>
            <textarea
              value={desiredBehavior}
              onChange={(e) => setDesiredBehavior(e.target.value)}
              rows={3}
              placeholder="Describe the desired behavior."
              className="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-300"
            />
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 border-t border-slate-200 px-5 py-3">
          <button
            onClick={onClose}
            disabled={saving}
            className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!canSave}
            className="rounded bg-slate-900 px-3 py-1.5 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {saving ? "Saving…" : saveLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
