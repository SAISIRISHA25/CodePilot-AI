import React, { useState, useEffect } from "react";
import { useProject } from "../contexts/ProjectContext";
import { projectService } from "../services/api";
import { useToast } from "../contexts/ToastContext";
import { useSearchParams } from "react-router-dom";
import {
  Folder,
  Search,
  Plus,
  Trash2,
  Edit2,
  FolderOpen,
  X,
  FileCode,
} from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

export const Projects: React.FC = () => {
  const { projects, refreshProjects, currentProject, setCurrentProject } = useProject();
  const { toast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [search, setSearch] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"create" | "edit">("create");
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({ name: "", description: "" });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    // Check search params to open create modal
    if (searchParams.get("create") === "true") {
      openCreateModal();
      // Remove param from url
      setSearchParams({});
    }
  }, [searchParams]);

  const filteredProjects = projects.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase())
  );

  const openCreateModal = () => {
    setModalMode("create");
    setFormData({ name: "", description: "" });
    setIsModalOpen(true);
  };

  const openEditModal = (projectId: string, name: string, description: string) => {
    setModalMode("edit");
    setSelectedProjectId(projectId);
    setFormData({ name, description: description || "" });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast("Project name is required", "error");
      return;
    }

    setIsSubmitting(true);
    try {
      if (modalMode === "create") {
        await projectService.create(formData.name, formData.description);
        toast("Project created successfully!", "success");
      } else if (modalMode === "edit" && selectedProjectId) {
        await projectService.update(selectedProjectId, formData.name, formData.description);
        toast("Project updated successfully!", "success");
      }
      setIsModalOpen(false);
      await refreshProjects();
    } catch (error) {
      console.error(error);
      toast("Operation failed. Try again.", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Avoid triggering open project

    try {
      await projectService.delete(id);
      toast("Project deleted successfully.", "success");
      if (currentProject?.id === id) {
        setCurrentProject(null);
      }
      await refreshProjects();
    } catch (error) {
      console.error(error);
      toast("Failed to delete project.", "error");
    }
  };

  return (
    <div className="space-y-8">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight font-heading text-slate-100">
            Workspace Projects
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Manage your SDLC execution projects and workspace metadata contexts.
          </p>
        </div>

        <button
          onClick={openCreateModal}
          className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 font-medium text-sm text-white transition-all shadow-lg shadow-blue-500/25 shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>Create Project</span>
        </button>
      </div>

      {/* Filter and search */}
      <div className="relative max-w-md w-full">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input
          type="text"
          placeholder="Search projects..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-11 pr-4 py-2.5 rounded-xl border border-slate-900 bg-[#0c0e18] focus:border-blue-500 text-sm placeholder-slate-500 text-slate-200 outline-none transition-colors"
        />
      </div>

      {/* Grid of Projects */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredProjects.map((p) => {
          const isActive = currentProject?.id === p.id;
          return (
            <motion.div
              key={p.id}
              layoutId={p.id}
              onClick={() => setCurrentProject(p)}
              className={`glass-card p-6 rounded-2xl cursor-pointer relative overflow-hidden flex flex-col justify-between group ${
                isActive ? "border-blue-500/40 ring-1 ring-blue-500/10" : ""
              }`}
            >
              {/* Highlight background glow */}
              {isActive && (
                <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-blue-500/10 to-transparent rounded-bl-full pointer-events-none" />
              )}

              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-2.5 rounded-xl ${isActive ? "bg-blue-500/10 text-blue-400" : "bg-slate-900 text-slate-400"}`}>
                    <Folder className="w-5 h-5" />
                  </div>

                  {/* Actions buttons */}
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        openEditModal(p.id, p.name, p.description || "");
                      }}
                      className="p-1.5 rounded-lg hover:bg-slate-800/80 text-slate-400 hover:text-slate-200 transition-colors"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={(e) => handleDelete(p.id, e)}
                      className="p-1.5 rounded-lg hover:bg-slate-800/80 text-slate-400 hover:text-red-400 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <h3 className="text-lg font-bold tracking-tight text-slate-100 group-hover:text-blue-400 transition-colors">
                  {p.name}
                </h3>
                <p className="text-xs text-slate-400 mt-2 line-clamp-3">
                  {p.description || "No project description provided."}
                </p>
              </div>

              <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-900/50">
                <span className="text-[10px] text-slate-500 font-mono">
                  Created: {new Date(p.created_at).toLocaleDateString()}
                </span>
                <span className="flex items-center gap-1 text-[11px] font-semibold text-blue-400">
                  <FolderOpen className="w-3.5 h-3.5" />
                  <span>{isActive ? "Active" : "Select"}</span>
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Modal Dialog for Create/Edit */}
      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Overlay */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.6 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsModalOpen(false)}
              className="absolute inset-0 bg-black"
            />

            {/* Content box */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="relative w-full max-w-md p-6 rounded-2xl glass-card z-10"
            >
              <button
                onClick={() => setIsModalOpen(false)}
                className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>

              <h2 className="text-xl font-bold font-heading text-slate-100 mb-4">
                {modalMode === "create" ? "Create New Project" : "Edit Project Details"}
              </h2>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                    Project Name
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Enter project name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-800 bg-[#090b14] focus:border-blue-500 outline-none text-slate-200 text-sm transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                    Description
                  </label>
                  <textarea
                    rows={4}
                    placeholder="Provide a brief description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-xl border border-slate-800 bg-[#090b14] focus:border-blue-500 outline-none text-slate-200 text-sm transition-colors resize-none"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="px-4 py-2.5 text-xs font-semibold rounded-xl bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/25 transition-all flex items-center justify-center min-w-[80px]"
                  >
                    {isSubmitting ? "Saving..." : "Save"}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
