import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { checkHealth } from "../lib/api";
import { getLastImportRunId, getServerConfig, getSourceConnectorConfig } from "../lib/store";

interface NavState {
  connected: boolean;
  serverUrl: string | null;
  hasSourceConfig: boolean;
  hasCompletedImport: boolean;
}

export default function AppShell() {
  const [state, setState] = useState<NavState>({
    connected: false,
    serverUrl: null,
    hasSourceConfig: false,
    hasCompletedImport: false,
  });
  const navigate = useNavigate();

  useEffect(() => {
    async function load() {
      const server = await getServerConfig();
      const sourceCfg = await getSourceConnectorConfig();
      const lastRun = await getLastImportRunId();
      let connected = false;
      if (server) {
        connected = await checkHealth(server.url);
      }
      setState({
        connected,
        serverUrl: server?.url ?? null,
        hasSourceConfig: !!sourceCfg,
        hasCompletedImport: !!lastRun,
      });
      if (!server || !connected) {
        navigate("/connect");
      }
    }
    void load();
  }, [navigate]);

  return (
    <div className="flex h-full">
      <aside className="w-56 border-r border-slate-200 bg-slate-50 p-4 flex flex-col">
        <div className="mb-6">
          <h1 className="text-lg font-bold text-slate-900">AnswerGuard</h1>
          <div className="mt-1 flex items-center gap-1.5 text-xs">
            <span
              className={`inline-block h-2 w-2 rounded-full ${
                state.connected ? "bg-emerald-500" : "bg-rose-500"
              }`}
            />
            <span className="text-slate-600">
              {state.connected ? state.serverUrl ?? "Connected" : "Not connected"}
            </span>
          </div>
        </div>
        <nav className="flex flex-col gap-1 text-sm">
          <SidebarLink to="/connector" label="Source Setup" enabled={state.connected} />
          <SidebarLink to="/import" label="Import" enabled={state.hasSourceConfig} />
          <SidebarLink to="/data" label="Data" enabled={state.hasCompletedImport} />
        </nav>
      </aside>
      <main className="flex-1 overflow-auto bg-white">
        <Outlet />
      </main>
    </div>
  );
}

function SidebarLink({ to, label, enabled }: { to: string; label: string; enabled: boolean }) {
  if (!enabled) {
    return (
      <span className="px-3 py-1.5 rounded text-slate-400 cursor-not-allowed">{label}</span>
    );
  }
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `px-3 py-1.5 rounded transition-colors ${
          isActive
            ? "bg-slate-900 text-white"
            : "text-slate-700 hover:bg-slate-200"
        }`
      }
    >
      {label}
    </NavLink>
  );
}
