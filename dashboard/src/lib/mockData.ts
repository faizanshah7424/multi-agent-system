import { TaskModel, AgentMetadata, WorkerInfo, QueueStatus, SystemMetrics, MemoryLog, MemoryMessage, MemorySearchItem } from './api';

export const mockAgents: AgentMetadata[] = [
  {
    name: "planner",
    role: "Workflow Planner & Architect",
    description: "Deconstructs complex user instructions into concrete executable dependency graphs.",
    capabilities: ["workflow_planning", "validation", "dependency_resolution"],
    tools: ["memory_recall", "dir_scanner"]
  },
  {
    name: "researcher",
    role: "Academic & Web Researcher",
    description: "Performs web queries, extracts web content, and synthesizes reference material.",
    capabilities: ["web_search", "document_scraping", "synthesis"],
    tools: ["web_search", "file_reader"]
  },
  {
    name: "developer",
    role: "Senior Software Engineer",
    description: "Writes, refactors, debugs, and integrates production-grade codebase files.",
    capabilities: ["code_generation", "refactoring", "debugging"],
    tools: ["file_reader", "file_writer", "dir_scanner"]
  },
  {
    name: "reviewer",
    role: "QA Engineer & Auditor",
    description: "Audits written code against standards, logs errors, and recommends optimization paths.",
    capabilities: ["code_review", "linter_checks", "security_audit"],
    tools: ["file_reader"]
  }
];

export const mockTasks: TaskModel[] = [
  {
    task_id: "task_e3c12f0a",
    user_id: "user_dev_01",
    task_type: "workflow",
    payload: { task: "Build a responsive Next.js frontend for checking real-time queue states." },
    status: "COMPLETED",
    created_at: "2026-06-25T17:30:10Z",
    started_at: "2026-06-25T17:30:12Z",
    completed_at: "2026-06-25T17:32:45Z",
    retry_count: 0,
    error: null
  },
  {
    task_id: "task_fa2b98e1",
    user_id: "user_dev_01",
    task_type: "workflow",
    payload: { task: "Implement distributed worker support in core queue coordinator." },
    status: "RUNNING",
    created_at: "2026-06-25T23:45:00Z",
    started_at: "2026-06-25T23:45:05Z",
    completed_at: null,
    retry_count: 1,
    error: "Transient rate limits hit on Gemini API (HTTP 429)"
  },
  {
    task_id: "task_301bdf2a",
    user_id: "user_marketing_03",
    task_type: "workflow",
    payload: { task: "Scrape and compile competitive analysis report on multi-agent frameworks." },
    status: "RETRYING",
    created_at: "2026-06-25T23:50:12Z",
    started_at: "2026-06-25T23:50:18Z",
    completed_at: null,
    retry_count: 2,
    error: "Failed to connect to web search server: timeout after 10000ms"
  },
  {
    task_id: "task_408bcf11",
    user_id: "user_qa_02",
    task_type: "workflow",
    payload: { task: "Verify memory leaks on heavy background task loops with 50 parallel workers." },
    status: "FAILED",
    created_at: "2026-06-25T22:10:00Z",
    started_at: "2026-06-25T22:10:08Z",
    completed_at: "2026-06-25T22:15:20Z",
    retry_count: 3,
    error: "SystemException: Memory allocation failed - host exhausted 100% swap memory."
  },
  {
    task_id: "task_92cf88ab",
    user_id: null,
    task_type: "workflow",
    payload: { task: "Refactor core/cache.py invalidation rules." },
    status: "QUEUED",
    created_at: "2026-06-25T23:55:00Z",
    started_at: null,
    completed_at: null,
    retry_count: 0,
    error: null
  }
];

export const mockWorkers: WorkerInfo[] = [
  {
    worker_name: "WorkerThread-1",
    worker_id: 1,
    is_alive: true,
    is_healthy: true,
    current_task: "task_fa2b98e1",
    last_active: "2026-06-25T23:56:40Z"
  },
  {
    worker_name: "WorkerThread-2",
    worker_id: 2,
    is_alive: true,
    is_healthy: true,
    current_task: null,
    last_active: "2026-06-25T23:56:38Z"
  },
  {
    worker_name: "WorkerThread-3",
    worker_id: 3,
    is_alive: false,
    is_healthy: false,
    current_task: null,
    last_active: "2026-06-25T22:15:20Z"
  }
];

export const mockQueueStatus: QueueStatus = {
  queue_size: 2,
  worker_count: 3,
  tasks_by_status: {
    "COMPLETED": 124,
    "RUNNING": 1,
    "FAILED": 8,
    "RETRYING": 1,
    "QUEUED": 1,
    "PENDING": 0
  }
};

export const mockMetrics: SystemMetrics = {
  requests_count: 1452,
  agent_executions_count: 612,
  workflow_executions_count: 134,
  tool_executions_count: 2489,
  queue_size: 2,
  retries_count: 15,
  failures_count: 9,
  timestamp: "2026-06-25T23:56:43Z",
  costs: {
    total_system_cost_usd: 8.7523,
    cost_per_agent_usd: {
      "planner": 1.2405,
      "researcher": 3.8412,
      "developer": 2.9103,
      "reviewer": 0.7603
    },
    cost_per_task_usd: {
      "task_e3c12f0a": 0.3541,
      "task_fa2b98e1": 0.8123,
      "task_301bdf2a": 0.4502,
      "task_408bcf11": 1.1205
    },
    cost_per_workflow_usd: {
      "task_e3c12f0a": 0.3541,
      "task_fa2b98e1": 0.8123,
      "task_301bdf2a": 0.4502,
      "task_408bcf11": 1.1205
    },
    cost_per_request_usd: {
      "req_a1b2c3": 0.0025,
      "req_d4e5f6": 0.0152,
      "req_789012": 0.0078
    }
  },
  tokens: {
    total_prompt_tokens: 3845920,
    total_completion_tokens: 1854910,
    total_tokens: 5700830,
    tokens_by_agent: {
      "planner": 892010,
      "researcher": 2459100,
      "developer": 1820420,
      "reviewer": 529300
    },
    tokens_by_task: {
      "task_e3c12f0a": 250000,
      "task_fa2b98e1": 580000,
      "task_301bdf2a": 320000,
      "task_408bcf11": 810000
    },
    tokens_by_workflow: {
      "task_e3c12f0a": 250000,
      "task_fa2b98e1": 580000,
      "task_301bdf2a": 320000,
      "task_408bcf11": 810000
    },
    tokens_by_session: {
      "task_e3c12f0a": 250000,
      "task_fa2b98e1": 580000,
      "task_301bdf2a": 320000,
      "task_408bcf11": 810000
    },
    llm_calls_count: 854
  },
  performance: {
    average_workflow_latency_seconds: 45.8,
    p95_workflow_latency_seconds: 112.5,
    average_request_latency_seconds: 0.142,
    p95_request_latency_seconds: 0.485,
    average_queue_wait_time_seconds: 2.14,
    worker_utilization_rate: 0.333,
    memory_usage_bytes: 142590200 // ~142MB
  }
};

export const mockCacheMetrics = {
  llm_cache: {
    hits: 245,
    misses: 609,
    hit_rate: 0.286,
    size: 412
  },
  tool_cache: {
    hits: 1204,
    misses: 1285,
    hit_rate: 0.483,
    latency_saved_ms: 184500, // ~184.5 seconds saved!
    size: 678
  }
};

export const mockHistory: Record<string, { logs: MemoryLog[]; messages: MemoryMessage[] }> = {
  "task_fa2b98e1": {
    logs: [
      { timestamp: "2026-06-25T23:45:00Z", source: "system", message: "Queuing background task execution: 'Implement distributed worker support in core queue coordinator.'", level: "INFO" },
      { timestamp: "2026-06-25T23:45:05Z", source: "worker", message: "Worker pulling task_fa2b98e1 for execution.", level: "INFO" },
      { timestamp: "2026-06-25T23:45:06Z", source: "workflow", message: "Starting workflow execution for task: 'Implement distributed worker support...'", level: "INFO" },
      { timestamp: "2026-06-25T23:45:10Z", source: "planner", message: "Generating workflow plan steps...", level: "INFO" },
      { timestamp: "2026-06-25T23:45:12Z", source: "workflow", message: "Plan generated: Distributed Worker Architecture. Total steps: 3", level: "INFO" },
      { timestamp: "2026-06-25T23:45:13Z", source: "workflow", message: "Beginning Step 1: 'Identify required message queues' -> Assigned to researcher", level: "INFO" },
      { timestamp: "2026-06-25T23:45:20Z", source: "researcher", message: "Searching web for: 'Python distributed task queues with Redis or RabbitMQ comparison'", level: "INFO" },
      { timestamp: "2026-06-25T23:45:21Z", source: "researcher", message: "Cache Hit for search query: web search latency saved = 350ms.", level: "INFO" },
      { timestamp: "2026-06-25T23:45:30Z", source: "researcher", message: "Formulating research report summarizing Redis pub/sub vs. Celery protocol.", level: "INFO" },
      { timestamp: "2026-06-25T23:45:40Z", source: "LLM", message: "Gemini API call warning: rate limit (429) resource exhausted, retrying in exponential backoff...", level: "WARN" }
    ],
    messages: [
      { role: "user", content: "Implement distributed worker support in core queue coordinator.", timestamp: "2026-06-25T23:45:00Z", agent_name: "user" },
      { role: "planner", content: "Plan generated:\n1. [researcher] Research messaging protocols.\n2. [developer] Write distributed connection listeners.\n3. [reviewer] Review lock safety.", timestamp: "2026-06-25T23:45:12Z", agent_name: "planner" },
      { role: "researcher", content: "Comparing Redis vs RMQ: Redis is ideal for low-latency in-memory message routing. I suggest implementing Redis Pub/Sub.", timestamp: "2026-06-25T23:45:38Z", agent_name: "researcher" }
    ]
  },
  "task_e3c12f0a": {
    logs: [
      { timestamp: "2026-06-25T17:30:10Z", source: "system", message: "Queuing background task execution: 'Build responsive Next.js frontend...'", level: "INFO" },
      { timestamp: "2026-06-25T17:30:12Z", source: "worker", message: "Worker pulling task_e3c12f0a.", level: "INFO" },
      { timestamp: "2026-06-25T17:30:15Z", source: "workflow", message: "Beginning execution. Step 1: 'Draft Tailwind structure' -> Assigned to developer", level: "INFO" },
      { timestamp: "2026-06-25T17:31:00Z", source: "developer", message: "Writing code file: dashboard/src/app/page.tsx", level: "INFO" },
      { timestamp: "2026-06-25T17:32:00Z", source: "developer", message: "Tailwind templates written. Running reviewer verification...", level: "INFO" },
      { timestamp: "2026-06-25T17:32:30Z", source: "reviewer", message: "Verifying HTML semantic layouts and dark mode mappings.", level: "INFO" },
      { timestamp: "2026-06-25T17:32:45Z", source: "workflow", message: "All workflow steps completed successfully.", level: "INFO" }
    ],
    messages: [
      { role: "user", content: "Build a responsive Next.js frontend...", timestamp: "2026-06-25T17:30:10Z", agent_name: "user" },
      { role: "developer", content: "Code written to index dashboard. Layout uses flexgrid responsive queries.", timestamp: "2026-06-25T17:32:00Z", agent_name: "developer" },
      { role: "reviewer", content: "Review passed. Excellent grid spacing and theme variables mapping.", timestamp: "2026-06-25T17:32:40Z", agent_name: "reviewer" }
    ]
  }
};

export const mockMemorySearch: MemorySearchItem[] = [
  {
    text: "Distributed tasks are processed by WorkerPool class listening to TaskQueue.",
    metadata: { source: "task_queue_implementation_summary", doc_type: "design" },
    similarity: 0.892,
    timestamp: "2026-06-25T18:19:10Z"
  },
  {
    text: "Task models represent PENDING, QUEUED, RUNNING, COMPLETED, FAILED, RETRYING states.",
    metadata: { source: "task_queue_implementation_summary", doc_type: "design" },
    similarity: 0.814,
    timestamp: "2026-06-25T18:19:10Z"
  },
  {
    text: "Central metrics service aggregates prompt_tokens, completion_tokens, and total_cost.",
    metadata: { source: "observability_design_report", doc_type: "observability" },
    similarity: 0.745,
    timestamp: "2026-06-25T23:55:00Z"
  }
];
