import React, { createContext, useContext, useState, useEffect } from "react";
import { Project } from "../types";
import { projectService } from "../services/api";

interface ProjectContextType {
  currentProject: Project | null;
  setCurrentProject: (project: Project | null) => void;
  projects: Project[];
  isLoadingProjects: boolean;
  refreshProjects: () => Promise<void>;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export const ProjectProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentProject, setCurrentProjectState] = useState<Project | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoadingProjects, setIsLoadingProjects] = useState(true);

  const refreshProjects = async () => {
    setIsLoadingProjects(true);
    try {
      const data = await projectService.list();
      setProjects(data);
      
      // Auto-select first project if none is selected
      if (data.length > 0 && !currentProject) {
        // Try to load selected project from localStorage
        const savedId = localStorage.getItem("selected_project_id");
        const found = data.find((p) => p.id === savedId);
        setCurrentProjectState(found || data[0]);
      } else if (data.length === 0) {
        setCurrentProjectState(null);
      } else if (currentProject) {
        // Update current project if it changed in backend list
        const updated = data.find((p) => p.id === currentProject.id);
        if (updated) setCurrentProjectState(updated);
      }
    } catch (error) {
      console.error("Failed to load projects:", error);
    } finally {
      setIsLoadingProjects(false);
    }
  };

  const setCurrentProject = (project: Project | null) => {
    setCurrentProjectState(project);
    if (project) {
      localStorage.setItem("selected_project_id", project.id);
    } else {
      localStorage.removeItem("selected_project_id");
    }
  };

  useEffect(() => {
    refreshProjects();
  }, []);

  return (
    <ProjectContext.Provider
      value={{
        currentProject,
        setCurrentProject,
        projects,
        isLoadingProjects,
        refreshProjects,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
};

export const useProject = () => {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error("useProject must be used within a ProjectProvider");
  }
  return context;
};
