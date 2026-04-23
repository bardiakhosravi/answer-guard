import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { open } from "@tauri-apps/plugin-dialog";
import { getSourceConnectorConfig, setSourceConnectorConfig } from "../../lib/store";
import type { SourceConnectorConfig } from "../../types";

interface FormValues {
  sourceSystemId: string;
  gcpProjectId: string;
  datasetId: string;
  tableId: string;
  credentialsPath: string;
}

export default function DetailsScreen() {
  const navigate = useNavigate();
  const { register, handleSubmit, watch, setValue, reset, formState: { isValid } } = useForm<FormValues>({
    mode: "all",
    defaultValues: {
      sourceSystemId: "",
      gcpProjectId: "",
      datasetId: "",
      tableId: "",
      credentialsPath: "",
    },
  });

  useEffect(() => {
    void (async () => {
      const existing = await getSourceConnectorConfig();
      if (existing) {
        // `reset` re-runs validation against the loaded values immediately.
        reset({
          sourceSystemId: existing.sourceSystemId,
          gcpProjectId: existing.gcpProjectId,
          datasetId: existing.datasetId,
          tableId: existing.tableId,
          credentialsPath: existing.credentialsPath ?? "",
        });
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reset]);

  async function browseCredentials() {
    const selected = await open({
      multiple: false,
      filters: [{ name: "JSON", extensions: ["json"] }],
    });
    if (typeof selected === "string") {
      setValue("credentialsPath", selected, { shouldValidate: true });
    }
  }

  async function onSubmit(values: FormValues) {
    const existing = await getSourceConnectorConfig();
    const config: SourceConnectorConfig = {
      sourceSystemId: values.sourceSystemId.trim(),
      gcpProjectId: values.gcpProjectId.trim(),
      datasetId: values.datasetId.trim(),
      tableId: values.tableId.trim(),
      credentialsPath: values.credentialsPath.trim() || undefined,
      // Row filter and page size are NOT asked here — the row filter is set on
      // the Import screen where users can iterate on it. Page size keeps its
      // default (5000) which is right for essentially every case.
      rowFilter: existing?.rowFilter,
      pageSize: existing?.pageSize ?? 5000,
      fieldMapping: existing?.fieldMapping ?? {
        questionColumn: "",
        answerColumn: "",
        metadataColumns: {},
      },
    };
    await setSourceConnectorConfig(config);
    navigate("/connector/schema");
  }

  return (
    <div className="mx-auto max-w-3xl p-8">
      <StepIndicator step={1} />
      <h1 className="text-2xl font-bold text-slate-900">Configure Source</h1>
      <p className="mt-1 mb-4 text-sm text-slate-600">
        Tell AnswerGuard where to find your Q&amp;A history in BigQuery.
      </p>

      <InfoCallout>
        <strong>Before you start:</strong> You'll need a BigQuery table containing Q&amp;A data and a service
        account (or local ADC) with <code className="rounded bg-slate-200 px-1 font-mono text-xs">BigQuery Data Viewer</code> access.
        If you don't have a service account yet,{" "}
        <a
          href="https://console.cloud.google.com/iam-admin/serviceaccounts"
          className="text-sky-700 underline"
          target="_blank"
          rel="noreferrer"
        >
          create one in the GCP Console
        </a>{" "}
        and download its JSON key.
      </InfoCallout>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-5">
        <Field
          label="Source System ID"
          required
          help={
            <>
              <p>
                A <strong>name you choose</strong> to identify this data source inside AnswerGuard. This is
                not a GCP value — it's a label for your own reference.
              </p>
              <p className="mt-1.5">
                Pick something descriptive so you can tell sources apart later if you add more
                (e.g.&nbsp;if you have multiple agent systems).
              </p>
              <Examples items={["prod-agent-v2", "support-chatbot", "staging-agent"]} />
            </>
          }
        >
          <input
            type="text"
            placeholder="e.g. prod-agent-v2"
            {...register("sourceSystemId", { required: true, minLength: 1 })}
            className="field-input"
          />
        </Field>

        <Field
          label="GCP Project ID"
          required
          help={
            <>
              <p>
                The ID of the Google Cloud project that contains your BigQuery dataset. This is the
                <strong> project ID</strong> (not the display name) — they're often different.
              </p>
              <p className="mt-1.5">
                <strong>Where to find it:</strong> open the{" "}
                <a
                  href="https://console.cloud.google.com/"
                  className="text-sky-700 underline"
                  target="_blank"
                  rel="noreferrer"
                >
                  GCP Console
                </a>
                , click the project selector at the top; the project ID appears under the display name.
              </p>
              <Examples items={["my-company-prod", "acme-analytics-1234"]} />
            </>
          }
        >
          <input
            type="text"
            placeholder="my-gcp-project"
            {...register("gcpProjectId", { required: true })}
            className="field-input"
          />
        </Field>

        <Field
          label="Dataset ID"
          required
          help={
            <>
              <p>
                The BigQuery dataset containing your Q&amp;A table. A dataset is a collection of tables —
                think of it like a schema or folder.
              </p>
              <p className="mt-1.5">
                <strong>Where to find it:</strong> in the{" "}
                <a
                  href="https://console.cloud.google.com/bigquery"
                  className="text-sky-700 underline"
                  target="_blank"
                  rel="noreferrer"
                >
                  BigQuery Console
                </a>
                , expand your project in the left panel — datasets are listed directly under it.
              </p>
              <Examples items={["agent_logs", "customer_support", "chat_history"]} />
            </>
          }
        >
          <input
            type="text"
            placeholder="agent_logs"
            {...register("datasetId", { required: true })}
            className="field-input"
          />
        </Field>

        <Field
          label="Table ID"
          required
          help={
            <>
              <p>
                The specific BigQuery table (or view) with your Q&amp;A rows. Each row should represent one
                interaction — a question from a user and the agent's response.
              </p>
              <p className="mt-1.5">
                <strong>Where to find it:</strong> expand the dataset in the BigQuery Console — tables are
                listed underneath. You can click one to preview its schema.
              </p>
              <Examples items={["qa_responses", "conversations", "support_tickets"]} />
            </>
          }
        >
          <input
            type="text"
            placeholder="qa_responses"
            {...register("tableId", { required: true })}
            className="field-input"
          />
        </Field>

        <Field
          label="Credentials File"
          help={
            <>
              <p>
                A service account JSON key file that grants AnswerGuard access to your BigQuery table.
                The service account must have the{" "}
                <code className="rounded bg-slate-200 px-1 font-mono text-xs">BigQuery Data Viewer</code> role.
              </p>
              <p className="mt-1.5">
                <strong>How to get one:</strong>{" "}
                <a
                  href="https://console.cloud.google.com/iam-admin/serviceaccounts"
                  className="text-sky-700 underline"
                  target="_blank"
                  rel="noreferrer"
                >
                  open IAM &amp; Admin → Service Accounts
                </a>
                , create or select a service account, go to <em>Keys</em>, click <em>Add Key → Create new key</em>,
                choose JSON, and save the file.
              </p>
              <p className="mt-1.5 rounded bg-sky-50 px-3 py-2 text-xs text-sky-900">
                <strong>Skip this field</strong> if you've run{" "}
                <code className="rounded bg-sky-100 px-1 font-mono">gcloud auth application-default login</code>{" "}
                on this machine — AnswerGuard will use those credentials automatically.
              </p>
            </>
          }
        >
          <div className="flex gap-2">
            <input
              type="text"
              readOnly
              value={watch("credentialsPath")}
              placeholder="(not selected — using Application Default Credentials)"
              className="field-input flex-1"
            />
            <button
              type="button"
              onClick={browseCredentials}
              className="rounded border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50"
            >
              Browse…
            </button>
          </div>
        </Field>

        <div className="flex justify-end pt-4">
          <button
            type="submit"
            disabled={!isValid}
            className="rounded bg-slate-900 px-6 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50 hover:bg-slate-800"
          >
            Discover Schema →
          </button>
        </div>
      </form>

      <style>{`.field-input { width: 100%; border: 1px solid rgb(203 213 225); border-radius: 0.375rem; padding: 0.5rem 0.75rem; font-size: 0.875rem; background: white; }
      .field-input:focus { outline: none; border-color: rgb(15 23 42); box-shadow: 0 0 0 3px rgba(15, 23, 42, 0.08); }
      .field-input::placeholder { color: rgb(148 163 184); }`}</style>
    </div>
  );
}

function Field({
  label,
  required,
  help,
  children,
}: {
  label: string;
  required?: boolean;
  help?: React.ReactNode;
  children: React.ReactNode;
}) {
  const [helpOpen, setHelpOpen] = useState(false);
  return (
    <div>
      <div className="mb-1.5 flex items-center gap-2">
        <label className="text-sm font-medium text-slate-800">
          {label}
          {required && <span className="ml-0.5 text-rose-600">*</span>}
        </label>
        {help && (
          <button
            type="button"
            onClick={() => setHelpOpen((v) => !v)}
            className="inline-flex h-4 w-4 items-center justify-center rounded-full border border-slate-300 text-[10px] text-slate-500 hover:bg-slate-100 hover:text-slate-700"
            aria-label="Help"
            title="Show help"
          >
            ?
          </button>
        )}
      </div>
      {children}
      {help && helpOpen && (
        <div className="mt-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-2.5 text-xs leading-relaxed text-slate-700">
          {help}
        </div>
      )}
    </div>
  );
}

function Examples({ items }: { items: string[] }) {
  return (
    <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
      <span className="text-[10px] uppercase tracking-wider text-slate-500">Examples:</span>
      {items.map((item) => (
        <code key={item} className="rounded bg-slate-200 px-1.5 py-0.5 font-mono text-[11px] text-slate-700">
          {item}
        </code>
      ))}
    </div>
  );
}

function InfoCallout({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-md border border-sky-200 bg-sky-50 px-4 py-3 text-sm leading-relaxed text-sky-900">
      {children}
    </div>
  );
}

export function StepIndicator({ step }: { step: 1 | 2 | 3 }) {
  const steps = ["Connection Details", "Field Mapping", "Review"];
  return (
    <div className="mb-4 flex items-center gap-2 text-xs text-slate-500">
      {steps.map((label, i) => (
        <span key={label} className="flex items-center">
          <span
            className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-semibold ${
              i + 1 === step
                ? "bg-slate-900 text-white"
                : i + 1 < step
                  ? "bg-emerald-600 text-white"
                  : "bg-slate-200 text-slate-500"
            }`}
          >
            {i + 1}
          </span>
          <span className={`ml-1.5 ${i + 1 === step ? "text-slate-900 font-medium" : ""}`}>{label}</span>
          {i < 2 && <span className="mx-3 text-slate-300">→</span>}
        </span>
      ))}
    </div>
  );
}
