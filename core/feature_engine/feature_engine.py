import time
import uuid
from typing import Dict, Any, List, Optional
from core.knowledge.engine import InMemoryGraphEngine
from core.debate.debate_engine import DebateEngine
from core.autonomous_execution.rollback_manager import RollbackManager
from core.feature_engine.feature_parser import FeatureParser, FeatureSpec
from core.feature_engine.feature_planner import FeaturePlanner, FeatureExecutionPlan
from core.feature_engine.feature_architect import FeatureArchitect
from core.feature_engine.feature_builder import FeatureBuilder
from core.feature_engine.migration_manager import MigrationManager
from core.feature_engine.feature_validator import FeatureValidator
from core.feature_engine.feature_memory import FeatureMemory, FeatureRecord

class AutonomousFeatureEngine:
    """
    Core coordinator of the Autonomous Feature Development Engine (AFDE).
    Pipeline: Natural Language Goal -> Parsing -> KG Traversal -> Fit Checks -> Debate -> Plan -> Build -> Verify -> Log.
    """
    def __init__(self, graph: Optional[InMemoryGraphEngine] = None):
        self.graph = graph or InMemoryGraphEngine()
        self.parser = FeatureParser()
        self.planner = FeaturePlanner()
        self.architect = FeatureArchitect()
        self.builder = FeatureBuilder()
        self.migration_mgr = MigrationManager()
        self.validator = FeatureValidator(self.graph)
        self.rollback_mgr = RollbackManager(self.graph)
        self.debate_engine = DebateEngine()
        self.memory = FeatureMemory()

    def develop_feature(self, requirement: str, apply_feature_fn: Optional[Any] = None) -> Dict[str, Any]:
        t_start = time.perf_counter()
        execution_id = str(uuid.uuid4())

        # 1. Feature Parsing
        spec = self.parser.parse_requirement(requirement)

        # 2. Architectural Checks
        arch_analysis = self.architect.analyze_architecture_fit(spec)

        # 3. Multi-Agent Debate
        debate_res = self.debate_engine.run_debate({
            "requirement": requirement,
            "spec": spec.model_dump(),
            "architect_analysis": arch_analysis
        })

        # 4. Feature Planning
        plan = self.planner.create_plan(spec)

        # 5. Rollback Checkpoint
        self.rollback_mgr.create_checkpoint(plan.affected_files)

        success = True
        failures = None
        artifacts = {}

        try:
            # 6. Apply database schema migration
            migration_ver = f"migration_{execution_id[:8]}"
            db_script = "\n".join(plan.database_migration_steps)
            rollback_script = f"-- rollback {migration_ver}"
            mig_ok = self.migration_mgr.apply_migration(migration_ver, db_script, rollback_script)

            if not mig_ok:
                raise RuntimeError("Database migration execution failed.")

            # 7. Apply feature modifications
            artifacts = self.builder.build_feature(spec, plan)
            if apply_feature_fn:
                apply_feature_fn(artifacts)

            # 8. Post-Execution Validation
            val_res = self.validator.validate_feature(plan.affected_files)
            if not val_res["success"]:
                raise RuntimeError(f"Validation constraints failed: {val_res['results']}")
        except Exception as e:
            success = False
            failures = str(e)
            # Trigger rollback actions
            self.rollback_mgr.rollback()
            self.migration_mgr.rollback_migration(migration_ver)

        duration = time.perf_counter() - t_start

        # 9. Save details in Learning Memory
        record = FeatureRecord(
            id=execution_id,
            feature_name=requirement,
            execution_duration_seconds=duration,
            files_modified=plan.affected_files,
            success_rate=1.0 if success else 0.0,
            confidence=plan.confidence,
            lessons_learned=[
                f"Successfully implemented {requirement}." if success else f"Failed to build {requirement}: {failures}"
            ]
        )
        self.memory.add_record(record)

        return {
            "execution_id": execution_id,
            "requirement": requirement,
            "success": success,
            "failures": failures,
            "duration_s": duration,
            "plan": plan.model_dump(),
            "architect_analysis": arch_analysis,
            "debate": debate_res,
            "artifacts": artifacts
        }
