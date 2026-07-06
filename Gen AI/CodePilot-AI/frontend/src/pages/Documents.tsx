import React, { useState, useEffect } from "react";
import { useProject } from "../contexts/ProjectContext";
import { documentService } from "../services/api";
import { Document } from "../types";
import { useToast } from "../contexts/ToastContext";
import {
  FileText,
  Upload,
  Database,
  Trash2,
  AlertCircle,
  FolderLock,
  Loader2,
  FileCheck,
  Download,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export const Documents: React.FC = () => {
  const { currentProject } = useProject();
  const { toast } = useToast();

  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  // Upload States
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [docType, setDocType] = useState("business_requirement_document");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  
  // Ingest state tracker (docId -> boolean)
  const [ingestingMap, setIngestingMap] = useState<Record<string, boolean>>({});

  const documentTypes = [
    { value: "business_requirement_document", label: "Business Requirements (BRD)" },
    { value: "system_architecture_document", label: "Architecture Spec" },
    { value: "project_plan", label: "Project Implementation Plan" },
    { value: "codebase_manifest", label: "Code Manifest" },
    { value: "test_specification", label: "Test Spec Sheet" },
  ];

  const fetchDocuments = async () => {
    if (!currentProject) return;
    setIsLoading(true);
    try {
      const data = await documentService.list(currentProject.id);
      setDocuments(data);
    } catch (error) {
      console.error(error);
      toast("Failed to load documents.", "error");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [currentProject]);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentProject) return;
    if (!selectedFile) {
      toast("Please select a file to upload first.", "error");
      return;
    }

    setIsUploading(true);
    setUploadProgress(20);
    try {
      setUploadProgress(50);
      await documentService.upload(currentProject.id, selectedFile, docType);
      setUploadProgress(90);
      toast(`Uploaded ${selectedFile.name} successfully!`, "success");
      setSelectedFile(null);
      await fetchDocuments();
    } catch (error) {
      console.error(error);
      toast("Document upload failed.", "error");
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleIngest = async (docId: string, filename: string) => {
    if (!currentProject) return;
    setIngestingMap((prev) => ({ ...prev, [docId]: true }));
    try {
      await documentService.ingest(currentProject.id, docId);
      toast(`Indexed ${filename} in vector database successfully!`, "success");
    } catch (error) {
      console.error(error);
      toast("Indexing / Ingestion failed.", "error");
    } finally {
      setIngestingMap((prev) => ({ ...prev, [docId]: false }));
    }
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!currentProject) return;

    try {
      await documentService.delete(currentProject.id, docId);
      toast("Document removed.", "success");
      await fetchDocuments();
    } catch (error) {
      console.error(error);
      toast("Failed to delete document.", "error");
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
          Please select or create a project context from the dropdown at the top header to begin uploading documents.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Heading */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight font-heading text-slate-100">
          Source Documents
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Upload and index reference specification documents into the RAG vector store for project context.
        </p>
      </div>

      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Column */}
        <div className="glass-card p-6 rounded-2xl h-fit">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-900/50 pb-3 mb-4">
            Upload Document
          </h2>

          <form onSubmit={handleUploadSubmit} className="space-y-4">
            {/* Drag Drop Area */}
            <div
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              className={`relative border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center transition-all ${
                dragActive
                  ? "border-blue-500 bg-blue-500/5"
                  : selectedFile
                  ? "border-slate-700 bg-slate-900/20"
                  : "border-slate-800 hover:border-slate-700"
              }`}
            >
              <input
                type="file"
                id="file-upload"
                onChange={handleFileChange}
                accept=".txt,.pdf,.docx"
                className="hidden"
              />
              
              {selectedFile ? (
                <>
                  <FileCheck className="w-10 h-10 text-blue-400 mb-3" />
                  <p className="text-xs font-semibold text-slate-200 truncate max-w-[200px]">
                    {selectedFile.name}
                  </p>
                  <p className="text-[10px] text-slate-500 mt-1">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </p>
                  <button
                    type="button"
                    onClick={() => setSelectedFile(null)}
                    className="text-[10px] font-semibold text-red-400 hover:text-red-300 mt-4 underline decoration-dotted"
                  >
                    Remove File
                  </button>
                </>
              ) : (
                <>
                  <Upload className="w-8 h-8 text-slate-500 mb-3" />
                  <label
                    htmlFor="file-upload"
                    className="text-xs font-semibold text-blue-400 hover:text-blue-300 cursor-pointer"
                  >
                    Click to upload
                  </label>
                  <p className="text-[10px] text-slate-500 mt-1">
                    or drag & drop text files (PDF, DOCX, TXT)
                  </p>
                </>
              )}
            </div>

            {/* Document Type Selection */}
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-500 mb-1.5">
                Document Type
              </label>
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-800 bg-[#090b14] focus:border-blue-500 outline-none text-slate-300 text-xs transition-colors"
              >
                {documentTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Progress bar */}
            {isUploading && (
              <div className="space-y-1.5">
                <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                  <span>Uploading...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="h-1 bg-slate-900 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isUploading || !selectedFile}
              className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-lg shadow-blue-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-1.5"
            >
              {isUploading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
              <span>Upload Document</span>
            </button>
          </form>
        </div>

        {/* List Column */}
        <div className="lg:col-span-2 glass-card p-6 rounded-2xl">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-900/50 pb-3 mb-4">
            Uploaded Documents ({documents.length})
          </h2>

          <div className="divide-y divide-slate-900/40">
            {isLoading ? (
              <div className="flex items-center justify-center py-16 text-xs text-slate-500 italic">
                <Loader2 className="w-4 h-4 animate-spin text-blue-500 mr-2" />
                <span>Loading documents...</span>
              </div>
            ) : documents.length === 0 ? (
              <div className="flex flex-col items-center justify-center text-center py-16 text-slate-500 italic text-xs gap-3">
                <FileText className="w-8 h-8 text-slate-600" />
                <span>No source documents uploaded.</span>
              </div>
            ) : (
              documents.map((doc) => {
                const isIngesting = ingestingMap[doc.id] || false;
                
                return (
                  <div key={doc.id} className="flex items-center justify-between py-4 hover:bg-slate-900/10 px-2 rounded-xl transition-colors">
                    <div className="flex items-start gap-3 min-w-0">
                      <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 shrink-0">
                        <FileText className="w-4.5 h-4.5" />
                      </div>
                      <div className="min-w-0">
                        <h3 className="text-xs font-semibold text-slate-200 truncate max-w-xs md:max-w-md">
                          {doc.filename}
                        </h3>
                        <div className="flex items-center gap-2 mt-1 text-[10px] text-slate-500 font-mono">
                          <span className="bg-slate-900/80 px-2 py-0.5 rounded-full border border-slate-800/40">
                            {doc.document_type.replace(/_/g, " ")}
                          </span>
                          <span>•</span>
                          <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {/* Ingest trigger */}
                      <button
                        onClick={() => handleIngest(doc.id, doc.filename)}
                        disabled={isIngesting}
                        className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg border text-[10px] font-semibold transition-all ${
                          isIngesting
                            ? "bg-slate-900 border-slate-800 text-slate-500 cursor-not-allowed"
                            : "bg-blue-600/10 hover:bg-blue-600/20 border-blue-500/20 text-blue-400"
                        }`}
                      >
                        {isIngesting ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <Database className="w-3 h-3" />
                        )}
                        <span>{isIngesting ? "Indexing..." : "Index Vector"}</span>
                      </button>

                      {/* Delete */}
                      <button
                        onClick={() => handleDelete(doc.id, doc.filename)}
                        className="p-2 rounded-lg hover:bg-slate-900 border border-transparent hover:border-slate-800 text-slate-500 hover:text-red-400 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
