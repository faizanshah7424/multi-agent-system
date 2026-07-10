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

let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

function onRefreshed(token: string) {
  refreshSubscribers.map(cb => cb(token));
  refreshSubscribers = [];
}

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('auth_access_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      ...headers,
      ...(options?.headers || {}),
    },
  });

  if (response.status === 401 && typeof window !== 'undefined') {
    const refreshToken = localStorage.getItem('auth_refresh_token');
    if (refreshToken && path !== '/auth/refresh' && path !== '/auth/login') {
      if (!isRefreshing) {
        isRefreshing = true;
        try {
          const refreshUrl = `${API_BASE_URL}/auth/refresh`;
          const refreshRes = await fetch(refreshUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });

          if (refreshRes.ok) {
            const data = await refreshRes.json() as { access_token: string };
            localStorage.setItem('auth_access_token', data.access_token);
            isRefreshing = false;
            onRefreshed(data.access_token);
          } else {
            localStorage.removeItem('auth_access_token');
            localStorage.removeItem('auth_refresh_token');
            isRefreshing = false;
            window.dispatchEvent(new Event('auth_logout'));
            throw new Error('Session expired');
          }
        } catch (err) {
          isRefreshing = false;
          localStorage.removeItem('auth_access_token');
          localStorage.removeItem('auth_refresh_token');
          window.dispatchEvent(new Event('auth_logout'));
          throw err;
        }
      }

      const retryPromise = new Promise<T>((resolve, reject) => {
        subscribeTokenRefresh((newToken) => {
          const newHeaders = {
            ...headers,
            ...(options?.headers || {}),
            'Authorization': `Bearer ${newToken}`,
          };
          fetch(url, { ...options, headers: newHeaders })
            .then(res => {
              if (!res.ok) {
                res.text().then(txt => reject(new Error(`API Error: ${res.status} - ${txt || res.statusText}`)));
              } else {
                resolve(res.json() as Promise<T>);
              }
            })
            .catch(reject);
        });
      });

      return retryPromise;
    }
  }

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error: ${response.status} - ${errorText || response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  // Auth endpoints
  login: (payload: Record<string, string>) => fetchJson<{ access_token: string; refresh_token: string }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  signup: (payload: Record<string, string>) => fetchJson<{ message: string; user_id: string; verification_token: string }>('/auth/signup', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  logout: (payload: { refresh_token: string }) => fetchJson<{ message: string }>('/auth/logout', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  forgotPassword: (payload: { email: string }) => fetchJson<{ message: string; reset_token?: string }>('/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  resetPassword: (payload: Record<string, string>) => fetchJson<{ message: string }>('/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  verifyEmail: (token: string) => fetchJson<{ message: string }>(`/auth/verify-email?token=${token}`),

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
