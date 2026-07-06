import React, { useState, useEffect } from "react";
import { useProject } from "../contexts/ProjectContext";
import { workflowService } from "../services/api";
import { useToast } from "../contexts/ToastContext";
import {
  GitFork,
  Play,
  Loader2,
  Trash2,
  Clock,
  Compass,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  FileCode,
  FolderLock,
  RefreshCw,
} from "lucide-react";
import { motion } from "framer-motion";

const workflowNodes = [
  { key: "requirements", name: "Requirements Engineering" },
  { key: "architecture", name: "System Architecture" },
  { key: "planning", name: "Project Planning" },
  { key: "coding", name: "Code Generation" },
  { key: "testing", name: "Test Design" },
  { key: "documentation", name: "Documentation" },
  { key: "review", name: "Engineering Review" },
];

export const Workflow: React.FC = () => {
  const { currentProject } = useProject();
  const { toast } = useToast();

  const [prompt, setPrompt] = useState("Draft CodePilot integration workflow");
  const [status, setStatus] = useState<any | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchWorkflowState = async (silent: boolean = false) => {
    if (!currentProject) return;
    if (!silent) setIsLoading(true);
    try {
      const runStatus = await workflowService.getStatus(currentProject.id);
      setStatus(runStatus);

      const runHistory = await workflowService.getHistory(currentProject.id);
      setHistory(runHistory.history || []);
    } catch (error) {
      console.error(error);
    } finally {
      if (!silent) setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflowState();
  }, [currentProject]);

  const handleStartWorkflow = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentProject) return;
    if (!prompt.trim()) {
      toast("Please specify a workflow directive/prompt.", "error");
      return;
    }

    setIsRefreshing(true);
    try {
      toast("Triggering LangGraph workflow execution...", "info");
      const res = await workflowService.start(currentProject.id, prompt);
      setStatus(res);
      toast("Workflow execution complete!", "success");
      await fetchWorkflowState(true);
    } catch (error) {
      console.error(error);
      toast("Workflow failed or index is empty.", "error");
      await fetchWorkflowState(true);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleCancelWorkflow = async () => {
    if (!currentProject) return;

    try {
      await workflowService.cancel(currentProject.id);
      toast("Workflow execution cancelled.", "success");
      await fetchWorkflowState(true);
    } catch (error) {
      console.error(error);
      toast("Failed to cancel workflow.", "error");
    }
  };

  if (!currentProject) {
    return (
      <div className="h-[80vh] flex flex-col items-center justify-center text-center p-8 max-w-md mx-auto">
        <div className="w-16 h-16 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center mb-6">
          <FolderLock className="w-8 h-8 text-blue-500" />
        </div>
        <h2 className="text-xl font-bold font-heading text-slate-100">Project Context Required</h2>
        <p className="text-sm text-slate-500 mt-2">
          Please select or create a project context from the dropdown at the top header to inspect workflows.
        </p>
      </div>
    );
  }

  // Helper to determine state of each node based on the overall workflow status
  const getNodeState = (nodeKey: string) => {
    if (!status) return "pending";
    const statusVal = status.status?.toLowerCase();
    
    if (statusVal === "failed") return "failed";
    if (statusVal === "cancelled") return "failed";
    
    // Sequence order of execution
    const phaseOrder = [
      "requirements",
      "architecture",
      "planning",
      "coding",
      "testing",
      "documentation",
      "review"
    ];
    
    const nodeIndex = phaseOrder.indexOf(nodeKey);
    
    if (statusVal === "running") {
      const currentPhase = status.message?.toLowerCase() || "";
      if (currentPhase.includes(nodeKey)) return "running";
      
      const activeNodeIndex = phaseOrder.findIndex((ph) => currentPhase.includes(ph));
      if (activeNodeIndex === -1) return "pending";
      if (nodeIndex < activeNodeIndex) return "completed";
      return "pending";
    }
    
    // If finished, its status is the final completed phase (like "review")
    const activeNodeIndex = phaseOrder.indexOf(statusVal);
    if (activeNodeIndex !== -1) {
      if (nodeIndex <= activeNodeIndex) return "completed";
      return "pending";
    }
    
    if (statusVal === "completed") return "completed";
    
    return "pending";
  };

  return (
    <div className="space-y-8">
      {/* Heading */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight font-heading text-slate-100">
            Workflow Orchestration
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Orchestrate and monitor LangGraph SDLC pipelines in real-time.
          </p>
        </div>

        <button
          onClick={() => fetchWorkflowState(false)}
          className="p-2 rounded-xl border border-slate-800 bg-slate-950/20 text-slate-400 hover:text-slate-200 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Graph Pipeline */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-6 rounded-2xl">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-900/50 pb-3 mb-6">
              Visual SDLC Execution Graph
            </h2>

            {/* Nodes timeline */}
            <div className="flex flex-col gap-6 relative">
              {/* Connecting line */}
              <div className="absolute left-[21px] top-6 bottom-6 w-0.5 bg-slate-900 z-0" />

              {workflowNodes.map((node, index) => {
                const nodeState = getNodeState(node.key);
                
                return (
                  <div key={node.key} className="flex items-center gap-4 relative z-10">
                    {/* Node status bubble */}
                    <div className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0 border shadow-md font-bold text-xs"
                      style={{
                        backgroundColor:
                          nodeState === "completed"
                            ? "rgba(16, 185, 129, 0.1)"
                            : nodeState === "running"
                            ? "rgba(59, 130, 246, 0.1)"
                            : nodeState === "failed"
                            ? "rgba(239, 68, 68, 0.1)"
                            : "rgba(15, 23, 42, 0.6)",
                        borderColor:
                          nodeState === "completed"
                            ? "rgba(16, 185, 129, 0.4)"
                            : nodeState === "running"
                            ? "#3b82f6"
                            : nodeState === "failed"
                            ? "rgba(239, 68, 68, 0.4)"
                            : "rgba(255, 255, 255, 0.05)",
                        color:
                          nodeState === "completed"
                            ? "#10b981"
                            : nodeState === "running"
                            ? "#3b82f6"
                            : nodeState === "failed"
                            ? "#ef4444"
                            : "#64748b",
                      }}
                    >
                      {nodeState === "completed" ? (
                        <CheckCircle className="w-5 h-5" />
                      ) : nodeState === "running" ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : nodeState === "failed" ? (
                        <AlertTriangle className="w-5 h-5" />
                      ) : (
                        <span>{index + 1}</span>
                      )}
                    </div>

                    {/* Node Label details */}
                    <div>
                      <h3 className={`text-xs font-bold ${nodeState === "running" ? "text-blue-400" : "text-slate-300"}`}>
                        {node.name}
                      </h3>
                      <p className="text-[10px] text-slate-500 font-mono mt-0.5 capitalize">
                        Status: {nodeState}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Trigger / Controls side-panel */}
        <div className="space-y-6">
          {/* Controls */}
          <div className="glass-card p-6 rounded-2xl">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-900/50 pb-3 mb-4">
              Trigger Master Prompt
            </h2>

            <form onSubmit={handleStartWorkflow} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                  Workflow Directive
                </label>
                <textarea
                  rows={3}
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="e.g. Build CodePilot system orchestrator"
                  className="w-full px-3 py-2 rounded-lg border border-slate-900 bg-[#090b14]/50 focus:border-blue-500 outline-none text-slate-300 text-xs transition-colors resize-none"
                />
              </div>

              {/* Status display banner */}
              {status && (
                <div className="p-3.5 rounded-xl border border-slate-900 bg-slate-950/20 text-xs flex flex-col">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-400">Current Status:</span>
                    <span className="font-mono uppercase text-blue-400 font-bold">{status.status}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 mt-1">{status.message}</span>
                </div>
              )}

              <div className="flex gap-3 pt-2">
                {status?.status === "running" ? (
                  <button
                    type="button"
                    onClick={handleCancelWorkflow}
                    className="flex-1 py-2.5 rounded-xl bg-red-600/10 border border-red-500/20 hover:bg-red-600/20 text-red-400 font-semibold text-xs transition-all flex items-center justify-center gap-1.5"
                  >
                    <span>Cancel Run</span>
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={isRefreshing}
                    className="flex-1 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center gap-1.5 disabled:opacity-50"
                  >
                    {isRefreshing ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Play className="w-3.5 h-3.5" />
                    )}
                    <span>{isRefreshing ? "Running..." : "Run Workflow"}</span>
                  </button>
                )}
              </div>
            </form>
          </div>

          {/* History log */}
          <div className="glass-card p-6 rounded-2xl flex flex-col max-h-96">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-900/50 pb-3 mb-4">
              Execution Trace Logs ({history.length})
            </h2>

            <div className="flex-1 overflow-y-auto space-y-3">
              {history.length === 0 ? (
                <div className="text-slate-500 text-xs py-8 italic text-center">
                  No execution traces available
                </div>
              ) : (
                history.map((h, hidx) => (
                  <div key={hidx} className="p-3 rounded-lg border border-slate-900/40 bg-slate-950/20 text-xs">
                    <div className="flex justify-between items-center font-bold text-slate-300">
                      <span>Phase: {h.phase}</span>
                      <span className="text-[9px] text-slate-500 font-mono">
                        {new Date(h.occurred_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-500 mt-1 leading-relaxed">{h.summary}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
