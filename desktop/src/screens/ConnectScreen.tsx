import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { checkHealth } from "../lib/api";
import { getServerConfig, setServerConfig } from "../lib/store";

export default function ConnectScreen() {
  const [url, setUrl] = useState("http://localhost:8000");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    void (async () => {
      const existing = await getServerConfig();
      if (existing) setUrl(existing.url);
    })();
  }, []);

  async function handleConnect(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const cleaned = url.trim().replace(/\/$/, "");
      const ok = await checkHealth(cleaned);
      if (!ok) {
        setError(
          "Could not reach an AnswerGuard server at that URL. Check the URL and that the server is running.",
        );
        return;
      }
      await setServerConfig({ url: cleaned, lastVerifiedAt: new Date().toISOString() });
      navigate("/connector/details");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-screen items-center justify-center bg-slate-50">
      <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="mb-2 text-2xl font-bold text-slate-900">Connect to AnswerGuard</h1>
        <p className="mb-6 text-sm text-slate-600">
          Enter the URL of your running AnswerGuard instance.
        </p>
        <form onSubmit={handleConnect}>
          <label className="mb-1 block text-sm font-medium text-slate-700">Server URL</label>
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="http://localhost:8000"
            className="w-full rounded border border-slate-300 px-3 py-2 text-sm focus:border-slate-900 focus:outline-none"
            autoFocus
          />
          {error && (
            <p className="mt-2 text-sm text-rose-600">{error}</p>
          )}
          <button
            type="submit"
            disabled={loading || !url.trim()}
            className="mt-6 w-full rounded bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50 hover:bg-slate-800"
          >
            {loading ? "Connecting…" : "Connect"}
          </button>
        </form>
      </div>
    </div>
  );
}
