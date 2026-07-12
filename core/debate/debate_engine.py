import uuid
from core.debate.consensus_engine import ConsensusEngine


class DebateEngine:
    """
    Moderator engine simulating round-robin critiques between different personas.
    Wraps the new ConsensusEngine to orchestrate real agent collaboration and EDR generation.
    """

    def run_debate(self, context: dict) -> dict:
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        goal = (
            context.get("goal")
            or context.get("requirement")
            or context.get("idea")
            or "General Task Execution"
        )

        # Instantiate and run ConsensusEngine
        engine = ConsensusEngine()
        res = engine.run_consensus(task_id, goal)

        return {
            "consensus": res["status"],
            "edr": res["edr"],
            "code_proposal": res["code_proposal"],
            "plan": res["plan"],
        }
