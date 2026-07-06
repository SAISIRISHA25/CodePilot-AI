import React, { useState, useEffect } from "react";
import { useProject } from "../contexts/ProjectContext";
import { artifactService } from "../services/api";
import { Artifact } from "../types";
import { useToast } from "../contexts/ToastContext";
import {
  FileText,
  Download,
  Trash2,
  Eye,
  Loader2,
  FolderLock,
  X,
  FileCode,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export const Artifacts: React.FC = () => {
  const { currentProject } = useProject();
  const { toast } = useToast();

  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activePreview, setActivePreview] = useState<Artifact | null>(null);
  const [previewContent, setPreviewContent] = useState("");
  const [loadingPreview, setLoadingPreview] = useState(false);

  const fetchArtifacts = async () => {
    if (!currentProject) return;
    setIsLoading(true);
    try {
      const data = await artifactService.list(currentProject.id);
      setArtifacts(data);
    } catch (error) {
      console.error(error);
      toast("Failed to load artifacts.", "error");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchArtifacts();
  }, [currentProject]);

  const handleOpenPreview = async (art: Artifact) => {
    setActivePreview(art);
    setLoadingPreview(true);
    try {
      const content = await artifactService.download(art.id);
      setPreviewContent(content);
    } catch (error) {
      console.error(error);
      toast("Failed to download artifact details.", "error");
      setActivePreview(null);
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleDownloadFile = async (art: Artifact) => {
    try {
      const content = await artifactService.download(art.id);
      
      // Trigger browser download
      const blob = new Blob([content], { type: "text/markdown;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${art.name}_blueprint.md`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      toast(`Downloaded ${art.name} blueprint successfully.`, "success");
    } catch (error) {
      console.error(error);
      toast("Download failed.", "error");
    }
  };

  const handleDelete = async (artId: string, name: string) => {
    try {
      await artifactService.delete(artId);
      toast("Artifact removed.", "success");
      await fetchArtifacts();
    } catch (error) {
      console.error(error);
      toast("Failed to delete artifact.", "error");
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
          Please select or create a project context from the dropdown at the top header to view generated artifacts.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Heading */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight font-heading text-slate-100">
          Generated Blueprints
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Explore and export generated software specifications, design manifests, and source files.
        </p>
      </div>

      {/* Grid List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-24 text-xs text-slate-500 italic">
          <Loader2 className="w-4 h-4 animate-spin text-blue-500 mr-2" />
          <span>Retrieving artifacts...</span>
        </div>
      ) : artifacts.length === 0 ? (
        <div className="glass-card p-12 rounded-2xl flex flex-col items-center justify-center text-center text-slate-500 italic text-xs gap-3">
          <FileText className="w-10 h-10 text-slate-700" />
          <span>No blueprints have been generated yet. Run the workflow or agent pipelines to produce outputs.</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {artifacts.map((art) => (
            <motion.div
              key={art.id}
              className="glass-card p-5 rounded-2xl flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-blue-400 shrink-0">
                    <FileCode className="w-5 h-5" />
                  </div>

                  <div className="flex items-center gap-1">
                    {/* View Preview */}
                    <button
                      onClick={() => handleOpenPreview(art)}
                      className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                    {/* Download */}
                    <button
                      onClick={() => handleDownloadFile(art)}
                      className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </button>
                    {/* Delete */}
                    <button
                      onClick={() => handleDelete(art.id, art.name)}
                      className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-red-400 transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <h3 className="text-xs font-bold text-slate-200 capitalize">
                  {art.name.replace(/_/g, " ")} Blueprint
                </h3>
                <p className="text-[10px] text-slate-500 mt-1 font-mono">
                  ID: {art.id.substring(0, 8)}...
                </p>
              </div>

              <div className="mt-6 pt-3 border-t border-slate-900/40 text-[10px] text-slate-500 font-mono">
                Generated: {new Date(art.created_at || Date.now()).toLocaleDateString()}
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Code Preview Drawer overlay */}
      <AnimatePresence>
        {activePreview && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.6 }}
              exit={{ opacity: 0 }}
              onClick={() => setActivePreview(null)}
              className="absolute inset-0 bg-black"
            />

            {/* Container box */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="relative w-full max-w-2xl h-[70vh] p-6 rounded-2xl glass-card z-10 flex flex-col"
            >
              <button
                onClick={() => setActivePreview(null)}
                className="absolute top-4 right-4 text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>

              <h2 className="text-lg font-bold font-heading text-slate-100 capitalize mb-4">
                {activePreview.name.replace(/_/g, " ")} Blueprint
              </h2>

              <div className="flex-1 overflow-y-auto p-4 rounded-xl border border-slate-900 bg-slate-950/40 font-mono text-[11px] leading-relaxed whitespace-pre-wrap text-slate-300">
                {loadingPreview ? (
                  <div className="flex items-center justify-center py-24 text-slate-500 italic">
                    <Loader2 className="w-4 h-4 animate-spin text-blue-500 mr-2" />
                    <span>Downloading blueprint details...</span>
                  </div>
                ) : (
                  previewContent
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
