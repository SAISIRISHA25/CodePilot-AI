import React, { useState } from "react";
import { Link, useLocation, Outlet, useNavigate } from "react-router-dom";
import { useProject } from "../contexts/ProjectContext";
import {
  LayoutDashboard,
  FolderKanban,
  FileText,
  MessageSquare,
  Bot,
  GitFork,
  FileArchive,
  BarChart3,
  Settings,
  Menu,
  ChevronDown,
  Plus,
  Compass,
} from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

interface SidebarItem {
  name: string;
  path: string;
  icon: React.ComponentType<any>;
}

const sidebarItems: SidebarItem[] = [
  { name: "Dashboard", path: "/", icon: LayoutDashboard },
  { name: "Projects", path: "/projects", icon: FolderKanban },
  { name: "Documents", path: "/documents", icon: FileText },
  { name: "AI Chat", path: "/chat", icon: MessageSquare },
  { name: "Agents", path: "/agents", icon: Bot },
  { name: "Workflow", path: "/workflow", icon: GitFork },
  { name: "Artifacts", path: "/artifacts", icon: FileArchive },
  { name: "Analytics", path: "/analytics", icon: BarChart3 },
  { name: "Settings", path: "/settings", icon: Settings },
];

export const DashboardLayout: React.FC = () => {
  const { currentProject, setCurrentProject, projects, refreshProjects } = useProject();
  const location = useLocation();
  const navigate = useNavigate();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleProjectSelect = (projId: string) => {
    const selected = projects.find((p) => p.id === projId) || null;
    setCurrentProject(selected);
    setDropdownOpen(false);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#07080d]">
      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-64 shrink-0 border-r border-slate-900 bg-[#0b0d18] text-slate-300">
        {/* Brand Logo */}
        <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-900">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-500 to-purple-600 flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/25">
            CP
          </div>
          <div>
            <h1 className="text-md font-bold tracking-tight font-heading text-slate-100">CodePilot AI</h1>
            <p className="text-[10px] text-slate-500 font-mono">v1.0.0 (development)</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 py-6 px-4 space-y-1 overflow-y-auto">
          {sidebarItems.map((item) => {
            const isActive =
              item.path === "/"
                ? location.pathname === "/"
                : location.pathname.startsWith(item.path);

            return (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? "bg-gradient-to-r from-blue-600/15 to-purple-600/15 text-blue-400 border border-blue-500/20 shadow-inner"
                    : "hover:bg-slate-900/40 hover:text-slate-200 border border-transparent"
                }`}
              >
                <item.icon className={`w-4 h-4 ${isActive ? "text-blue-400" : "text-slate-400"}`} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-slate-900 bg-[#090b14]/50 flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-pink-500 flex items-center justify-center text-white font-bold text-sm shadow-md">
            S
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-300">Sai Sirisha</p>
            <p className="text-[10px] text-slate-500 font-mono">SAISIRISHA25/Hexaware</p>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-16 shrink-0 border-b border-slate-900 bg-[#090b14]/80 backdrop-blur-md flex items-center justify-between px-6 z-20">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden text-slate-400 hover:text-slate-200"
            >
              <Menu className="w-6 h-6" />
            </button>

            {/* Project Context Switcher */}
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-slate-800 bg-[#0d111d] hover:border-slate-700 text-xs font-medium text-slate-300 transition-colors"
              >
                <Compass className="w-3.5 h-3.5 text-blue-400" />
                <span className="max-w-[120px] truncate">
                  {currentProject ? currentProject.name : "Select Project"}
                </span>
                <ChevronDown className="w-3 h-3 text-slate-500" />
              </button>

              <AnimatePresence>
                {dropdownOpen && (
                  <>
                    {/* Backdrop */}
                    <div
                      className="fixed inset-0 z-30"
                      onClick={() => setDropdownOpen(false)}
                    />
                    <motion.div
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 8 }}
                      className="absolute left-0 mt-2 w-56 rounded-xl border border-slate-800 bg-[#0f1322] shadow-2xl z-40 py-1 overflow-hidden"
                    >
                      <div className="px-3 py-2 border-b border-slate-900 flex justify-between items-center">
                        <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">
                          Projects
                        </span>
                        <button
                          onClick={() => {
                            setDropdownOpen(false);
                            navigate("/projects?create=true");
                          }}
                          className="p-1 rounded-md hover:bg-slate-800 text-blue-400 hover:text-blue-300 transition-colors"
                        >
                          <Plus className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      <div className="max-h-48 overflow-y-auto">
                        {projects.length === 0 ? (
                          <div className="px-4 py-3 text-xs text-slate-500 italic">
                            No projects found
                          </div>
                        ) : (
                          projects.map((p) => (
                            <button
                              key={p.id}
                              onClick={() => handleProjectSelect(p.id)}
                              className={`w-full text-left px-4 py-2 text-xs font-medium transition-colors hover:bg-slate-900 flex items-center justify-between ${
                                currentProject?.id === p.id
                                  ? "text-blue-400 bg-blue-500/5"
                                  : "text-slate-300"
                              }`}
                            >
                              <span className="truncate">{p.name}</span>
                              {currentProject?.id === p.id && (
                                <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                              )}
                            </button>
                          ))
                        )}
                      </div>
                    </motion.div>
                  </>
                )}
              </AnimatePresence>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {currentProject && (
              <span className="hidden sm:inline text-xs text-slate-500 font-mono bg-slate-900/60 px-2.5 py-1 rounded-full border border-slate-800/40">
                Project ID: {currentProject.id.substring(0, 8)}...
              </span>
            )}
          </div>
        </header>

        {/* Mobile Navigation Drawer */}
        <AnimatePresence>
          {mobileOpen && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.5 }}
                exit={{ opacity: 0 }}
                onClick={() => setMobileOpen(false)}
                className="fixed inset-0 bg-black z-30 md:hidden"
              />
              <motion.aside
                initial={{ x: "-100%" }}
                animate={{ x: 0 }}
                exit={{ x: "-100%" }}
                transition={{ type: "spring", damping: 25 }}
                className="fixed top-0 bottom-0 left-0 w-64 bg-[#0b0d18] border-r border-slate-900 z-40 flex flex-col text-slate-300 md:hidden"
              >
                <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-900">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-500 to-purple-600 flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/25">
                    CP
                  </div>
                  <h1 className="text-md font-bold tracking-tight font-heading text-slate-100">CodePilot AI</h1>
                </div>
                <nav className="flex-1 py-6 px-4 space-y-1 overflow-y-auto">
                  {sidebarItems.map((item) => {
                    const isActive =
                      item.path === "/"
                        ? location.pathname === "/"
                        : location.pathname.startsWith(item.path);

                    return (
                      <Link
                        key={item.name}
                        to={item.path}
                        onClick={() => setMobileOpen(false)}
                        className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                          isActive
                            ? "bg-gradient-to-r from-blue-600/15 to-purple-600/15 text-blue-400 border border-blue-500/20 shadow-inner"
                            : "hover:bg-slate-900/40 hover:text-slate-200 border border-transparent"
                        }`}
                      >
                        <item.icon className={`w-4 h-4 ${isActive ? "text-blue-400" : "text-slate-400"}`} />
                        <span>{item.name}</span>
                      </Link>
                    );
                  })}
                </nav>
              </motion.aside>
            </>
          )}
        </AnimatePresence>

        {/* Scrollable Content View */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
