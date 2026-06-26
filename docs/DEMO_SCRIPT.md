# Product Demonstration Script: Multi-Agent AI Platform

This script provides a 5-10 minute step-by-step guide for demonstrating the Multi-Agent AI Platform to recruiters, freelance clients, or interviewers. It covers dashboard navigation, task creation, multi-agent execution tracking, safety sandbox verification, and metrics monitoring.

---

## Demo Overview
* **Goal**: Show a task go from creation, planning, and multi-agent execution to final completion and metrics capture.
* **Duration**: 5 - 10 minutes.
* **Preparation**: Ensure containers are running:
  ```bash
  docker compose up -d
  ```

---

## Step 1: System & Dashboard Walkthrough (1-2 Mins)

### Action:
1. Open the Admin Dashboard in your browser: `http://localhost:3000/` (or your host port).
2. Point out the core layout.

### Speaking Points:
> *"Here is the Next.js 15 Web Dashboard for our Multi-Agent Platform. On the main landing page, we see our cluster-wide stats: total tasks registered, active queue size, and worker nodes currently online. Below that, we have our database activity graphs showing task claim speeds, execution times, and worker heartbeats."*

> *"In the **Workers** list, we see each worker thread register its process ID (PID), host name, status, and active task. This lets us monitor the processing pool in real-time."*

---

## Step 2: Task Creation & Queue Dispatch (1-2 Mins)

### Action:
1. Navigate to the **Create Task** form on the dashboard (or execute a curl command in a terminal).
2. Enter the task prompt:
   ```json
   "Write a Python script that calculates the first 10 Fibonacci numbers, runs it to verify output, and saves the results in a file named fibonacci.txt"
   ```
3. Submit the task.

### Speaking Points:
> *"Let's submit a complex, multi-step task. This prompt requires writing code, executing it, validating the results, and creating files. When I click submit, the FastAPI gateway creates a database record, pushes the task ID to the thread-safe queue, and returns a `PENDING` status in under 2 milliseconds."*

> *"The task is immediately picked up by an active background worker thread, which transitions the status to `RUNNING` transactionally."*

---

## Step 3: Multi-Agent Execution & Real-Time Logs (3 Mins)

### Action:
1. Navigate to the **Task Details / History** view on the dashboard.
2. Watch the log streams and agent messages update.

### Speaking Points:
> *"Now we are inside the execution details view. Here, we can watch our agents work collaboratively:"*
> 1. *"First, the **Planner Agent** takes the main task and decomposes it into a Directed Acyclic Graph (DAG) of dependencies. We see step 1 is writing the code, step 2 is running it, and step 3 is saving results."*
> 2. *"Next, the system runs a cycle-detection algorithm to ensure the plan is a valid Directed Acyclic Graph with no circular deadlocks. Once verified, the steps are registered in memory."*
> 3. *"The **Developer Agent** is triggered. It writes the script and updates the shared memory variables."*
> 4. *"The **Tool Agent** takes the code and runs it. It executes the script safely inside our AST Python sandbox."*
> 5. *"Finally, the **Writer Agent** takes the stdout and writes the results to `fibonacci.txt` within the permitted workspace folder."*

---

## Step 4: Safety & Sandbox Verification (1-2 Mins)

### Action:
1. Submit a malicious task design to demonstrate the safety features:
   ```json
   "Read the system secrets by running a Python script containing: import os; os.system('cat /etc/passwd')"
   ```
2. Navigate to the task page and watch it fail. Show the security logs.

### Speaking Points:
> *"One of the key engineering highlights of this platform is **Security Hardening**. Let's submit a malicious prompt trying to escape the workspace and read system secrets using `os.system`."*

> *"As we see, the task immediately fails. The system parsed the script into an Abstract Syntax Tree (AST) before running it, identified that the code attempts to import the banned `os` module, and terminated execution. The dashboard logs show: `SecurityError: Banned module os import detected`."*

> *"Additionally, if we look at our logs directory, the custom logger has redacted our Gemini API keys, demonstrating built-in credential scrubbing."*

---

## Step 5: Metrics & Monitoring Verification (1 Min)

### Action:
1. Open the API health and metrics endpoint in a browser: `http://localhost:8000/metrics` (or view metrics on dashboard charts).
2. Point out execution times and average queue delays.

### Speaking Points:
> *"Lastly, the platform exposes a `/metrics` health endpoint. This tracks our processing statistics: average queue wait time, agent run counts, and workflow success rates."*

> *"Our stress tests simulating load show the engine handles up to 859 task creations per second and processes 108 tasks/sec concurrently with high transaction resiliency, demonstrating the scalability of our SQLite WAL configuration."*

> *"This concludes the walkthrough. The platform is security-hardened, concurrent, fully containerized, and designed with production-readiness principles."*
