import re
from typing import List, Optional, Protocol
from pydantic import BaseModel, Field
from core.logging import get_logger
from core.queue.scheduler import PlanStep
from core.sandbox.interface import ISandbox
from core.di import DIContainer
from core.queue.execution_runtime import IAgentExecutor

logger = get_logger("SelfHealingEngine")

class ParsedFailure(BaseModel):
    """
    Structured representation of a build/test/lint failure.
    """
    category: str = Field(..., description="Failure category (e.g. SYNTAX_ERROR, IMPORT_ERROR, TYPE_ERROR, LINT_ERROR, UNIT_TEST_FAILURE, MISSING_DEPENDENCY)")
    file_path: Optional[str] = Field(default=None, description="Path to the file containing the error.")
    line_number: Optional[int] = Field(default=None, description="Line number of the error.")
    column_number: Optional[int] = Field(default=None, description="Column number of the error.")
    message: str = Field(..., description="Raw error message description.")
    probable_root_cause: str = Field(..., description="Probable root cause analysis.")

class ISelfHealingEngine(Protocol):
    """
    Interface orchestrating log parsing, classification, linter/test validation,
    and agent-driven code repair iteration loops.
    """
    def repair_failure(self, task_id: str, step: PlanStep, error_log: str, workspace_path: str, sandbox: ISandbox) -> bool:
        """
        Runs the self-healing repair loop. Returns True if successfully repaired and validated.
        """
        ...

class SelfHealingEngine(ISelfHealingEngine):
    """
    Disciplined engineering repair loop that diagnoses errors, coordinates agent repairs,
    and validates outcomes up to 3 times.
    """
    def __init__(self) -> None:
        pass

    def repair_failure(self, task_id: str, step: PlanStep, error_log: str, workspace_path: str, sandbox: ISandbox) -> bool:
        """
        Diagnoses failures, invokes agent repairs, and re-validates.
        """
        logger.info(f"Self-healing triggered for Step {step.step_id} (Task: {task_id})")
        
        # 1. Parse and classify failure
        failure = self.classify_failure(error_log)
        if not failure:
            logger.warning("Log parsing yielded no recognizable failure pattern. Aborting repair.")
            return False

        logger.info(
            f"Classified failure: {failure.category} in file {failure.file_path} "
            f"at line {failure.line_number}. Probable Root Cause: {failure.probable_root_cause}"
        )

        # 2. Enforce safety checks (Never edit tests)
        if failure.file_path and ("test_" in failure.file_path or "tests/" in failure.file_path):
            logger.error(f"Safety Gate Violation: Self-healing blocked editing test file: {failure.file_path}")
            return False

        # Retrieve similar fixes from EME (Engineering Memory Engine)
        try:
            memory_engine = DIContainer.get("memory_engine")
            similar_fixes = memory_engine.retrieve_similar_fixes(error_log, limit=2)
        except Exception:
            memory_engine = None
            similar_fixes = []

        history_context = ""
        if similar_fixes:
            history_context = "\n\nRELEVANT PAST FIXES FOUND IN MEMORY ENGINE (EME):\n"
            for idx, fix in enumerate(similar_fixes):
                history_context += (
                    f"Past Fix {idx+1}:\n"
                    f"- File: {fix['file_path']}\n"
                    f"- Error matched: {fix['error_msg']}\n"
                    f"- Applied Fix: {fix['applied_fix']}\n"
                )

        # 3. Iterate repair attempts up to 3 times
        max_attempts = 3
        agent_executor = DIContainer.get(IAgentExecutor)

        for attempt in range(1, max_attempts + 1):
            logger.info(f"Self-healing repair attempt {attempt} of {max_attempts}...")
            
            # Format evidence-driven instructions for Developer Agent
            repair_description = (
                f"REPAIR ATTEMPT {attempt}:\n"
                f"The build/test command failed with a {failure.category}.\n"
                f"Target File: {failure.file_path}\n"
                f"Line Number: {failure.line_number}\n"
                f"Error Message: {failure.message}\n"
                f"Root Cause: {failure.probable_root_cause}\n"
                f"Please correct the error in {failure.file_path} immediately. "
                f"Do not edit test files. Do not disable linter checks or warnings."
                f"{history_context}"
            )
            
            repair_step = PlanStep(
                step_id=step.step_id,
                dependencies=step.dependencies,
                assigned_agent=step.assigned_agent,
                description=repair_description,
                files=[failure.file_path] if failure.file_path else step.files
            )

            # Trigger agent execution to modify code
            agent_success = agent_executor.execute_step(task_id, repair_step, workspace_path, sandbox)
            if not agent_success:
                logger.warning(f"Agent failed to apply repair on attempt {attempt}.")
                continue

            # 4. Re-run validation checks (Ruff, Pytest)
            logger.info(f"Validating repair attempt {attempt}...")
            validation_success = self.validate_workspace(sandbox)
            if validation_success:
                logger.info(f"Self-healing succeeded on attempt {attempt}!")
                
                # Record successful repair in EME database
                if memory_engine:
                    try:
                        memory_engine.record_fix(
                            task_id=task_id,
                            step_id=step.step_id,
                            file_path=failure.file_path or "unknown.py",
                            error_msg=error_log,
                            applied_fix=f"Fixed {failure.category} at line {failure.line_number} on attempt {attempt}."
                        )
                    except Exception as e:
                        logger.warning(f"Failed to record fix in EME: {e}")
                        
                return True
            else:
                logger.warning(f"Validation failed after repair attempt {attempt}.")
                
        logger.error(f"Self-healing failed to repair step {step.step_id} after {max_attempts} attempts.")
        return False

    def classify_failure(self, error_log: str) -> Optional[ParsedFailure]:
        """
        Inspects logs via sequential regex filters to categorize failures.
        """
        # A. Python traceback parser
        tb_match = re.search(r'File "([^"]+)", line (\d+)(?:, in (\w+))?\n\s*(.*?)\n(\w+Error|SyntaxError|NameError|ImportError|TypeError|ValueError): (.*)', error_log, re.DOTALL)
        if tb_match:
            file_path, line_no, func, line_code, err_name, err_msg = tb_match.groups()
            
            category = "SYNTAX_ERROR" if err_name == "SyntaxError" else "TYPE_ERROR"
            if err_name in ["ImportError", "ModuleNotFoundError"]:
                category = "IMPORT_ERROR"
            elif "dependency" in err_msg.lower() or "missing" in err_msg.lower():
                category = "MISSING_DEPENDENCY"
                
            return ParsedFailure(
                category=category,
                file_path=file_path,
                line_number=int(line_no),
                message=f"{err_name}: {err_msg.strip()}",
                probable_root_cause=f"Python execution failed with {err_name} in function {func or 'global'}."
            )

        # B. Ruff linter parser
        ruff_match = re.search(r'([^\s:]+\.py):(\d+):(\d+): ([A-Z]\d+) (.*)', error_log)
        if ruff_match:
            file_path, line_no, col_no, code, msg = ruff_match.groups()
            return ParsedFailure(
                category="LINT_ERROR",
                file_path=file_path,
                line_number=int(line_no),
                column_number=int(col_no),
                message=f"Ruff {code}: {msg}",
                probable_root_cause="Linter rule violation detected."
            )

        # C. Pytest failure parser
        pytest_match = re.search(r'>\s*(.*?)\nE\s*(\w+Error|AssertionError): (.*?)\n\n([^\s:]+\.py):(\d+):', error_log, re.DOTALL)
        if pytest_match:
            line_code, err_name, msg, file_path, line_no = pytest_match.groups()
            return ParsedFailure(
                category="UNIT_TEST_FAILURE",
                file_path=file_path,
                line_number=int(line_no),
                message=f"{err_name}: {msg.strip()}",
                probable_root_cause=f"Assertion failed inside unit test at expression: {line_code.strip()}"
            )

        # D. TypeScript compiler parser
        tsc_match = re.search(r'([^\s:]+\.ts)\((\d+),(\d+)\): error (TS\d+): (.*)', error_log)
        if tsc_match:
            file_path, line_no, col_no, code, msg = tsc_match.groups()
            return ParsedFailure(
                category="TYPE_ERROR",
                file_path=file_path,
                line_number=int(line_no),
                column_number=int(col_no),
                message=f"TypeScript error {code}: {msg}",
                probable_root_cause="Type validation failed during compilation."
            )

        # E. ESLint parser
        eslint_match = re.search(r'([^\s:]+\.js): line (\d+), col (\d+), Error - (.*)', error_log)
        if eslint_match:
            file_path, line_no, col_no, msg = eslint_match.groups()
            return ParsedFailure(
                category="LINT_ERROR",
                file_path=file_path,
                line_number=int(line_no),
                column_number=int(col_no),
                message=f"ESLint: {msg}",
                probable_root_cause="ESLint linter rule violation."
            )

        # Fallback generic classifier
        if "syntax" in error_log.lower():
            return ParsedFailure(category="SYNTAX_ERROR", message="Syntax error found.", probable_root_cause="Unspecified syntax error.")
        if "test" in error_log.lower():
            return ParsedFailure(category="UNIT_TEST_FAILURE", message="Test run failed.", probable_root_cause="Unit test assertion crash.")

        return None

    def validate_workspace(self, sandbox: ISandbox) -> bool:
        """
        Validates repair by executing Ruff and unit tests (pytest).
        """
        # 1. Run Ruff linter
        res_lint = sandbox.execute(["ruff", "check", "."])
        if res_lint.exit_code != 0:
            logger.warning(f"Validation failed: Linter Ruff found errors: {res_lint.stderr}")
            return False

        # 2. Run unit tests
        res_test = sandbox.execute(["pytest"])
        if res_test.exit_code != 0:
            logger.warning(f"Validation failed: pytest unit tests failed: {res_test.stderr}")
            return False

        return True
