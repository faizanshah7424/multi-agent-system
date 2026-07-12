import time
import uuid
from typing import Dict, Any, List, Optional
from core.knowledge.engine import InMemoryGraphEngine
from core.debate.debate_engine import DebateEngine
from core.autonomous_execution.rollback_manager import RollbackManager
from core.feature_engine.migration_manager import MigrationManager
from core.autonomous_repository.repository_context import (
    RepositoryContextDetector,
    RepositoryContext,
)
from core.autonomous_repository.repository_planner import (
    RepositoryPlanner,
    RepositoryTaskPlan,
)
from core.autonomous_repository.repository_executor import RepositoryExecutor
from core.autonomous_repository.repository_validator import RepositoryValidator
from core.autonomous_repository.repository_memory import (
    RepositoryMemory,
    RepositoryRecord,
)
from core.autonomous_repository.repository_history import RepositoryHistory
from core.autonomous_repository.repository_report import RepositoryReportGenerator


class AutonomousRepositoryEngine:
    """
    Main orchestrator of the Autonomous Repository Engineer (ARE).
    Pipeline: Goal -> Auto-Scan -> planning specs -> Traversal -> Debate -> backups -> Code Gen -> Verification -> Log.
    """

    def __init__(self, graph: Optional[InMemoryGraphEngine] = None):
        self.graph = graph or InMemoryGraphEngine()
        self.detector = RepositoryContextDetector()
        self.planner = RepositoryPlanner()
        self.executor = RepositoryExecutor(self.graph)
        self.validator = RepositoryValidator(self.graph)
        self.rollback_mgr = RollbackManager(self.graph)
        self.migration_mgr = MigrationManager()
        self.debate_engine = DebateEngine()
        self.memory = RepositoryMemory()
        self.history = RepositoryHistory(self.memory)
        self.report_gen = RepositoryReportGenerator()

    def run_repository_engineering(
        self, goal: str, apply_changes_fn: Optional[Any] = None
    ) -> Dict[str, Any]:
        t_start = time.perf_counter()
        execution_id = str(uuid.uuid4())

        # 1. Automatic Context Scanning
        context = self.detector.build_context()

        # 2. Plan Generation
        plan = self.planner.create_plan(goal, context)

        # 3. Impact Analysis & Traversal
        impact = self.executor.run_impact_analysis(plan)

        # 4. Multi-Agent Debate Consensus
        debate_res = self.debate_engine.run_debate(
            {
                "goal": goal,
                "context": context.model_dump(),
                "plan": plan.model_dump(),
                "impact": impact,
            }
        )

        # 5. Checkpoint Backups
        self.rollback_mgr.create_checkpoint(impact["affected_files"])

        success = True
        failures = None
        artifacts = {}
        reports_paths = {}

        try:
            # 6. Schema Migration Execution
            migration_ver = f"repo_mig_{execution_id[:8]}"
            db_script = "\n".join(
                [f"-- migration: {change}" for change in plan.database_changes]
            )
            rollback_script = f"-- rollback {migration_ver}"
            mig_ok = self.migration_mgr.apply_migration(
                migration_ver, db_script, rollback_script
            )
            if not mig_ok:
                raise RuntimeError("Repository DB schema migration failed.")

            # 7. Code Generation & Execution
            artifacts = self.executor.generate_code_artifacts(plan)
            if apply_changes_fn:
                apply_changes_fn(artifacts)

            # 8. Post-Execution Validation
            val_res = self.validator.validate_repository(impact["affected_files"])
            if not val_res["success"]:
                raise RuntimeError(
                    f"Repository validation failed: {val_res['results']}"
                )

            # 9. Documentation Reports Generation
            reports_paths = self.report_gen.generate_all_reports(
                goal, plan.model_dump(), val_res
            )
        except Exception as e:
            success = False
            failures = str(e)
            # Revert files and schemas
            self.rollback_mgr.rollback()
            self.migration_mgr.rollback_migration(migration_ver)

        duration = time.perf_counter() - t_start

        # 10. Persist Job details to Memory
        record = RepositoryRecord(
            id=execution_id,
            goal=goal,
            repo_snapshot={
                "tests_count": len(context.tests),
                "api_endpoints_count": len(context.api_endpoints),
            },
            generated_files=impact["affected_files"],
            confidence=plan.confidence,
            validation_results={"success": success, "failures": failures},
            rollback_snapshot=f"git_reset_{execution_id[:8]}",
            execution_duration_seconds=duration,
        )
        self.memory.add_record(record)

        return {
            "execution_id": execution_id,
            "goal": goal,
            "success": success,
            "failures": failures,
            "duration_s": duration,
            "context": context.model_dump(),
            "plan": plan.model_dump(),
            "impact": impact,
            "debate": debate_res,
            "artifacts": artifacts,
            "reports": reports_paths,
        }
