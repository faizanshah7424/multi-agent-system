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

export interface AdminUser {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface AdminRole {
  id: string;
  name: string;
  description: string;
  created_at: string;
  permissions: string[];
}

export interface AdminPermission {
  id: string;
  name: string;
  description: string;
}

export interface AuditLog {
  id: number;
  event_type: string;
  user_id: string;
  details: string;
  timestamp: string;
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  type: string;
  category: string;
  is_read: boolean;
  created_at: string;
  read_at: string | null;
}

export interface NotificationPreferences {
  email_enabled: boolean;
  sms_enabled: boolean;
  in_app_enabled: boolean;
  marketing_emails: boolean;
  security_alerts: boolean;
  task_updates: boolean;
}

export interface NotificationQueueItem {
  id: string;
  channel: string;
  recipient: string;
  title: string | null;
  content: string;
  status: string;
  attempts: number;
  error_message: string | null;
  created_at: string;
}

export interface NotificationStats {
  in_app: {
    total: number;
    unread: number;
  };
  queue: {
    total: number;
    pending: number;
    sent: number;
    failed: number;
    retrying: number;
  };
  channels: {
    email: number;
    sms: number;
  };
  recent_queue: NotificationQueueItem[];
}

export interface HospitalPatient {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  date_of_birth: string;
  gender: string;
  medical_history: string | null;
}

export interface HospitalDoctor {
  id: string;
  name: string;
  specialty: string;
  email: string | null;
  phone: string | null;
  is_available: boolean;
}

export interface HospitalAppointment {
  id: string;
  patient_id: string;
  patient_name: string;
  doctor_id: string;
  doctor_name: string;
  appointment_date: string;
  reason: string;
  status: string;
  notes: string | null;
}

export interface HospitalBilling {
  id: string;
  patient_id: string;
  patient_name: string;
  appointment_id: string | null;
  amount: number;
  status: string;
  payment_method: string | null;
  billing_date: string;
}

export interface HospitalPharmacyItem {
  id: string;
  name: string;
  dosage: string;
  stock_quantity: number;
  unit_price: number;
}

export interface HospitalPrescription {
  id: string;
  patient_id: string;
  patient_name: string;
  doctor_id: string;
  doctor_name: string;
  medication_name: string;
  dosage_instruction: string;
  status: string;
  created_at: string;
}

export interface HospitalLabTest {
  id: string;
  patient_id: string;
  patient_name: string;
  test_name: string;
  result: string | null;
  status: string;
  technician_notes: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface HospitalStats {
  patients: number;
  doctors: number;
  appointments: {
    total: number;
    scheduled: number;
  };
  billing: {
    total_billed: number;
    unpaid: number;
    paid: number;
  };
  pharmacy: {
    total_drugs: number;
    total_prescriptions: number;
    pending: number;
  };
  laboratory: {
    total_tests: number;
    pending: number;
  };
}

export interface ProjectRecord {
  product_id: string;
  idea: string;
  success: boolean;
  duration_s: number;
  business_specs?: Record<string, unknown>;
  requirements?: Record<string, unknown>;
  domain_model?: Record<string, unknown>;
  database_design?: Record<string, unknown>;
  api_design?: Record<string, unknown>;
  frontend_plan?: Record<string, unknown>;
  backend_plan?: Record<string, unknown>;
  testing_plan?: Record<string, unknown>;
  deployment_plan?: Record<string, unknown>;
  debate?: Record<string, unknown>;
  documents?: Record<string, string>;
  generated_code?: {
    project_dir: string;
    zip_path: string;
    zip_filename: string;
    files: Array<{ path: string; lines: number; size_bytes: number }>;
    total_files: number;
  };
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

  // Admin endpoints
  getAdminUsers: () => fetchJson<AdminUser[]>('/admin/users'),
  updateAdminUser: (userId: string, payload: { role?: string; is_active?: boolean }) =>
    fetchJson<{ message: string; user: { id: string; email: string; role: string; is_active: boolean } }>(`/admin/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  getAdminRoles: () => fetchJson<AdminRole[]>('/admin/roles'),
  getAdminPermissions: () => fetchJson<AdminPermission[]>('/admin/permissions'),
  updateRolePermissions: (roleId: string, permissionNames: string[]) =>
    fetchJson<{ message: string }>(`/admin/roles/${roleId}/permissions`, {
      method: 'POST',
      body: JSON.stringify({ permission_names: permissionNames }),
    }),
  getAdminAuditLogs: (limit = 100, offset = 0) =>
    fetchJson<AuditLog[]>(`/admin/audit-logs?limit=${limit}&offset=${offset}`),

  // Notification endpoints
  getNotifications: (unreadOnly = false) => 
    fetchJson<NotificationItem[]>(`/notifications?unread_only=${unreadOnly}`),
  readNotification: (notificationId: string) => 
    fetchJson<{ message: string }>(`/notifications/${notificationId}/read`, { method: 'PUT' }),
  readAllNotifications: () => 
    fetchJson<{ message: string }>('/notifications/read-all', { method: 'POST' }),
  getNotificationPreferences: () => 
    fetchJson<NotificationPreferences>('/notifications/preferences'),
  updateNotificationPreferences: (payload: Partial<NotificationPreferences>) => 
    fetchJson<{ message: string; preferences: NotificationPreferences }>('/notifications/preferences', {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  getNotificationStats: () => 
    fetchJson<NotificationStats>('/notifications/stats'),
  triggerTestNotification: (payload: { title: string; message: string; category?: string; channel?: string; force_failure?: boolean }) => 
    fetchJson<{ message: string; result: Record<string, string> }>('/notifications/test', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  triggerProcessQueue: () => 
    fetchJson<{ message: string }>('/notifications/process-queue', { method: 'POST' }),

  // Hospital Management System endpoints
  getHospitalPatients: () => fetchJson<HospitalPatient[]>('/hospital/patients'),
  createHospitalPatient: (payload: Omit<HospitalPatient, 'id'>) => 
    fetchJson<{ message: string; id: string }>('/hospital/patients', { method: 'POST', body: JSON.stringify(payload) }),
  getHospitalDoctors: () => fetchJson<HospitalDoctor[]>('/hospital/doctors'),
  createHospitalDoctor: (payload: Omit<HospitalDoctor, 'id' | 'created_at'>) => 
    fetchJson<{ message: string; id: string }>('/hospital/doctors', { method: 'POST', body: JSON.stringify(payload) }),
  getHospitalAppointments: () => fetchJson<HospitalAppointment[]>('/hospital/appointments'),
  createHospitalAppointment: (payload: { patient_id: string; doctor_id: string; appointment_date: string; reason: string; notes?: string }) => 
    fetchJson<{ message: string; id: string }>('/hospital/appointments', { method: 'POST', body: JSON.stringify(payload) }),
  updateHospitalAppointmentStatus: (id: string, status: string) => 
    fetchJson<{ message: string }>(`/hospital/appointments/${id}/status?status=${status}`, { method: 'PUT' }),
  getHospitalBilling: () => fetchJson<HospitalBilling[]>('/hospital/billing'),
  createHospitalBilling: (payload: { patient_id: string; appointment_id?: string; amount: number }) => 
    fetchJson<{ message: string; id: string }>('/hospital/billing', { method: 'POST', body: JSON.stringify(payload) }),
  payHospitalBill: (id: string, payload: { payment_method: string }) => 
    fetchJson<{ message: string }>(`/hospital/billing/${id}/pay`, { method: 'PUT', body: JSON.stringify(payload) }),
  getHospitalPharmacyItems: () => fetchJson<HospitalPharmacyItem[]>('/hospital/pharmacy/items'),
  createHospitalPharmacyItem: (payload: Omit<HospitalPharmacyItem, 'id'>) => 
    fetchJson<{ message: string; id: string }>('/hospital/pharmacy/items', { method: 'POST', body: JSON.stringify(payload) }),
  getHospitalPrescriptions: () => fetchJson<HospitalPrescription[]>('/hospital/pharmacy/prescriptions'),
  createHospitalPrescription: (payload: { patient_id: string; doctor_id: string; medication_name: string; dosage_instruction: string }) => 
    fetchJson<{ message: string; id: string }>('/hospital/pharmacy/prescriptions', { method: 'POST', body: JSON.stringify(payload) }),
  dispenseHospitalPrescription: (id: string) => 
    fetchJson<{ message: string }>(`/hospital/pharmacy/prescriptions/${id}/dispense`, { method: 'PUT' }),
  getHospitalLabTests: () => fetchJson<HospitalLabTest[]>('/hospital/lab/tests'),
  createHospitalLabTest: (payload: { patient_id: string; test_name: string }) => 
    fetchJson<{ message: string; id: string }>('/hospital/lab/tests', { method: 'POST', body: JSON.stringify(payload) }),
  completeHospitalLabTest: (id: string, payload: { result: string; technician_notes?: string }) => 
    fetchJson<{ message: string }>(`/hospital/lab/tests/${id}/complete`, { method: 'PUT', body: JSON.stringify(payload) }),
  getHospitalStats: () => fetchJson<HospitalStats>('/hospital/stats'),

  // Autonomous Project Engine Endpoints
  buildProject: (idea: string) => fetchJson<ProjectRecord>('/projects/build', {
    method: 'POST',
    body: JSON.stringify({ idea }),
  }),
  getProjects: () => fetchJson<ProjectRecord[]>('/projects'),
  getProject: (projectId: string) => fetchJson<ProjectRecord>(`/projects/${projectId}`),
  getProjectDownloadUrl: (projectId: string) => `${API_BASE_URL}/projects/${projectId}/download`,
};
