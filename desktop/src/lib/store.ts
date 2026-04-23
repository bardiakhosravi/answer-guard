import { load, Store } from "@tauri-apps/plugin-store";
import type { ServerConfig, SourceConnectorConfig } from "../types";

const CONFIG_FILE = "config.json";
let _store: Store | null = null;

async function getStore(): Promise<Store> {
  if (!_store) {
    _store = await load(CONFIG_FILE, { autoSave: true, defaults: {} });
  }
  return _store;
}

export async function getServerConfig(): Promise<ServerConfig | null> {
  const store = await getStore();
  return (await store.get<ServerConfig>("serverConfig")) ?? null;
}

export async function setServerConfig(config: ServerConfig): Promise<void> {
  const store = await getStore();
  await store.set("serverConfig", config);
}

export async function getSourceConnectorConfig(): Promise<SourceConnectorConfig | null> {
  const store = await getStore();
  return (await store.get<SourceConnectorConfig>("sourceConnector")) ?? null;
}

export async function setSourceConnectorConfig(config: SourceConnectorConfig): Promise<void> {
  const store = await getStore();
  await store.set("sourceConnector", config);
}

export async function getLastImportRunId(): Promise<string | null> {
  const store = await getStore();
  return (await store.get<string>("lastImportRunId")) ?? null;
}

export async function setLastImportRunId(runId: string): Promise<void> {
  const store = await getStore();
  await store.set("lastImportRunId", runId);
}
