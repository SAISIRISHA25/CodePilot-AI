import React, { createContext, useContext, useState, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react";

interface Toast {
  id: string;
  message: string;
  type: "success" | "error" | "info";
}

interface ToastContextType {
  toast: (message: string, type?: "success" | "error" | "info") => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((message: string, type: "success" | "error" | "info" = "success") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      
      {/* Toast Overlay Container */}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-3 max-w-md w-full pointer-events-none">
        <AnimatePresence>
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.15 } }}
              className="pointer-events-auto flex items-center justify-between gap-3 p-4 rounded-xl border glass shadow-2xl"
              style={{
                borderColor:
                  t.type === "success"
                    ? "rgba(16, 185, 129, 0.2)"
                    : t.type === "error"
                    ? "rgba(239, 68, 68, 0.2)"
                    : "rgba(59, 130, 246, 0.2)",
                background:
                  t.type === "success"
                    ? "rgba(6, 78, 59, 0.85)"
                    : t.type === "error"
                    ? "rgba(127, 29, 29, 0.85)"
                    : "rgba(30, 58, 138, 0.85)",
              }}
            >
              <div className="flex items-center gap-3">
                {t.type === "success" && <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />}
                {t.type === "error" && <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />}
                {t.type === "info" && <Info className="w-5 h-5 text-blue-400 shrink-0" />}
                <p className="text-sm font-medium text-slate-100">{t.message}</p>
              </div>
              <button
                onClick={() => removeToast(t.id)}
                className="text-slate-400 hover:text-slate-200 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
};
