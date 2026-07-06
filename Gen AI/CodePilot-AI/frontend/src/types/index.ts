export interface Project {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  project_id: string;
  filename: string;
  document_type: string;
  file_path: string;
  created_at: string;
}

export interface IngestionResult {
  project_id: string;
  filename: string;
  document_type: string;
  source_document_id: string;
  total_chunks: number;
  chunk_ids: string[];
  embedding_model: string | null;
  ingested_at: string | null;
}

export interface QuerySource {
  filename: string;
  chunk_index: number;
  relevance_score: number;
}

export interface QueryResponse {
  question: string;
  answer: string;
  sources: QuerySource[];
  token_usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  model?: string;
}

export interface Agent {
  name: string;
  description: string;
  agent_type: string;
}

export interface AgentExecutionResponse {
  agent_type: string;
  agent_name: string;
  content: string;
  token_usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  execution_time_ms?: number;
}

export interface WorkflowStatusResponse {
  project_id: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
  message: string;
}

export interface WorkflowHistoryItem {
  phase: string;
  summary: string;
  occurred_at: string;
}

export interface WorkflowHistoryResponse {
  project_id: string;
  history: WorkflowHistoryItem[];
}

export interface Artifact {
  id: string;
  project_id: string;
  name: string;
  content: string;
  created_at: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: QuerySource[];
}

export interface Conversation {
  id: string;
  project_id: string;
  title: string | null;
}
