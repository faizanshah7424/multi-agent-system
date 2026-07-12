import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class LatencyBreakdown(BaseModel):
    planning: float = Field(default=0.0)
    execution: float = Field(default=0.0)
    repair: float = Field(default=0.0)
    consensus: float = Field(default=0.0)
    memory_lookup: float = Field(default=0.0)

class RunMetrics(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    task_id: str
    success: bool
    latencies: LatencyBreakdown
    tokens_used: int = Field(default=0)
    cost_usd: float = Field(default=0.0)

class MetricsCollector:
    """
    Subsystem gathering run latencies, token counters, costs, and success profiles.
    Persists data in a local JSON database database catalog history.
    """
    def __init__(self, persist_path: str = "data/metrics_history.json") -> None:
        self.persist_path = Path(persist_path)
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        self.runs = self._load_history()

    def _load_history(self) -> List[RunMetrics]:
        if not self.persist_path.exists():
            return []
        try:
            with open(self.persist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [RunMetrics.model_validate(item) for item in data]
        except Exception:
            return []

    def record_run(self, run: RunMetrics) -> None:
        """Records a new execution run in the history log."""
        self.runs.append(run)
        self._save_history()

    def _save_history(self) -> None:
        try:
            with open(self.persist_path, "w", encoding="utf-8") as f:
                json.dump([run.model_dump() for run in self.runs], f, indent=2)
        except Exception:
            pass

    def get_summary(self) -> Dict[str, Any]:
        """Calculates success rates, average costs, and mean latencies across all historical run data."""
        if not self.runs:
            return {
                "total_runs": 0,
                "success_rate": 0.0,
                "avg_cost_usd": 0.0,
                "avg_planning_s": 0.0,
                "avg_execution_s": 0.0,
                "avg_consensus_s": 0.0
            }
            
        total = len(self.runs)
        successes = sum(1 for r in self.runs if r.success)
        avg_cost = sum(r.cost_usd for r in self.runs) / total
        
        avg_plan = sum(r.latencies.planning for r in self.runs) / total
        avg_exec = sum(r.latencies.execution for r in self.runs) / total
        avg_con = sum(r.latencies.consensus for r in self.runs) / total
        
        return {
            "total_runs": total,
            "success_rate": (successes / total) * 100.0,
            "avg_cost_usd": avg_cost,
            "avg_planning_s": avg_plan,
            "avg_execution_s": avg_exec,
            "avg_consensus_s": avg_con
        }
