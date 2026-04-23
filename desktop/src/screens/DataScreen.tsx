import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useLocation } from "react-router-dom";
import { getImportStatus, getOverallStatus, listQAPairs } from "../lib/api";
import { getLastImportRunId, getSourceConnectorConfig } from "../lib/store";
import QAPairList from "../components/QAPairList";
import QAPairDetail from "../components/QAPairDetail";
import type { QAPairRecord } from "../types";

type Tab = "all" | "skipped";

export default function DataScreen() {
  const location = useLocation();
  const incomingQAPairId =
    (location.state as { openQAPairId?: string } | null)?.openQAPairId ?? null;

  const [tab, setTab] = useState<Tab>("all");
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(incomingQAPairId);
  const [sourceSystemId, setSourceSystemId] = useState<string | undefined>(undefined);
  const [lastImportRunId, setLastImportRunId] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      const cfg = await getSourceConnectorConfig();
      if (cfg?.sourceSystemId) setSourceSystemId(cfg.sourceSystemId);
      const runId = await getLastImportRunId();
      if (runId) setLastImportRunId(runId);
    })();
  }, []);

  // Debounce search input → search query (300ms)
  useEffect(() => {
    const id = setTimeout(() => {
      setSearch(searchInput.trim());
      setPage(1);
    }, 300);
    return () => clearTimeout(id);
  }, [searchInput]);

  // Keep the current page's items handy so the detail panel can read from them
  // without issuing a second request.
  const { data: currentPage } = useQuery({
    queryKey: ["qa-pairs", page, 50, sourceSystemId, search],
    queryFn: () => listQAPairs({ page, pageSize: 50, sourceSystemId, search }),
    enabled: tab === "all",
  });

  const selectedPair: QAPairRecord | null = useMemo(() => {
    if (!selectedId || !currentPage) return null;
    return currentPage.items.find((p) => p.id === selectedId) ?? null;
  }, [selectedId, currentPage]);

  const { data: overallStatus } = useQuery({
    queryKey: ["overall-status"],
    queryFn: getOverallStatus,
  });

  const source = overallStatus?.sources.find((s) => s.sourceSystemId === sourceSystemId);

  return (
    <div className="flex h-full flex-col">
      {/* Header / stats */}
      <div className="border-b border-slate-200 bg-slate-50 px-6 py-3">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-bold text-slate-900">Ingested Data</h1>
          <div className="flex items-center gap-4 text-xs text-slate-600">
            <span>
              <strong className="text-slate-900">
                {source?.totalRecords?.toLocaleString() ?? "—"}
              </strong>{" "}
              total records
            </span>
            <span>
              <strong className="text-slate-900">
                {source?.runtimeCapturesLast24h?.toLocaleString() ?? "—"}
              </strong>{" "}
              captured in last 24h
            </span>
            {source?.lastIngestedAt && (
              <span>Last ingested {new Date(source.lastIngestedAt).toLocaleString()}</span>
            )}
          </div>
        </div>

        <div className="mt-3 flex items-center gap-2">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search questions and answers…"
            className="flex-1 rounded border border-slate-300 bg-white px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-slate-300"
          />
          <div className="flex rounded border border-slate-300 bg-white text-xs overflow-hidden">
            <TabButton active={tab === "all"} onClick={() => setTab("all")}>
              All records
            </TabButton>
            <TabButton
              active={tab === "skipped"}
              onClick={() => setTab("skipped")}
              disabled={!lastImportRunId}
            >
              Skipped during last import
            </TabButton>
          </div>
        </div>
      </div>

      {/* Body */}
      {tab === "all" ? (
        <div className="grid grid-cols-[420px_1fr] flex-1 overflow-hidden">
          <div className="border-r border-slate-200 overflow-hidden">
            <QAPairList
              page={page}
              pageSize={50}
              sourceSystemId={sourceSystemId}
              search={search}
              selectedId={selectedId}
              onSelect={setSelectedId}
              onPageChange={(p) => {
                setPage(p);
                setSelectedId(null);
              }}
            />
          </div>
          <QAPairDetail pair={selectedPair} />
        </div>
      ) : (
        <SkippedRecordsView runId={lastImportRunId!} />
      )}
    </div>
  );
}

function TabButton({
  children,
  active,
  onClick,
  disabled,
}: {
  children: React.ReactNode;
  active: boolean;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`px-3 py-1.5 transition-colors ${
        active ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-50"
      } ${disabled ? "cursor-not-allowed opacity-40" : ""}`}
    >
      {children}
    </button>
  );
}

function SkippedRecordsView({ runId }: { runId: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["import-status", runId],
    queryFn: () => getImportStatus(runId),
  });

  if (isLoading) {
    return <div className="p-8 text-center text-sm text-slate-500">Loading skipped records…</div>;
  }
  if (error || !data) {
    return (
      <div className="m-6 rounded border border-rose-300 bg-rose-50 p-4 text-sm text-rose-900">
        Could not load skipped records from the last import.
      </div>
    );
  }
  if (data.errors.length === 0) {
    return (
      <div className="p-8 text-center text-sm text-slate-500">
        🎉 No records were skipped during the last import.
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto p-6">
      <div className="mb-3 text-xs text-slate-600">
        {data.errors.length.toLocaleString()} rows were skipped during the last import run.
      </div>
      <div className="rounded border border-slate-200 overflow-hidden">
        <table className="w-full text-xs">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-3 py-2 text-left font-semibold text-slate-600">Source row index</th>
              <th className="px-3 py-2 text-left font-semibold text-slate-600">Reason</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {data.errors.map((err, i) => (
              <tr key={i}>
                <td className="px-3 py-2 font-mono text-slate-700">{err.index}</td>
                <td className="px-3 py-2 text-slate-800">{err.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
