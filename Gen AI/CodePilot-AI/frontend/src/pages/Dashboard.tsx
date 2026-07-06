import React, { useEffect, useState } from "react";
import { useProject } from "../contexts/ProjectContext";
import { projectService, documentService, artifactService, workflowService } from "../services/api";
import { Project, Document, Artifact } from "../types";
import { Link, useNavigate } from "react-router-dom";
import {
  Folder,
  FileText,
  FileArchive,
  GitFork,
  ChevronRight,
  TrendingUp,
  Activity,
  Plus,
} from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { motion } from "framer-motion";

export const Dashboard: React.FC = () => {
  const { projects, refreshProjects, isLoadingProjects } = useProject();
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    projectsCount: 0,
    documentsCount: 0,
    artifactsCount: 0,
    workflowRunsCount: 0,
  });
  const [recentActivities, setRecentActivities] = useState<any[]>([]);
  const [chartData, setChartData] = useState<any[]>([]);

  useEffect(() => {
    const fetchDashboardStats = async () => {
      if (projects.length === 0) {
        setStats({
          projectsCount: 0,
          documentsCount: 0,
          artifactsCount: 0,
          workflowRunsCount: 0,
        });
        setRecentActivities([]);
        setChartData([]);
        return;
      }

      try {
        let totalDocs = 0;
        let totalArtifacts = 0;
        let totalHistoryCount = 0;
        const activities: any[] = [];

        // Query details for all projects to aggregate totals
        await Promise.all(
          projects.map(async (p) => {
            try {
              const docs = await documentService.list(p.id);
              totalDocs += docs.length;

              const artifacts = await artifactService.list(p.id);
              totalArtifacts += artifacts.length;

              const history = await workflowService.getHistory(p.id);
              totalHistoryCount += history.history.length;

              // Log activities
              docs.forEach((d) => {
                const actTime = d.created_at ? new Date(d.created_at) : new Date();
                activities.push({
                  id: d.id,
                  type: "document",
                  message: `Uploaded document: ${d.filename}`,
                  project: p.name,
                  time: isNaN(actTime.getTime()) ? new Date() : actTime,
                });
              });

              artifacts.forEach((art) => {
                const actTime = art.created_at ? new Date(art.created_at) : new Date();
                activities.push({
                  id: art.id,
                  type: "artifact",
                  message: `Generated artifact: ${art.name}`,
                  project: p.name,
                  time: isNaN(actTime.getTime()) ? new Date() : actTime,
                });
              });
            } catch (err) {
              console.error(`Error loading stats for project ${p.id}:`, err);
            }
          })
        );

        setStats({
          projectsCount: projects.length,
          documentsCount: totalDocs,
          artifactsCount: totalArtifacts,
          workflowRunsCount: totalHistoryCount,
        });

        // Sort activities by time desc
        activities.sort((a, b) => b.time.getTime() - a.time.getTime());
        setRecentActivities(activities.slice(0, 5));

        // Create weekly chart data based on activities
        const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
        const weeklyData = days.map((day) => ({ name: day, activities: 0 }));
        
        activities.forEach((act) => {
          const dayIndex = act.time.getDay();
          weeklyData[dayIndex].activities += 1;
        });
        setChartData(weeklyData);

      } catch (error) {
        console.error("Failed to load dashboard data:", error);
      }
    };

    fetchDashboardStats();
  }, [projects]);

  const cards = [
    { name: "Total Projects", value: stats.projectsCount, icon: Folder, color: "from-blue-500 to-indigo-600", path: "/projects" },
    { name: "Uploaded Documents", value: stats.documentsCount, icon: FileText, color: "from-purple-500 to-pink-600", path: "/documents" },
    { name: "Artifacts Generated", value: stats.artifactsCount, icon: FileArchive, color: "from-amber-500 to-orange-600", path: "/artifacts" },
    { name: "Workflow Runs", value: stats.workflowRunsCount, icon: GitFork, color: "from-emerald-500 to-teal-600", path: "/workflow" },
  ];

  return (
    <div className="space-y-8">
      {/* Welcome Heading */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight font-heading text-slate-100">
            Welcome to <span className="text-gradient">CodePilot AI</span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time SDLC intelligence, multi-agent operations, and retrieval-grounded workflows.
          </p>
          <div className="flex flex-wrap gap-2 mt-3.5">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-sm shadow-emerald-500/5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              API: Online
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-500/10 text-blue-400 border border-blue-500/20 shadow-sm shadow-blue-500/5">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
              RAG Core: Ready
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-purple-500/10 text-purple-400 border border-purple-500/20 shadow-sm shadow-purple-500/5">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400"></span>
              LangGraph: Compiled
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-sm shadow-cyan-500/5">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
              SQLite Ledger: Connected
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-sm shadow-amber-500/5">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
              ChromaDB: Mounted
            </span>
          </div>
        </div>
        <button
          onClick={() => navigate("/projects?create=true")}
          className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 font-medium text-sm text-white transition-all shadow-lg shadow-blue-500/20"
        >
          <Plus className="w-4 h-4" />
          <span>New Project</span>
        </button>
      </div>

      {/* Stats Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((card, idx) => (
          <motion.div
            key={card.name}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            onClick={() => navigate(card.path)}
            className="glass-card p-6 rounded-2xl cursor-pointer relative overflow-hidden group"
          >
            {/* Hover Glow */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  {card.name}
                </p>
                <p className="text-3xl font-bold tracking-tight text-slate-100 mt-2">
                  {card.value}
                </p>
              </div>
              <div className={`w-10 h-10 rounded-xl bg-gradient-to-tr ${card.color} flex items-center justify-center shadow-lg`}>
                <card.icon className="w-5 h-5 text-white" />
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Main Sections Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Activity Chart Card */}
        <div className="lg:col-span-2 glass-card p-6 rounded-2xl flex flex-col">
          <div className="flex items-center gap-2 border-b border-slate-900/50 pb-4 mb-4">
            <TrendingUp className="w-4 h-4 text-blue-400" />
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              System Operations
            </h2>
          </div>
          <div className="h-64 w-full flex-1 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData.length > 0 ? chartData : [{ name: "Sun", activities: 0 }, { name: "Mon", activities: 0 }]}>
                <defs>
                  <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="name" stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "rgba(255,255,255,0.08)", borderRadius: "8px" }}
                  labelStyle={{ color: "#94a3b8", fontWeight: "bold" }}
                />
                <Area type="monotone" dataKey="activities" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#chartGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Activities Section */}
        <div className="glass-card p-6 rounded-2xl">
          <div className="flex items-center gap-2 border-b border-slate-900/50 pb-4 mb-4">
            <Activity className="w-4 h-4 text-purple-400" />
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Recent Activity
            </h2>
          </div>
          <div className="space-y-4 flex-1">
            {recentActivities.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 py-12 italic text-xs">
                No recent activity recorded
              </div>
            ) : (
              recentActivities.map((act) => (
                <div key={act.id} className="flex flex-col p-3 rounded-xl border border-slate-900/40 bg-slate-950/20 text-xs">
                  <span className="font-medium text-slate-200">{act.message}</span>
                  <div className="flex items-center justify-between mt-1 text-[10px] text-slate-500 font-mono">
                    <span>Project: {act.project}</span>
                    <span>{act.time.toLocaleTimeString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Recent Projects List */}
      <div className="glass-card p-6 rounded-2xl">
        <div className="flex items-center justify-between border-b border-slate-900/50 pb-4 mb-4">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Recent Projects
          </h2>
          <Link to="/projects" className="text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1">
            <span>View All</span>
            <ChevronRight className="w-3 h-3" />
          </Link>
        </div>
        <div className="divide-y divide-slate-900/40">
          {isLoadingProjects ? (
            <div className="text-slate-500 text-xs py-4 italic">Loading projects...</div>
          ) : projects.length === 0 ? (
            <div className="text-slate-500 text-xs py-4 italic">No projects found. Create your first one to begin!</div>
          ) : (
            projects.slice(0, 3).map((p) => (
              <div
                key={p.id}
                onClick={() => {
                  navigate(`/projects?id=${p.id}`);
                }}
                className="flex items-center justify-between py-4 hover:bg-slate-900/20 px-3 rounded-xl cursor-pointer transition-colors"
              >
                <div>
                  <h3 className="text-sm font-bold text-slate-200">{p.name}</h3>
                  <p className="text-xs text-slate-500 mt-0.5 max-w-md truncate">{p.description || "No description"}</p>
                </div>
                <span className="text-[10px] font-mono text-slate-500">
                  {new Date(p.created_at).toLocaleDateString()}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
