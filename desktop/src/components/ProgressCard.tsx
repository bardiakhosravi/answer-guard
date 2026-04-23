import { useEffect, useState } from "react";
import type { ImportJob, ImportStatus } from "../types";

const statusColours: Record<ImportStatus, string> = {
  RUNNING: "bg-sky-100 text-sky-800",
  RESUMED: "bg-indigo-100 text-indigo-800",
  COMPLETED: "bg-emerald-100 text-emerald-800",
  FAILED: "bg-rose-100 text-rose-800",
};

export default function ProgressCard({ job }: { job: ImportJob }) {
  const [elapsed, setElapsed] = useState("");

  useEffect(() => {
    function tick() {
      const start = new Date(job.startedAt).getTime();
      const end = job.completedAt ? new Date(job.completedAt).getTime() : Date.now();
      const seconds = Math.max(0, Math.floor((end - start) / 1000));
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      setElapsed(`${mins}m ${secs.toString().padStart(2, "0")}s`);
    }
    tick();
    if (job.status === "RUNNING" || job.status === "RESUMED") {
      const id = setInterval(tick, 1000);
      return () => clearInterval(id);
    }
  }, [job.startedAt, job.completedAt, job.status]);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6">
      <div className="mb-4 flex items-center justify-between">
        <span
          className={`inline-block rounded-full px-3 py-0.5 text-xs font-semibold uppercase tracking-wide ${statusColours[job.status]}`}
        >
          {job.status}
        </span>
        <span className="text-xs text-slate-500">Run ID: {job.runId.slice(0, 8)}…</span>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <Stat label="Processed" value={job.recordsProcessed.toLocaleString()} accent="emerald" />
        <Stat label="Skipped" value={job.recordsSkipped.toLocaleString()} accent="amber" />
        <Stat label="Elapsed" value={elapsed} accent="slate" />
      </div>

      {job.lastCheckpoint != null && (
        <div className="mt-4 text-xs text-slate-500">
          Last checkpoint: <span className="font-mono text-slate-700">{job.lastCheckpoint.toLocaleString()}</span>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent: "emerald" | "amber" | "slate" }) {
  const colour = {
    emerald: "text-emerald-700",
    amber: "text-amber-700",
    slate: "text-slate-800",
  }[accent];
  return (
    <div>
      <div className="text-xs uppercase tracking-wider text-slate-500">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${colour}`}>{value}</div>
    </div>
  );
}
