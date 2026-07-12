import sys
import uvicorn
from api.app import app
from config import settings
from agents.manager import ManagerAgent


def start_server() -> None:
    """
    Start the FastAPI web server using Uvicorn with values from config settings.
    """
    print(
        f"Hosting FastAPI web server on http://{settings.api_host}:{settings.api_port}"
    )
    uvicorn.run(
        "api.app:app", host=settings.api_host, port=settings.api_port, reload=False
    )


def run_cli(task: str) -> None:
    """
    Execute task in CLI mode.
    Outputs step-by-step logs and results to stdout.
    """
    print(f"Running in CLI Mode for task: '{task}'")
    manager = ManagerAgent(session_id="cli_session")
    result = manager.execute(task)

    print("\n" + "=" * 50)
    for key, value in result.items():
        if key in ["workflow_steps", "messages"]:
            # Skip verbose system keys in CLI prints
            continue
        print(f"\n{key.upper()}")
        print("-" * 50)
        print(value)


if __name__ == "__main__":
    # If task parameters are provided in terminal, run CLI mode.
    # E.g. python main.py "Build a FastAPI CRUD API"
    if len(sys.argv) > 1:
        task_str = " ".join(sys.argv[1:])
        run_cli(task_str)
    else:
        # Otherwise start the production API server
        start_server()
