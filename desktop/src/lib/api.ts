import type {
  DiscoveredColumn,
  ImportJob,
  OverallStatus,
  QAPairsPage,
  SourceConnectorConfig,
} from "../types";
import { getServerConfig } from "./store";

export class ApiError extends Error {
  constructor(public status: number, message: string, public detail?: unknown) {
    super(message);
  }
}

async function getBaseUrl(): Promise<string> {
  const config = await getServerConfig();
  if (!config) throw new ApiError(0, "Server URL not configured");
  return config.url.replace(/\/$/, "");
}

async function request<T>(path: string, init?: RequestInit, baseUrlOverride?: string): Promise<T> {
  const base = baseUrlOverride ?? (await getBaseUrl());
  const response = await fetch(`${base}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    let detail: unknown;
    try {
      detail = await response.json();
    } catch {
      detail = await response.text();
    }
    throw new ApiError(response.status, `${response.status} ${response.statusText}`, detail);
  }
  return response.json() as Promise<T>;
}

export async function checkHealth(url: string): Promise<boolean> {
  const base = url.replace(/\/$/, "");
  try {
    const res = await fetch(`${base}/health`);
    if (!res.ok) return false;
    const body = (await res.json()) as { status?: string };
    return body.status === "ok";
  } catch {
    return false;
  }
}

export interface DiscoverSchemaRequest {
  gcpProjectId: string;
  datasetId: string;
  tableId: string;
  credentialsPath?: string;
  rowFilter?: string;
}

export async function discoverSchema(req: DiscoverSchemaRequest): Promise<DiscoveredColumn[]> {
  const body = await request<{ columns: DiscoveredColumn[] }>("/v1/sources/discover-schema", {
    method: "POST",
    body: JSON.stringify({
      gcp_project_id: req.gcpProjectId,
      dataset_id: req.datasetId,
      table_id: req.tableId,
      credentials_path: req.credentialsPath,
      row_filter: req.rowFilter,
    }),
  });
  return body.columns;
}

/** Extract a structured { error, field, detail } payload from an ApiError, if present. */
export function getFieldError(
  err: unknown,
): { error: string; field?: string; detail: string } | null {
  if (!(err instanceof ApiError)) return null;
  const d = err.detail;
  if (d && typeof d === "object" && "detail" in d && typeof (d as any).detail === "object") {
    const inner = (d as any).detail;
    if (inner && typeof inner === "object" && "error" in inner) {
      return {
        error: String(inner.error),
        field: inner.field ? String(inner.field) : undefined,
        detail: String(inner.detail ?? ""),
      };
    }
  }
  if (d && typeof d === "object" && "error" in d) {
    return {
      error: String((d as any).error),
      field: (d as any).field ? String((d as any).field) : undefined,
      detail: String((d as any).detail ?? ""),
    };
  }
  return null;
}

export async function triggerImport(config: SourceConnectorConfig): Promise<{ ingestionRunId: string; status: string; message: string }> {
  const body = await request<{ ingestion_run_id: string; status: string; message: string }>(
    "/v1/ingest/import",
    {
      method: "POST",
      body: JSON.stringify({
        source_system_id: config.sourceSystemId,
        gcp_project_id: config.gcpProjectId,
        dataset_id: config.datasetId,
        table_id: config.tableId,
        credentials_path: config.credentialsPath,
        field_mapping: {
          question_column: config.fieldMapping.questionColumn,
          answer_column: config.fieldMapping.answerColumn,
          timestamp_column: config.fieldMapping.timestampColumn,
          external_id_column: config.fieldMapping.externalIdColumn,
          metadata_columns: config.fieldMapping.metadataColumns,
        },
        row_filter: config.rowFilter,
        page_size: config.pageSize,
      }),
    },
  );
  return {
    ingestionRunId: body.ingestion_run_id,
    status: body.status,
    message: body.message,
  };
}

export async function getImportStatus(runId: string): Promise<ImportJob> {
  const body = await request<any>(`/v1/ingest/status/${runId}`);
  return {
    runId: body.ingestion_run_id,
    status: body.status,
    recordsProcessed: body.records_processed,
    recordsSkipped: body.records_skipped,
    lastCheckpoint: body.last_checkpoint,
    startedAt: body.started_at,
    completedAt: body.completed_at,
    errors: body.errors ?? [],
  };
}

export async function getOverallStatus(): Promise<OverallStatus> {
  const body = await request<any>("/v1/ingest/status");
  return {
    totalQaPairs: body.total_qa_pairs,
    sources: (body.sources ?? []).map((s: any) => ({
      sourceSystemId: s.source_system_id,
      totalRecords: s.total_records,
      lastIngestedAt: s.last_ingested_at,
      runtimeCapturesLast24h: s.runtime_captures_last_24h,
      lastImportRun: s.last_import_run
        ? {
            runId: s.last_import_run.run_id,
            status: s.last_import_run.status,
            recordsProcessed: s.last_import_run.records_processed,
            recordsSkipped: s.last_import_run.records_skipped,
            startedAt: s.last_import_run.started_at,
            completedAt: s.last_import_run.completed_at,
          }
        : null,
    })),
  };
}

export interface ListQAPairsParams {
  page?: number;
  pageSize?: number;
  sourceSystemId?: string;
  search?: string;
}

export async function listQAPairs(params: ListQAPairsParams = {}): Promise<QAPairsPage> {
  const query = new URLSearchParams();
  if (params.page) query.set("page", String(params.page));
  if (params.pageSize) query.set("page_size", String(params.pageSize));
  if (params.sourceSystemId) query.set("source_system_id", params.sourceSystemId);
  if (params.search) query.set("search", params.search);

  const body = await request<any>(`/v1/qa-pairs?${query.toString()}`);
  return {
    total: body.total,
    page: body.page,
    pageSize: body.page_size,
    items: (body.items ?? []).map((p: any) => ({
      id: p.id,
      questionText: p.question_text,
      answerText: p.answer_text,
      sourceSystemId: p.source_system_id,
      capturedAt: p.captured_at,
      sourceTimestamp: p.source_timestamp,
      ingestionMethod: p.ingestion_method,
      externalId: p.external_id,
      metadata: p.metadata ?? {},
    })),
  };
}
