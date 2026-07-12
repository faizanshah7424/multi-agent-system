import os
import sys
import time
import uuid
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import init_db, get_db_session, Task
from core.repositories import TaskRepository


def run_load_test(num_tasks: int, num_workers: int):
    print(f"\n==========================================")
    print(f"Starting Load Test: {num_tasks} Tasks, {num_workers} Worker Threads")
    print(f"==========================================")

    # 1. Clean and initialize DB
    init_db()

    # 2. Measure Enqueue Latency
    start_enqueue = time.time()
    task_ids = [f"lt_{uuid.uuid4().hex[:8]}" for _ in range(num_tasks)]

    def enqueue_batch(batch_ids):
        with get_db_session() as session:
            repo = TaskRepository(session)
            for tid in batch_ids:
                repo.create_task(
                    task_id=tid,
                    payload={"task": "Simulated load test task"},
                    user_id="load_tester",
                )

    # Enqueue using a thread pool to simulate concurrent API requests
    batch_size = 50
    batches = [
        task_ids[i : i + batch_size] for i in range(0, len(task_ids), batch_size)
    ]

    print(f"Enqueuing {num_tasks} tasks concurrently in batches of {batch_size}...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(enqueue_batch, b) for b in batches]
        for f in as_completed(futures):
            f.result()

    enqueue_duration = time.time() - start_enqueue
    print(f"Successfully enqueued {num_tasks} tasks in {enqueue_duration:.2f} seconds.")
    print(f"Average enqueue speed: {num_tasks / enqueue_duration:.2f} tasks/sec.")
    print(
        f"Average latency per enqueue: {(enqueue_duration / num_tasks) * 1000:.2f} ms."
    )

    # 3. Simulate Worker Processing
    # We will simulate W concurrent workers claiming and executing tasks.
    # To simulate task execution, the worker will:
    #   - Claim task (transition status to RUNNING in database)
    #   - Sleep for a random interval (0.01 to 0.05 seconds) to simulate computation
    #   - Complete task (transition status to COMPLETED in database)
    # If a database lock occurs, we count it as a conflict/error.

    conflicts = 0
    completed_count = 0
    lock = threading.Lock()

    start_processing = time.time()

    def worker_loop(worker_id):
        nonlocal conflicts, completed_count
        local_completed = 0
        local_conflicts = 0

        while True:
            # Try to claim a task
            task_id = None
            try:
                with get_db_session() as session:
                    repo = TaskRepository(session)
                    db_task = repo.claim_task(f"sim_worker_{worker_id}")
                    if db_task:
                        task_id = db_task.task_id
            except Exception as e:
                local_conflicts += 1
                time.sleep(0.01)  # Backoff on SQLite locks
                continue

            if not task_id:
                # No tasks left
                break

            # Simulate task execution work
            time.sleep(random.uniform(0.01, 0.05))

            # Update task to COMPLETED
            try:
                with get_db_session() as session:
                    repo = TaskRepository(session)
                    db_task = repo.get_task(task_id)
                    if db_task:
                        db_task.status = "COMPLETED"
                        db_task.completed_at = datetime.now(timezone.utc).replace(
                            tzinfo=None
                        )
                        repo.save_task(db_task)
                local_completed += 1
            except Exception as e:
                local_conflicts += 1

        with lock:
            completed_count += local_completed
            conflicts += local_conflicts

    print(f"Simulating task execution with {num_workers} concurrent threads...")
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(worker_loop, i) for i in range(num_workers)]
        for f in as_completed(futures):
            f.result()

    processing_duration = time.time() - start_processing
    print(f"Processing complete.")
    print(f"Total time to process: {processing_duration:.2f} seconds.")
    print(f"Throughput: {completed_count / processing_duration:.2f} tasks/sec.")
    print(f"Database lock conflicts encountered: {conflicts}")

    # Return metrics
    return {
        "num_tasks": num_tasks,
        "enqueue_duration": enqueue_duration,
        "enqueue_tps": num_tasks / enqueue_duration,
        "processing_duration": processing_duration,
        "processing_tps": completed_count / processing_duration,
        "conflicts": conflicts,
    }


if __name__ == "__main__":
    # Run load tests for 100, 500, and 1000 tasks
    results = {}
    results[100] = run_load_test(100, 4)
    results[500] = run_load_test(500, 8)
    results[1000] = run_load_test(1000, 16)

    print("\n" + "=" * 50)
    print("LOAD TEST FINAL SUMMARY")
    print("=" * 50)
    for tasks, res in results.items():
        print(
            f"\n{tasks} Tasks (Workers: {tasks // 100 or 4 if tasks < 500 else 10 if tasks < 1000 else 16})"
        )
        print(f"  Enqueue TPS   : {res['enqueue_tps']:.2f} tasks/sec")
        print(f"  Processing TPS: {res['processing_tps']:.2f} tasks/sec")
        print(f"  Conflict count: {res['conflicts']}")
