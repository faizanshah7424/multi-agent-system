import os
import time
import math
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from config import settings
from core.logging import get_logger

logger = get_logger("MetricsCollector")

# Configurable Pricing Model per 1 Million Tokens
def calculate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Computes total cost in USD for a given prompt/completion token count and model.
    """
    pricing_model = settings.model_pricing
    pricing = pricing_model.get(model_name)
    if not pricing:
        # Match model family prefixes (e.g. gemini-2.5-flash-8b)
        for key, val in pricing_model.items():
            if key in model_name:
                pricing = val
                break
                
    if not pricing:
        # Fallback to flash pricing
        pricing = pricing_model.get("gemini-2.5-flash", {"input": 0.075 / 1_000_000, "output": 0.30 / 1_000_000})
        
    return (prompt_tokens * pricing["input"]) + (completion_tokens * pricing["output"])

class MetricsCollector:
    """
    Central Metrics Service to monitor, store, and audit system consumption.
    Thread-safe and designed for Grafana/Prometheus dashboard responses.
    """
    def __init__(self) -> None:
        self._lock = threading.Lock()
        
        # General activity counters
        self.requests = 0
        self.agent_executions = 0
        self.workflow_executions = 0
        self.tool_executions = 0
        self.retries = 0
        self.failures = 0
        
        # Token and cost registries
        self.llm_calls: List[Dict[str, Any]] = []
        self.total_cost = 0.0
        self.agent_costs: Dict[str, float] = {}
        self.task_costs: Dict[str, float] = {}
        self.workflow_costs: Dict[str, float] = {}
        self.request_costs: Dict[str, float] = {}
        
        # Performance monitoring lists
        self.latencies: List[float] = [] # Workflow response latencies (s)
        self.queue_wait_times: List[float] = [] # Task queue latency waits (s)
        self.request_latencies: List[float] = [] # API request latencies (s)

    def record_request(self) -> None:
        with self._lock:
            self.requests += 1

    def record_request_duration(self, duration_s: float) -> None:
        with self._lock:
            self.request_latencies.append(duration_s)

    def record_agent_run(self, success: bool = True) -> None:
        with self._lock:
            self.agent_executions += 1
            if not success:
                self.failures += 1

    def record_workflow_run(self, duration_s: float, success: bool = True) -> None:
        with self._lock:
            self.workflow_executions += 1
            self.latencies.append(duration_s)
            if not success:
                self.failures += 1

    def record_tool_run(self) -> None:
        with self._lock:
            self.tool_executions += 1

    def record_retry(self) -> None:
        with self._lock:
            self.retries += 1

    def record_failure(self) -> None:
        with self._lock:
            self.failures += 1

    def record_queue_wait(self, duration_s: float) -> None:
        with self._lock:
            self.queue_wait_times.append(duration_s)

    def record_llm_call(
        self, 
        model_name: str, 
        prompt_tokens: int, 
        completion_tokens: int, 
        total_tokens: int, 
        execution_time_ms: float
    ) -> None:
        cost = calculate_cost(model_name, prompt_tokens, completion_tokens)
        
        # Pull correlation parameters from thread context
        from core.logging import get_correlation_context
        context = get_correlation_context()
        task_id = context.get("task_id", "N/A")
        workflow_id = context.get("workflow_id", "N/A")
        agent_name = context.get("agent_name", "N/A")
        request_id = context.get("request_id", "N/A")
        session_id = context.get("session_id", "N/A")
        
        entry = {
            "model_name": model_name,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "execution_time_ms": execution_time_ms,
            "cost": cost,
            "task_id": task_id,
            "workflow_id": workflow_id,
            "agent_name": agent_name,
            "request_id": request_id,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        }
        
        with self._lock:
            self.llm_calls.append(entry)
            self.total_cost += cost
            
            # Sub-accounting
            if agent_name != "N/A":
                self.agent_costs[agent_name] = self.agent_costs.get(agent_name, 0.0) + cost
            if task_id != "N/A":
                self.task_costs[task_id] = self.task_costs.get(task_id, 0.0) + cost
            if workflow_id != "N/A":
                self.workflow_costs[workflow_id] = self.workflow_costs.get(workflow_id, 0.0) + cost
            if request_id != "N/A":
                self.request_costs[request_id] = self.request_costs.get(request_id, 0.0) + cost

    def get_costs(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_system_cost_usd": self.total_cost,
                "cost_per_agent_usd": self.agent_costs,
                "cost_per_task_usd": self.task_costs,
                "cost_per_workflow_usd": self.workflow_costs,
                "cost_per_request_usd": self.request_costs
            }

    def get_tokens(self) -> Dict[str, Any]:
        with self._lock:
            total_prompt = sum(x["prompt_tokens"] for x in self.llm_calls)
            total_completion = sum(x["completion_tokens"] for x in self.llm_calls)
            total_tokens = sum(x["total_tokens"] for x in self.llm_calls)
            
            by_agent = {}
            by_task = {}
            by_workflow = {}
            by_session = {}
            for call in self.llm_calls:
                a = call["agent_name"]
                t = call["task_id"]
                w = call["workflow_id"]
                s = call.get("session_id", "N/A")
                if a != "N/A":
                    by_agent[a] = by_agent.get(a, 0) + call["total_tokens"]
                if t != "N/A":
                    by_task[t] = by_task.get(t, 0) + call["total_tokens"]
                if w != "N/A":
                    by_workflow[w] = by_workflow.get(w, 0) + call["total_tokens"]
                if s != "N/A":
                    by_session[s] = by_session.get(s, 0) + call["total_tokens"]

            return {
                "total_prompt_tokens": total_prompt,
                "total_completion_tokens": total_completion,
                "total_tokens": total_tokens,
                "tokens_by_agent": by_agent,
                "tokens_by_task": by_task,
                "tokens_by_workflow": by_workflow,
                "tokens_by_session": by_session,
                "llm_calls_count": len(self.llm_calls)
            }

    def get_performance(self) -> Dict[str, Any]:
        with self._lock:
            avg_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0.0
            
            p95 = 0.0
            if self.latencies:
                sorted_lat = sorted(self.latencies)
                idx = int(len(sorted_lat) * 0.95)
                p95 = sorted_lat[min(idx, len(sorted_lat) - 1)]
                
            avg_queue_wait = sum(self.queue_wait_times) / len(self.queue_wait_times) if self.queue_wait_times else 0.0
            
            avg_request_latency = sum(self.request_latencies) / len(self.request_latencies) if self.request_latencies else 0.0
            p95_request_latency = 0.0
            if self.request_latencies:
                sorted_req_lat = sorted(self.request_latencies)
                idx_req = int(len(sorted_req_lat) * 0.95)
                p95_request_latency = sorted_req_lat[min(idx_req, len(sorted_req_lat) - 1)]
                
            memory_usage_bytes = 0
            try:
                import psutil
                process = psutil.Process(os.getpid())
                memory_usage_bytes = process.memory_info().rss
            except Exception:
                pass
                
            active_workers = 0
            total_workers = 0
            try:
                from core.queue import worker_pool
                active_workers = sum(1 for w in worker_pool.get_status() if w.get("current_task") is not None)
                total_workers = len(worker_pool.workers)
            except Exception:
                pass
            worker_utilization = active_workers / total_workers if total_workers > 0 else 0.0
            
            return {
                "average_workflow_latency_seconds": avg_latency,
                "p95_workflow_latency_seconds": p95,
                "average_request_latency_seconds": avg_request_latency,
                "p95_request_latency_seconds": p95_request_latency,
                "average_queue_wait_time_seconds": avg_queue_wait,
                "worker_utilization_rate": worker_utilization,
                "memory_usage_bytes": memory_usage_bytes
            }

    def get_all_metrics(self) -> Dict[str, Any]:
        costs = self.get_costs()
        tokens = self.get_tokens()
        performance = self.get_performance()
        
        qsize = 0
        try:
            from core.queue import task_queue
            qsize = task_queue.qsize()
        except Exception:
            pass
            
        return {
            "requests_count": self.requests,
            "agent_executions_count": self.agent_executions,
            "workflow_executions_count": self.workflow_executions,
            "tool_executions_count": self.tool_executions,
            "queue_size": qsize,
            "retries_count": self.retries,
            "failures_count": self.failures,
            "costs": costs,
            "tokens": tokens,
            "performance": performance,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        }

    def clear(self) -> None:
        with self._lock:
            self.requests = 0
            self.agent_executions = 0
            self.workflow_executions = 0
            self.tool_executions = 0
            self.retries = 0
            self.failures = 0
            self.llm_calls.clear()
            self.total_cost = 0.0
            self.agent_costs.clear()
            self.task_costs.clear()
            self.workflow_costs.clear()
            self.request_costs.clear()
            self.latencies.clear()
            self.queue_wait_times.clear()
            self.request_latencies.clear()

metrics_collector = MetricsCollector()
