import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ProjectProvider } from "./contexts/ProjectContext";
import { SettingsProvider } from "./contexts/SettingsContext";
import { ToastProvider } from "./contexts/ToastContext";
import { DashboardLayout } from "./layouts/DashboardLayout";

// Pages
import { Dashboard } from "./pages/Dashboard";
import { Projects } from "./pages/Projects";
import { Documents } from "./pages/Documents";
import { AIChat } from "./pages/AIChat";
import { AIAgents } from "./pages/AIAgents";
import { Workflow } from "./pages/Workflow";
import { Artifacts } from "./pages/Artifacts";
import { Analytics } from "./pages/Analytics";
import { Settings } from "./pages/Settings";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <ProjectProvider>
          <SettingsProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/" element={<DashboardLayout />}>
                  <Route index element={<Dashboard />} />
                  <Route path="projects" element={<Projects />} />
                  <Route path="documents" element={<Documents />} />
                  <Route path="chat" element={<AIChat />} />
                  <Route path="agents" element={<AIAgents />} />
                  <Route path="workflow" element={<Workflow />} />
                  <Route path="artifacts" element={<Artifacts />} />
                  <Route path="analytics" element={<Analytics />} />
                  <Route path="settings" element={<Settings />} />
                  
                  {/* Fallback path redirect */}
                  <Route path="*" element={<Dashboard />} />
                </Route>
              </Routes>
            </BrowserRouter>
          </SettingsProvider>
        </ProjectProvider>
      </ToastProvider>
    </QueryClientProvider>
  );
}

export default App;
