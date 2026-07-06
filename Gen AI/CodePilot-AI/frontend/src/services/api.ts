import { apiClient, APIResponse } from "../api/client";
import {
  Project,
  Document,
  IngestionResult,
  QueryResponse,
  Agent,
  AgentExecutionResponse,
  WorkflowStatusResponse,
  WorkflowHistoryResponse,
  Artifact,
  Conversation,
} from "../types";

export const projectService = {
  list: async (): Promise<Project[]> => {
    const res = await apiClient.get<APIResponse<Project[]>>("/projects");
    return res.data.data;
  },

  create: async (name: string, description: string): Promise<Project> => {
    const res = await apiClient.post<APIResponse<Project>>("/projects", {
      name,
      description,
    });
    return res.data.data;
  },

  get: async (id: string): Promise<Project> => {
    const res = await apiClient.get<APIResponse<Project>>(`/projects/${id}`);
    return res.data.data;
  },

  update: async (id: string, name: string, description: string): Promise<Project> => {
    const res = await apiClient.patch<APIResponse<Project>>(`/projects/${id}`, {
      name,
      description,
    });
    return res.data.data;
  },

  delete: async (id: string): Promise<boolean> => {
    const res = await apiClient.delete<APIResponse<{ deleted: boolean }>>(`/projects/${id}`);
    return res.data.success;
  },
};

export const documentService = {
  list: async (projectId: string): Promise<Document[]> => {
    const res = await apiClient.get<APIResponse<Document[]>>(`/projects/${projectId}/documents`);
    return res.data.data;
  },

  upload: async (projectId: string, file: File, documentType: string): Promise<Document> => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("document_type", documentType);

    const res = await apiClient.post<APIResponse<Document>>(
      `/projects/${projectId}/documents`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return res.data.data;
  },

  delete: async (projectId: string, docId: string): Promise<boolean> => {
    const res = await apiClient.delete<APIResponse<any>>(
      `/projects/${projectId}/documents/${docId}`
    );
    return res.data.success;
  },

  ingest: async (projectId: string, docId: string): Promise<IngestionResult> => {
    const res = await apiClient.post<APIResponse<IngestionResult>>(
      `/projects/${projectId}/documents/${docId}/ingest`
    );
    return res.data.data;
  },
};

export const queryService = {
  ask: async (projectId: string, question: string, topK: number = 3, documentType?: string): Promise<QueryResponse> => {
    const res = await apiClient.post<APIResponse<QueryResponse>>("/query", {
      project_id: projectId,
      question,
      top_k: topK,
      document_type: documentType || null,
    });
    return res.data.data;
  },
};

export const agentService = {
  list: async (): Promise<Agent[]> => {
    const res = await apiClient.get<APIResponse<Agent[]>>("/agents");
    return res.data.data;
  },

  execute: async (
    projectId: string,
    agentType: string,
    taskDescription: string,
    documentContext: string = "Functional Specifications"
  ): Promise<AgentExecutionResponse> => {
    const res = await apiClient.post<APIResponse<AgentExecutionResponse>>("/agents/execute", {
      project_id: projectId,
      agent_type: agentType,
      task_description: taskDescription,
      document_context: documentContext,
    });
    return res.data.data;
  },
};

export const workflowService = {
  start: async (projectId: string, prompt: string): Promise<WorkflowStatusResponse> => {
    const res = await apiClient.post<APIResponse<WorkflowStatusResponse>>(
      `/projects/${projectId}/workflow`,
      {
        project_id: projectId,
        prompt,
      }
    );
    return res.data.data;
  },

  getStatus: async (projectId: string): Promise<WorkflowStatusResponse> => {
    const res = await apiClient.get<APIResponse<WorkflowStatusResponse>>(
      `/projects/${projectId}/workflow`
    );
    return res.data.data;
  },

  getHistory: async (projectId: string): Promise<WorkflowHistoryResponse> => {
    const res = await apiClient.get<APIResponse<WorkflowHistoryResponse>>(
      `/projects/${projectId}/workflow/history`
    );
    return res.data.data;
  },

  cancel: async (projectId: string): Promise<boolean> => {
    const res = await apiClient.delete<APIResponse<any>>(`/projects/${projectId}/workflow`);
    return res.data.success;
  },
};

export const artifactService = {
  list: async (projectId: string): Promise<Artifact[]> => {
    const res = await apiClient.get<APIResponse<Artifact[]>>("/artifacts", {
      params: {
        project_id: projectId,
      },
    });
    return res.data.data;
  },

  download: async (artifactId: string): Promise<string> => {
    const res = await apiClient.get(`/artifacts/${artifactId}`, {
      responseType: "text",
    });
    return res.data;
  },

  delete: async (artifactId: string): Promise<boolean> => {
    const res = await apiClient.delete<APIResponse<any>>(`/artifacts/${artifactId}`);
    return res.data.success;
  },
};

export const chatService = {
  create: async (projectId: string, title?: string): Promise<Conversation> => {
    const res = await apiClient.post<APIResponse<Conversation>>("/conversations", {
      project_id: projectId,
      title: title || "New Chat",
    });
    return res.data.data;
  },
};

export const systemService = {
  getLogs: async (limit: number = 100): Promise<string[]> => {
    const res = await apiClient.get<APIResponse<{ lines: string[] }>>("/system/logs", {
      params: { limit },
    });
    return res.data.data.lines;
  },
};
