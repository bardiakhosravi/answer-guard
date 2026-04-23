import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, getFieldError, getImportStatus, triggerImport } from "../lib/api";
import {
  getLastImportRunId,
  getSourceConnectorConfig,
  setLastImportRunId,
  setSourceConnectorConfig,
} from "../lib/store";
import ProgressCard from "../components/ProgressCard";
import type { SourceConnectorConfig } from "../types";

export default function ImportScreen() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [config, setConfig] = useState<SourceConnectorConfig | null>(null);
  const [runId, setRunId] = useState<string | null>(null);
  const [triggerError, setTriggerError] = useState<string | null>(null);
  const [rowFilter, setRowFilter] = useState("");
  const [rowFilterError, setRowFilterError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    void (async () => {
      const c = await getSourceConnectorConfig();
      if (!c || !c.fieldMapping.questionColumn) {
        navigate("/connector/details", { replace: true });
        return;
      }
      setConfig(c);
      setRowFilter(c.rowFilter ?? "");
      const last = await getLastImportRunId();
      if (last) setRunId(last);
    })();
  }, [navigate]);

  const { data: job } = useQuery({
    queryKey: ["import-status", runId],
    queryFn: () => getImportStatus(runId!),
    enabled: !!runId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "RUNNING" || status === "RESUMED" ? 3000 : false;
    },
  });

  async function startImport() {
    if (!config) return;
    setTriggerError(null);
    setRowFilterError(null);
    setStarting(true);

    const trimmedFilter = rowFilter.trim();
    const updatedConfig: SourceConnectorConfig = {
      ...config,
      rowFilter: trimmedFilter || undefined,
    };
    // Persist the filter so resuming after app restart uses the same value.
    await setSourceConnectorConfig(updatedConfig);
    setConfig(updatedConfig);

    try {
      const result = await triggerImport(updatedConfig);
      await setLastImportRunId(result.ingestionRunId);
      setRunId(result.ingestionRunId);
      queryClient.invalidateQueries({ queryKey: ["import-status", result.ingestionRunId] });
    } catch (err) {
      const fieldErr = getFieldError(err);
      if (fieldErr?.field === "row_filter") {
        setRowFilterError(fieldErr.detail || fieldErr.error);
        return;
      }
      const e = err as ApiError;
      const msg =
        typeof e.detail === "object" && e.detail && "detail" in e.detail
          ? String((e.detail as any).detail)
          : typeof e.detail === "string"
            ? e.detail
            : e.message;
      setTriggerError(msg || "Failed to start import");
    } finally {
      setStarting(false);
    }
  }

  if (!config) return null;

  // State A — no active or recent run
  if (!runId) {
    return (
      <Layout>
        <h1 className="text-2xl font-bold text-slate-900">Historical Import</h1>
        <p className="mt-1 mb-6 text-sm text-slate-600">
          Import your Q&amp;A history from BigQuery. This is a one-time operation.
        </p>

        <SummaryCard config={config} />

        <div className="mt-6 rounded-md border border-slate-200 p-4">
          <div className="mb-1 flex items-center gap-2">
            <label className="text-sm font-semibold text-slate-800">
              Row Filter <span className="font-normal text-slate-500">(optional)</span>
            </label>
          </div>
          <p className="mb-2 text-xs text-slate-600">
            A BigQuery <code className="rounded bg-slate-100 px-1 font-mono">WHERE</code> clause to limit which rows are imported.
            Leave blank to import everything. You can change this between imports — already-imported rows are deduplicated automatically.
          </p>
          <input
            type="text"
            value={rowFilter}
            onChange={(e) => {
              setRowFilter(e.target.value);
              if (rowFilterError) setRowFilterError(null);
            }}
            placeholder="e.g. handled_by = 'ai_agent' AND handled_at > '2024-01-01'"
            className={`w-full rounded border px-3 py-2 font-mono text-xs ${
              rowFilterError ? "border-rose-400 bg-rose-50" : "border-slate-300"
            } focus:outline-none focus:ring-2 focus:ring-slate-300`}
          />
          {rowFilterError && (
            <div className="mt-2 rounded border border-rose-300 bg-rose-50 px-3 py-2 text-xs text-rose-900">
              <div className="font-semibold">BigQuery rejected this filter</div>
              <div className="mt-0.5 font-mono break-all">{rowFilterError}</div>
            </div>
          )}
          <div className="mt-2 flex flex-wrap gap-1.5 text-[11px]">
            <span className="text-slate-500">Examples:</span>
            {[
              "handled_by = 'ai_agent'",
              "handled_at > '2024-01-01'",
              "resolution_status = 'resolved'",
            ].map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => {
                  setRowFilter(ex);
                  setRowFilterError(null);
                }}
                className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-slate-700 hover:bg-slate-200"
              >
                {ex}
              </button>
            ))}
          </div>
        </div>

        {triggerError && (
          <div className="mt-4 rounded-md border border-rose-300 bg-rose-50 p-4 text-sm text-rose-900">
            <div className="font-semibold">Could not start import</div>
            <div className="mt-0.5 font-mono text-xs break-all">{triggerError}</div>
          </div>
        )}
        <div className="mt-6 flex justify-end">
          <button
            onClick={startImport}
            disabled={starting}
            className="rounded bg-slate-900 px-6 py-2 text-sm font-medium text-white disabled:opacity-50 hover:bg-slate-800"
          >
            {starting ? "Starting…" : "Start Import"}
          </button>
        </div>
      </Layout>
    );
  }

  // State B — loading the first status poll
  if (!job) {
    return (
      <Layout>
        <h1 className="text-2xl font-bold text-slate-900">Import</h1>
        <div className="mt-6 py-8 text-center text-sm text-slate-500">Loading status…</div>
      </Layout>
    );
  }

  // State C — COMPLETED
  if (job.status === "COMPLETED") {
    return (
      <Layout>
        <h1 className="text-2xl font-bold text-slate-900">Import Complete ✅</h1>
        <p className="mt-1 mb-6 text-sm text-slate-600">Your Q&amp;A history is now in AnswerGuard.</p>
        <ProgressCard job={job} />
        <div className="mt-6 flex justify-between">
          <button
            onClick={async () => {
              await setLastImportRunId("");
              setRunId(null);
            }}
            className="rounded border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50"
          >
            Run Another Import
          </button>
          <button
            onClick={() => navigate("/data")}
            className="rounded bg-slate-900 px-6 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            View Ingested Data →
          </button>
        </div>
      </Layout>
    );
  }

  // State D — FAILED
  if (job.status === "FAILED") {
    const lastError = job.errors[job.errors.length - 1]?.reason ?? "Unknown error";
    return (
      <Layout>
        <h1 className="text-2xl font-bold text-slate-900">Import Failed ❌</h1>
        <p className="mt-1 mb-6 text-sm text-slate-600">
          The import could not complete. Review the error below and correct your source configuration.
        </p>

        <div className="rounded-md border border-rose-300 bg-rose-50 p-4 text-sm text-rose-900">
          <div className="mb-1 font-semibold">Error</div>
          <div className="font-mono text-xs break-all">{lastError}</div>
        </div>

        <div className="mt-4">
          <ProgressCard job={job} />
        </div>

        <div className="mt-6 flex justify-between">
          <button
            onClick={() => navigate("/connector/details")}
            className="rounded border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50"
          >
            ← Fix Source Configuration
          </button>
          <button
            onClick={startImport}
            disabled={starting}
            className="rounded bg-slate-900 px-6 py-2 text-sm font-medium text-white disabled:opacity-50 hover:bg-slate-800"
          >
            {starting ? "Resuming…" : "Resume Import"}
          </button>
        </div>
      </Layout>
    );
  }

  // State B — RUNNING or RESUMED
  return (
    <Layout>
      <h1 className="text-2xl font-bold text-slate-900">Import Running</h1>
      <p className="mt-1 mb-6 text-sm text-slate-600">
        Progress updates every few seconds. You can leave this screen — the import continues on the server.
      </p>
      <ProgressCard job={job} />
    </Layout>
  );
}

function Layout({ children }: { children: React.ReactNode }) {
  return <div className="mx-auto max-w-3xl p-8">{children}</div>;
}

function SummaryCard({ config }: { config: SourceConnectorConfig }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm">
      <div className="mb-2 font-semibold text-slate-800">Source</div>
      <dl className="grid grid-cols-[140px_1fr] gap-y-1 text-slate-700">
        <dt className="text-slate-500">Source System ID</dt>
        <dd className="font-mono">{config.sourceSystemId}</dd>
        <dt className="text-slate-500">Table</dt>
        <dd className="font-mono">
          {config.gcpProjectId}.{config.datasetId}.{config.tableId}
        </dd>
        {config.rowFilter && (
          <>
            <dt className="text-slate-500">Row filter</dt>
            <dd className="font-mono text-xs">{config.rowFilter}</dd>
          </>
        )}
      </dl>
    </div>
  );
}
