// Type definitions for AnswerGuard desktop app.
// Mirrors specs/003-desktop-integration-setup/data-model.md.

export interface ServerConfig {
  url: string;
  lastVerifiedAt?: string;
}

export interface FieldMapping {
  questionColumn: string;
  answerColumn: string;
  timestampColumn?: string;
  externalIdColumn?: string;
  metadataColumns: Record<string, string>;
}

export interface SourceConnectorConfig {
  sourceSystemId: string;
  gcpProjectId: string;
  datasetId: string;
  tableId: string;
  credentialsPath?: string;
  rowFilter?: string;
  pageSize: number;
  fieldMapping: FieldMapping;
}

export interface DiscoveredColumn {
  name: string;
  type: string;
}

export type ImportStatus = "RUNNING" | "COMPLETED" | "FAILED" | "RESUMED";

export interface ImportJob {
  runId: string;
  status: ImportStatus;
  recordsProcessed: number;
  recordsSkipped: number;
  lastCheckpoint: number | null;
  startedAt: string;
  completedAt: string | null;
  errors: { index: number; reason: string }[];
}

export type IngestionMethod = "HISTORICAL_IMPORT" | "RUNTIME_CAPTURE";

export interface QAPairRecord {
  id: string;
  questionText: string;
  answerText: string;
  sourceSystemId: string;
  capturedAt: string;
  sourceTimestamp: string | null;
  ingestionMethod: IngestionMethod;
  externalId: string | null;
  metadata: Record<string, string>;
}

export interface QAPairsPage {
  total: number;
  page: number;
  pageSize: number;
  items: QAPairRecord[];
}

export interface OverallStatus {
  totalQaPairs: number;
  sources: {
    sourceSystemId: string;
    totalRecords: number;
    lastIngestedAt: string | null;
    runtimeCapturesLast24h: number;
    lastImportRun: {
      runId: string;
      status: ImportStatus;
      recordsProcessed: number;
      recordsSkipped: number;
      startedAt: string;
      completedAt: string | null;
    } | null;
  }[];
}
