import React, { useState, useEffect } from "react";
import { useProject } from "../contexts/ProjectContext";
import { documentService, artifactService, workflowService } from "../services/api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { FolderLock, BarChart3, PieChartIcon, Activity, Loader2 } from "lucide-react";

export const Analytics: React.FC = () => {
  const { currentProject } = useProject();
  const [loading, setLoading] = useState(false);
  const [dataSummary, setDataSummary] = useState({
    documents: 0,
    artifacts: 0,
    historyRuns: 0,
  });

  const [agentPieData, setAgentPieData] = useState<any[]>([]);
  const [weeklyBarData, setWeeklyBarData] = useState<any[]>([]);

  const COLORS = ["#3b82f6", "#8b5cf6", "#a78bfa", "#f59e0b", "#10b981", "#ec4899", "#6366f1"];

  useEffect(() => {
    const fetchAnalytics = async () => {
      if (!currentProject) return;
      setLoading(true);
      try {
        const docs = await documentService.list(currentProject.id);
        const artifacts = await artifactService.list(currentProject.id);
        const runs = await workflowService.getHistory(currentProject.id);

        setDataSummary({
          documents: docs.length,
          artifacts: artifacts.length,
          historyRuns: runs.history.length,
        });

        // Group artifacts by type for agentPieData
        const typeCount: Record<string, number> = {};
        artifacts.forEach((art) => {
          typeCount[art.name] = (typeCount[art.name] || 0) + 1;
        });

        const pie = Object.keys(typeCount).map((k) => ({
          name: k.replace(/_/g, " "),
          value: typeCount[k],
        }));

        setAgentPieData(pie.length > 0 ? pie : [{ name: "No Artifacts", value: 1 }]);

        // Group runs by weekday for weeklyBarData
        const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
        const bar = days.map((day) => ({ name: day, runs: 0, uploads: 0 }));
        
        runs.history.forEach((run) => {
          const dayIdx = new Date(run.occurred_at || Date.now()).getDay();
          bar[dayIdx].runs += 1;
        });

        docs.forEach((doc) => {
          const dayIdx = new Date(doc.created_at || Date.now()).getDay();
          bar[dayIdx].uploads += 1;
        });

        setWeeklyBarData(bar);

      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, [currentProject]);

  if (!currentProject) {
    return (
      <div className="h-[80vh] flex flex-col items-center justify-center text-center p-8 max-w-md mx-auto">
        <div className="w-16 h-16 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center mb-6">
          <FolderLock className="w-8 h-8 text-blue-500" />
        </div>
        <h2 className="text-xl font-bold font-heading text-slate-100">Project Context Required</h2>
        <p className="text-sm text-slate-500 mt-2">
          Please select or create a project context from the dropdown at the top header to inspect analytics.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Heading */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight font-heading text-slate-100">
          Project Analytics
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Monitor your document imports, agent actions, and pipeline run trends.
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-24 text-xs text-slate-500 italic">
          <Loader2 className="w-4 h-4 animate-spin text-blue-500 mr-2" />
          <span>Aggregating analytics parameters...</span>
        </div>
      ) : (
        <>
          {/* Summary counters */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-card p-6 rounded-2xl">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Documents Processed
              </p>
              <p className="text-3xl font-bold tracking-tight text-slate-100 mt-2">
                {dataSummary.documents}
              </p>
            </div>
            <div className="glass-card p-6 rounded-2xl">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Total Artifacts Created
              </p>
              <p className="text-3xl font-bold tracking-tight text-slate-100 mt-2">
                {dataSummary.artifacts}
              </p>
            </div>
            <div className="glass-card p-6 rounded-2xl">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Workflow Orchestrations
              </p>
              <p className="text-3xl font-bold tracking-tight text-slate-100 mt-2">
                {dataSummary.historyRuns}
              </p>
            </div>
          </div>

          {/* Charts Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Weekly Activity */}
            <div className="glass-card p-6 rounded-2xl flex flex-col h-96">
              <div className="flex items-center gap-2 border-b border-slate-900/50 pb-4 mb-6">
                <Activity className="w-4 h-4 text-blue-400" />
                <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                  Weekly Run Patterns
                </h2>
              </div>
              
              <div className="flex-1 w-full mt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={weeklyBarData}>
                    <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                    <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{ backgroundColor: "#0f172a", borderColor: "rgba(255,255,255,0.08)", borderRadius: "8px" }}
                      labelStyle={{ color: "#94a3b8", fontWeight: "bold" }}
                    />
                    <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                    <Bar dataKey="runs" name="Workflow Runs" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="uploads" name="Doc Uploads" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Agent Usage Pie Chart */}
            <div className="glass-card p-6 rounded-2xl flex flex-col h-96">
              <div className="flex items-center gap-2 border-b border-slate-900/50 pb-4 mb-6">
                <PieChartIcon className="w-4 h-4 text-purple-400" />
                <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                  Agent Artifact Distribution
                </h2>
              </div>

              <div className="flex-1 w-full mt-2 relative">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={agentPieData}
                      cx="50%"
                      cy="45%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {agentPieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ backgroundColor: "#0f172a", borderColor: "rgba(255,255,255,0.08)", borderRadius: "8px" }}
                    />
                    <Legend
                      verticalAlign="bottom"
                      height={36}
                      wrapperStyle={{ fontSize: 10 }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
