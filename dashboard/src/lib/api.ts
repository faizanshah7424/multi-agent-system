export interface AgentMetadata {
  name: string;
  role: string;
  description: string;
  capabilities: string[];
  tools: string[];
}

export interface TaskPayload {
  task: string;
  [key: string]: unknown;
}

export type TaskStatus = 'PENDING' | 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'RETRYING' | 'CANCELLED';

export interface TaskModel {
  task_id: string;
  user_id: string | null;
  task_type: string;
  payload: TaskPayload;
  status: TaskStatus;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  retry_count: number;
  error: string | null;
}

export interface WorkerInfo {
  worker_name: string;
  worker_id: number;
  is_alive: boolean;
  is_healthy: boolean;
  current_task: string | null;
  last_active: string;
}

export interface QueueStatus {
  queue_size: number;
  worker_count: number;
  tasks_by_status: Record<string, number>;
}

export interface CostMetrics {
  total_system_cost_usd: number;
  cost_per_agent_usd: Record<string, number>;
  cost_per_task_usd: Record<string, number>;
  cost_per_workflow_usd: Record<string, number>;
  cost_per_request_usd: Record<string, number>;
}

export interface TokenMetrics {
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  tokens_by_agent: Record<string, number>;
  tokens_by_task: Record<string, number>;
  tokens_by_workflow: Record<string, number>;
  tokens_by_session: Record<string, number>;
  llm_calls_count: number;
}

export interface PerformanceMetrics {
  average_workflow_latency_seconds: number;
  p95_workflow_latency_seconds: number;
  average_request_latency_seconds: number;
  p95_request_latency_seconds: number;
  average_queue_wait_time_seconds: number;
  worker_utilization_rate: number;
  memory_usage_bytes: number;
}

export interface CacheMetrics {
  llm_cache: {
    hits: number;
    misses: number;
    hit_rate: number;
    size: number;
  };
  tool_cache: {
    hits: number;
    misses: number;
    hit_rate: number;
    latency_saved_ms: number;
    size: number;
  };
}

export interface SystemMetrics {
  requests_count: number;
  agent_executions_count: number;
  workflow_executions_count: number;
  tool_executions_count: number;
  queue_size: number;
  retries_count: number;
  failures_count: number;
  costs: CostMetrics;
  tokens: TokenMetrics;
  performance: PerformanceMetrics;
  timestamp: string;
}

export interface MemoryLog {
  timestamp: string;
  source: string;
  message: string;
  level: string;
}

export interface MemoryMessage {
  role: string;
  content: string;
  timestamp: string;
  agent_name: string;
}

export interface SharedMemoryState {
  session_id: string;
  status: string;
  logs: MemoryLog[];
  messages: MemoryMessage[];
  variables: Record<string, unknown>;
}

export interface MemorySearchItem {
  text: string;
  metadata: Record<string, unknown>;
  similarity: number;
  timestamp: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error: ${response.status} - ${errorText || response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  // Agent Registry
  getAgents: () => fetchJson<AgentMetadata[]>('/agents'),

  // Tasks Management
  getTasks: () => fetchJson<TaskModel[]>('/tasks'),
  getTask: (taskId: string) => fetchJson<TaskModel>(`/tasks/${taskId}`),
  createTask: (payload: { task: string; task_type?: string; session_id?: string }) => 
    fetchJson<TaskModel>('/tasks', {
      method: 'POST',
      body: JSON.stringify({
        task_id: payload.session_id,
        task_type: payload.task_type || 'workflow',
        payload: { task: payload.task }
      })
    }),
  cancelTask: (taskId: string) => fetchJson<{ status: string; message: string }>(`/tasks/${taskId}`, {
    method: 'DELETE',
  }),

  // Workers & Queue
  getWorkers: () => fetchJson<WorkerInfo[]>('/workers'),
  getQueueStatus: () => fetchJson<QueueStatus>('/queue/status'),

  // Observability & Metrics
  getMetrics: () => fetchJson<SystemMetrics>('/metrics'),
  getCosts: () => fetchJson<CostMetrics>('/metrics/costs'),
  getTokens: () => fetchJson<TokenMetrics>('/metrics/tokens'),
  getPerformance: () => fetchJson<PerformanceMetrics>('/metrics/performance'),
  getCache: () => fetchJson<CacheMetrics>('/metrics/cache'),

  // Shared Memory & Logs status
  getMemoryStatus: (sessionId: string) => 
    fetchJson<{ session_id: string; status: string; steps: unknown[] }>(`/status?session_id=${sessionId}`),
  getMemoryHistory: (sessionId: string) =>
    fetchJson<{ session_id: string; logs: MemoryLog[]; messages: MemoryMessage[] }>(`/history?session_id=${sessionId}`),

  // Semantic Vector Memory Search
  searchMemory: (query: string, limit = 5) =>
    fetchJson<MemorySearchItem[]>(`/memory/search?query=${encodeURIComponent(query)}&limit=${limit}`),
  consolidateMemory: (sessionId: string) =>
    fetchJson<{ status: string; session_id: string; consolidated_summary: string }>(`/memory/consolidate?session_id=${sessionId}`, {
      method: 'POST',
    }),
};
