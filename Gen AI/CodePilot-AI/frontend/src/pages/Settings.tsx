import React, { useState, useEffect } from "react";
import { useSettings } from "../contexts/SettingsContext";
import { useToast } from "../contexts/ToastContext";
import { Settings as SettingsIcon, Save, Info, Activity, RefreshCw, Loader2 } from "lucide-react";
import { systemService } from "../services/api";

export const Settings: React.FC = () => {
  const { settings, updateSettings } = useSettings();
  const { toast } = useToast();

  const [logs, setLogs] = useState<string[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchLogs = async () => {
    setRefreshing(true);
    try {
      const data = await systemService.getLogs(150);
      setLogs(data);
    } catch (err) {
      console.error("Failed to load system logs:", err);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchLogs();
    }, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const handleSave = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    updateSettings({
      model: formData.get("model") as string,
      temperature: parseFloat(formData.get("temperature") as string),
      embeddingModel: formData.get("embeddingModel") as string,
      chunkSize: parseInt(formData.get("chunkSize") as string, 10),
      chunkOverlap: parseInt(formData.get("chunkOverlap") as string, 10),
    });

    toast("Settings updated successfully!", "success");
  };

  return (
    <div className="space-y-8 max-w-2xl">
      {/* Heading */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight font-heading text-slate-100">
          Configuration Settings
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Adjust LLM chat models, RAG vector sizes, and chunk overlap thresholds.
        </p>
      </div>

      <div className="glass-card p-6 rounded-2xl">
        <div className="flex items-center gap-2 border-b border-slate-900/50 pb-4 mb-6">
          <SettingsIcon className="w-4 h-4 text-blue-400" />
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            System Parameters
          </h2>
        </div>

        <form onSubmit={handleSave} className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {/* Model Selection */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Chat Completion Model
              </label>
              <select
                name="model"
                defaultValue={settings.model}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-800 bg-[#090b14] focus:border-blue-500 outline-none text-slate-300 text-xs transition-colors"
              >
                <option value="gpt-4o-mini">gpt-4o-mini (Default)</option>
                <option value="gpt-4o">gpt-4o (Premium)</option>
                <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
              </select>
            </div>

            {/* Temperature */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Temperature ({settings.temperature})
              </label>
              <input
                type="range"
                name="temperature"
                min="0"
                max="1"
                step="0.1"
                defaultValue={settings.temperature}
                className="w-full h-1 bg-slate-900 rounded-lg appearance-none cursor-pointer accent-blue-500 mt-4"
              />
              <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                <span>Deterministic (0.0)</span>
                <span>Creative (1.0)</span>
              </div>
            </div>

            {/* Embedding Model */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Embedding Model
              </label>
              <select
                name="embeddingModel"
                defaultValue={settings.embeddingModel}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-800 bg-[#090b14] focus:border-blue-500 outline-none text-slate-300 text-xs transition-colors"
              >
                <option value="text-embedding-3-small">text-embedding-3-small</option>
                <option value="text-embedding-3-large">text-embedding-3-large</option>
                <option value="text-embedding-ada-002">text-embedding-ada-002</option>
              </select>
            </div>

            <div className="hidden sm:block" />

            {/* Chunk Size */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                RAG Chunk Size (tokens)
              </label>
              <input
                type="number"
                name="chunkSize"
                required
                min="100"
                max="5000"
                defaultValue={settings.chunkSize}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-800 bg-[#090b14] focus:border-blue-500 outline-none text-slate-300 text-xs transition-colors"
              />
            </div>

            {/* Chunk Overlap */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Chunk Overlap (tokens)
              </label>
              <input
                type="number"
                name="chunkOverlap"
                required
                min="0"
                max="1000"
                defaultValue={settings.chunkOverlap}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-800 bg-[#090b14] focus:border-blue-500 outline-none text-slate-300 text-xs transition-colors"
              />
            </div>
          </div>

          <div className="p-3.5 rounded-xl border border-slate-900 bg-slate-950/20 text-xs flex gap-2.5 text-slate-400 leading-relaxed">
            <Info className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
            <span>
              These parameters calibrate prompt execution triggers. Adjusting chunk boundaries impacts how specifications are segmented during the document loading & vector indexing phases.
            </span>
          </div>

          <div className="flex justify-end pt-4 border-t border-slate-900/50">
            <button
              type="submit"
              className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs shadow-lg shadow-blue-500/25 transition-all flex items-center gap-1.5"
            >
              <Save className="w-4 h-4" />
              <span>Save Settings</span>
            </button>
          </div>
        </form>
      </div>

      {/* System Log Monitor */}
      <div className="glass-card p-6 rounded-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-900/50 pb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              System Log Monitor
            </h2>
          </div>
          <div className="flex items-center gap-4">
            {/* Auto refresh toggle */}
            <label className="flex items-center gap-1.5 cursor-pointer select-none text-[11px] text-slate-400">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded border-slate-800 bg-[#090b14] accent-blue-500 w-3.5 h-3.5 cursor-pointer"
              />
              <span>Auto-refresh (5s)</span>
            </label>
            <button
              onClick={fetchLogs}
              disabled={refreshing}
              className="px-2.5 py-1 rounded-lg border border-slate-800 bg-[#0d111d] hover:border-slate-700 text-[10px] font-semibold text-slate-300 transition-colors flex items-center gap-1.5"
            >
              <RefreshCw className={`w-3 h-3 ${refreshing ? "animate-spin text-blue-500" : ""}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Console view */}
        <div className="w-full h-80 rounded-xl bg-black/90 border border-slate-900/80 p-4 font-mono text-[10.5px] overflow-y-auto space-y-1.5 select-text scrollbar-thin">
          {logs.length === 0 ? (
            <div className="text-slate-600 italic text-center py-24">No log traces recorded yet.</div>
          ) : (
            logs.map((line, idx) => {
              let colorClass = "text-slate-400";
              if (line.includes(" | ERROR | ")) colorClass = "text-red-400 font-semibold";
              else if (line.includes(" | WARNING | ")) colorClass = "text-yellow-400 font-semibold";
              else if (line.includes(" | DEBUG | ")) colorClass = "text-purple-400";
              else if (line.includes(" | INFO | ")) colorClass = "text-slate-300";
              
              return (
                <div key={idx} className={`${colorClass} leading-5 break-all whitespace-pre-wrap`}>
                  {line}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
