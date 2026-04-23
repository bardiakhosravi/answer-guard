import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getSourceConnectorConfig } from "../../lib/store";
import { StepIndicator } from "./DetailsScreen";
import type { SourceConnectorConfig } from "../../types";

export default function ReviewScreen() {
  const [config, setConfig] = useState<SourceConnectorConfig | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    void (async () => {
      const c = await getSourceConnectorConfig();
      if (!c || !c.fieldMapping.questionColumn) {
        navigate("/connector/details");
        return;
      }
      setConfig(c);
    })();
  }, [navigate]);

  if (!config) return null;

  return (
    <div className="mx-auto max-w-3xl p-8">
      <StepIndicator step={3} />
      <h1 className="text-2xl font-bold text-slate-900">Review Configuration</h1>
      <p className="mt-1 mb-6 text-sm text-slate-600">
        Confirm everything looks correct, then save to proceed to the import.
      </p>

      <Section
        title="Connection"
        onEdit={() => navigate("/connector/details")}
        items={[
          ["Source System ID", config.sourceSystemId],
          ["GCP Project ID", config.gcpProjectId],
          ["Dataset ID", config.datasetId],
          ["Table ID", config.tableId],
          ["Credentials", config.credentialsPath ?? "Application Default Credentials"],
        ]}
      />

      <Section
        title="Field Mapping"
        onEdit={() => navigate("/connector/schema")}
        items={[
          ["Question column", config.fieldMapping.questionColumn],
          ["Answer column", config.fieldMapping.answerColumn],
          ["Timestamp column", config.fieldMapping.timestampColumn ?? "—"],
          ["External ID column", config.fieldMapping.externalIdColumn ?? "—"],
          [
            "Metadata columns",
            Object.keys(config.fieldMapping.metadataColumns).length > 0
              ? Object.entries(config.fieldMapping.metadataColumns)
                  .map(([k, v]) => `${k} ← ${v}`)
                  .join(", ")
              : "—",
          ],
        ]}
      />

      <div className="mt-8 flex justify-between">
        <button
          onClick={() => navigate("/connector/schema")}
          className="rounded border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50"
        >
          ← Edit Mapping
        </button>
        <button
          onClick={() => navigate("/import")}
          className="rounded bg-slate-900 px-6 py-2 text-sm font-medium text-white hover:bg-slate-800"
        >
          Save Configuration →
        </button>
      </div>
    </div>
  );
}

function Section({
  title,
  items,
  onEdit,
}: {
  title: string;
  items: [string, string][];
  onEdit: () => void;
}) {
  return (
    <div className="mb-6 rounded border border-slate-200">
      <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-4 py-2">
        <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
        <button onClick={onEdit} className="text-xs text-slate-600 hover:underline">
          Edit
        </button>
      </div>
      <dl className="divide-y divide-slate-100">
        {items.map(([label, value]) => (
          <div key={label} className="grid grid-cols-[200px_1fr] gap-4 px-4 py-2 text-sm">
            <dt className="text-slate-500">{label}</dt>
            <dd className="font-mono text-slate-800 break-all">{value || "—"}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
