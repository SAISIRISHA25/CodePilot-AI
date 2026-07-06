import React, { useState } from "react";
import { useProject } from "../contexts/ProjectContext";
import { agentService } from "../services/api";
import { useToast } from "../contexts/ToastContext";
import {
  Bot,
  Play,
  Loader2,
  FileText,
  Clock,
  Coins,
  ChevronRight,
  FolderLock,
  X,
  FileCode,
  CheckCircle,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface AgentCard {
  type: string;
  name: string;
  description: string;
  defaultTask: string;
  iconColor: string;
}

const agentsList: AgentCard[] = [
  {
    type: "requirements",
    name: "Requirements Agent",
    description: "Extracts and formats functional/non-functional requirements from sources.",
    defaultTask: "Extract all core functional requirements from the uploaded specification files.",
    iconColor: "text-blue-400 bg-blue-500/10",
  },
  {
    type: "architecture",
    name: "Architecture Agent",
    description: "Designs system components, database schemas, and data flow layers.",
    defaultTask: "Propose a system architecture diagram layout and outline component dependencies.",
    iconColor: "text-purple-400 bg-purple-500/10",
  },
  {
    type: "planning",
    name: "Planning Agent",
    description: "Drafts project implementation plans, milestones, and task checklists.",
    defaultTask: "Create a 3-phase implementation plan mapping files to modules.",
    iconColor: "text-amber-400 bg-amber-500/10",
  },
  {
    type: "coding",
    name: "Coding Agent",
    description: "Generates boilerplate code templates, route structures, and tests.",
    defaultTask: "Implement main class boilerplate and helper methods based on requirements.",
    iconColor: "text-emerald-400 bg-emerald-500/10",
  },
  {
    type: "testing",
    name: "Testing Agent",
    description: "Designs verification test scenarios, asserts, and mock expectations.",
    defaultTask: "Write basic unit test assertions validating database operations.",
    iconColor: "text-rose-400 bg-rose-500/10",
  },
  {
    type: "documentation",
    name: "Documentation Agent",
    description: "Produces deployment READMEs, user guides, and API schemas.",
    defaultTask: "Generate a markdown guide detailing endpoints and setup commands.",
    iconColor: "text-teal-400 bg-teal-500/10",
  },
  {
    type: "review",
    name: "Review Agent",
    description: "Performs audit code validations and signs off on architecture.",
    defaultTask: "Audit component boundary conditions and verify clean architecture adherence.",
    iconColor: "text-indigo-400 bg-indigo-500/10",
  },
];

export const AIAgents: React.FC = () => {
  const { currentProject } = useProject();
  const { toast } = useToast();

  const [tasks, setTasks] = useState<Record<string, string>>(() => {
    const initial: Record<string, string> = {};
    agentsList.forEach((a) => {
      initial[a.type] = a.defaultTask;
    });
    return initial;
  });

  const [executingMap, setExecutingMap] = useState<Record<string, boolean>>({});
  const [resultsMap, setResultsMap] = useState<Record<string, any>>({});
  const [activeResult, setActiveResult] = useState<any | null>(null);

  const handleRunAgent = async (type: string, name: string) => {
    if (!currentProject) return;
    
    const taskText = tasks[type]?.trim();
    if (!taskText) {
      toast("Please specify a task description.", "error");
      return;
    }

    setExecutingMap((prev) => ({ ...prev, [type]: true }));
    toast(`Triggered ${name}...`, "info");
    
    try {
      const response = await agentService.execute(currentProject.id, type, taskText);
      setResultsMap((prev) => ({ ...prev, [type]: response }));
      toast(`${name} execution complete!`, "success");
      setActiveResult(response);
    } catch (error) {
      console.error(error);
      toast(`${name} failed. Index files or provide context first.`, "error");
    } finally {
      setExecutingMap((prev) => ({ ...prev, [type]: false }));
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
          Please select or create a project context from the dropdown at the top header to run autonomous agents.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Heading */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight font-heading text-slate-100">
          AI Agent Operations
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Execute isolated agent actions directly on project data context and inspect outputs.
        </p>
      </div>

      {/* Grid of Agents */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agentsList.map((agent) => {
          const isRunning = executingMap[agent.type] || false;
          const result = resultsMap[agent.type];
          
          return (
            <div key={agent.type} className="glass-card p-5 rounded-2xl flex flex-col justify-between group">
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-2.5 rounded-xl ${agent.iconColor} shrink-0`}>
                    <Bot className="w-5 h-5" />
                  </div>
                  
                  {result && (
                    <button
                      onClick={() => setActiveResult(result)}
                      className="text-[10px] font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-0.5"
                    >
                      <span>Show Output</span>
                      <ChevronRight className="w-3 h-3" />
                    </button>
                  )}
                </div>

                <h3 className="text-sm font-bold text-slate-200">{agent.name}</h3>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                  {agent.description}
                </p>

                {/* Custom Task Input */}
                <div className="mt-4">
                  <label className="block text-[9px] font-bold uppercase tracking-wider text-slate-600 mb-1">
                    Task Prompt
                  </label>
                  <textarea
                    rows={2}
                    value={tasks[agent.type]}
                    onChange={(e) => setTasks({ ...tasks, [agent.type]: e.target.value })}
                    placeholder="Provide specific instructions..."
                    className="w-full px-3 py-2 rounded-lg border border-slate-900 bg-[#090b14]/50 focus:border-blue-500 outline-none text-slate-300 text-xs transition-colors resize-none"
                  />
                </div>
              </div>

              {/* Controls */}
              <div className="mt-6 pt-4 border-t border-slate-900/40 flex items-center justify-between">
                <span className="text-[10px] font-mono text-slate-500">
                  Type: {agent.type}
                </span>

                <button
                  onClick={() => handleRunAgent(agent.type, agent.name)}
                  disabled={isRunning}
                  className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 font-semibold text-[11px] text-white shadow-lg shadow-blue-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                >
                  {isRunning ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    <Play className="w-3 h-3 fill-white" />
                  )}
                  <span>{isRunning ? "Executing..." : "Run"}</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Slide-over details drawer for agent outputs */}
      <AnimatePresence>
        {activeResult && (
          <div className="fixed inset-0 z-50 flex justify-end">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.5 }}
              exit={{ opacity: 0 }}
              onClick={() => setActiveResult(null)}
              className="absolute inset-0 bg-black"
            />

            {/* Drawer */}
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 30, stiffness: 300 }}
              className="relative w-full max-w-xl h-full bg-[#0c0e18] border-l border-slate-900 shadow-2xl flex flex-col z-10 text-slate-200"
            >
              <header className="h-16 shrink-0 border-b border-slate-900 px-6 flex items-center justify-between bg-slate-950/20">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                  <div>
                    <h2 className="text-sm font-bold text-slate-200">
                      {activeResult.agent_name}
                    </h2>
                    <p className="text-[9px] text-slate-500 font-mono">
                      Type: {activeResult.agent_type}
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => setActiveResult(null)}
                  className="p-1 rounded-md hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </header>

              {/* Metadata display */}
              <div className="px-6 py-3 border-b border-slate-900 bg-slate-950/10 flex items-center gap-6 text-[10px] text-slate-400 font-mono">
                {activeResult.execution_time_ms && (
                  <div className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-blue-400" />
                    <span>Duration: {(activeResult.execution_time_ms / 1000).toFixed(2)}s</span>
                  </div>
                )}

                {activeResult.token_usage && (
                  <div className="flex items-center gap-1">
                    <Coins className="w-3.5 h-3.5 text-purple-400" />
                    <span>Tokens: {activeResult.token_usage.total_tokens}</span>
                  </div>
                )}
              </div>

              {/* Output Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-slate-400">
                  <FileText className="w-4 h-4 text-blue-400" />
                  <span>Generated Blueprint Output</span>
                </div>
                <div className="p-4 rounded-xl border border-slate-900 bg-slate-950/30 font-mono text-[11px] leading-relaxed whitespace-pre-wrap text-slate-300">
                  {activeResult.content}
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
