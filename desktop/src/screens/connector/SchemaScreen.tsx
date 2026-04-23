import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, discoverSchema, getFieldError } from "../../lib/api";
import { getSourceConnectorConfig, setSourceConnectorConfig } from "../../lib/store";
import FieldMappingForm from "../../components/FieldMappingForm";
import { StepIndicator } from "./DetailsScreen";
import type { DiscoveredColumn, FieldMapping } from "../../types";

type State =
  | { phase: "loading" }
  | { phase: "error"; message: string; detail?: string }
  | { phase: "missing-config" }
  | { phase: "ready"; columns: DiscoveredColumn[]; initial?: FieldMapping };

export default function SchemaScreen() {
  const navigate = useNavigate();
  const [state, setState] = useState<State>({ phase: "loading" });

  useEffect(() => {
    void (async () => {
      const config = await getSourceConnectorConfig();
      if (!config || !config.gcpProjectId || !config.tableId) {
        setState({ phase: "missing-config" });
        return;
      }
      try {
        const columns = await discoverSchema({
          gcpProjectId: config.gcpProjectId,
          datasetId: config.datasetId,
          tableId: config.tableId,
          credentialsPath: config.credentialsPath,
          rowFilter: config.rowFilter,
        });
        setState({
          phase: "ready",
          columns,
          initial: config.fieldMapping.questionColumn ? config.fieldMapping : undefined,
        });
      } catch (err) {
        // Structured field-level error (e.g. INVALID_ROW_FILTER) — send the user
        // back to Details with the error highlighted on the offending field.
        const fieldErr = getFieldError(err);
        if (fieldErr && fieldErr.field) {
          navigate("/connector/details", {
            replace: true,
            state: {
              fieldError: {
                field: fieldErr.field,
                error: fieldErr.error,
                detail: fieldErr.detail,
              },
            },
          });
          return;
        }

        const e = err as ApiError;
        const detail =
          typeof e.detail === "object" && e.detail && "detail" in e.detail
            ? String((e.detail as any).detail)
            : typeof e.detail === "string"
              ? e.detail
              : undefined;
        setState({
          phase: "error",
          message:
            e.status === 502
              ? "Could not connect to BigQuery"
              : e.status === 400
                ? "Invalid configuration"
                : "Schema discovery failed",
          detail,
        });
      }
    })();
  }, [navigate]);

  async function handleSubmit(mapping: FieldMapping) {
    const existing = await getSourceConnectorConfig();
    if (!existing) return;
    await setSourceConnectorConfig({ ...existing, fieldMapping: mapping });
    navigate("/connector/review");
  }

  return (
    <div className="mx-auto max-w-5xl p-8">
      <StepIndicator step={2} />
      <h1 className="text-2xl font-bold text-slate-900">Map Your Columns</h1>
      <p className="mt-1 mb-6 text-sm text-slate-600">
        Assign columns from your BigQuery table to AnswerGuard fields.
      </p>

      {state.phase === "loading" && (
        <div className="py-12 text-center text-sm text-slate-500">Discovering schema…</div>
      )}

      {state.phase === "missing-config" && (
        <div className="rounded border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
          Source details are missing. Go back and fill in the connection details first.
          <div className="mt-3">
            <button
              onClick={() => navigate("/connector/details")}
              className="rounded border border-amber-400 px-4 py-1.5 text-sm hover:bg-amber-100"
            >
              ← Back to Connection Details
            </button>
          </div>
        </div>
      )}

      {state.phase === "error" && (
        <div className="rounded border border-rose-300 bg-rose-50 p-4 text-sm text-rose-900">
          <div className="font-medium">{state.message}</div>
          {state.detail && <div className="mt-1 text-xs">{state.detail}</div>}
          <div className="mt-3">
            <button
              onClick={() => navigate("/connector/details")}
              className="rounded border border-rose-400 px-4 py-1.5 text-sm hover:bg-rose-100"
            >
              ← Back to Connection Details
            </button>
          </div>
        </div>
      )}

      {state.phase === "ready" && (
        <FieldMappingForm
          columns={state.columns}
          initial={state.initial}
          onSubmit={handleSubmit}
          onBack={() => navigate("/connector/details")}
        />
      )}
    </div>
  );
}
