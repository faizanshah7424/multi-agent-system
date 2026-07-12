# CodeOrbit AI — First-Run & Onboarding Walkthrough

Welcome to **CodeOrbit AI**! This guide is designed to help you set up, install, verify, and run your first multi-agent workflow in less than five minutes.

---

## 🏁 Step-by-Step Onboarding Walkthrough

### Step 1: Clone the Repository & Configure venv
Clone the project files and create a clean Python virtual environment boundaries:
```bash
git clone https://github.com/faizanshah7424/multi-agent-system.git
cd multi-agent-system

python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

---

### Step 2: Install Package Dependencies
Install the required execution packages:
```bash
pip install -r requirements.txt
```

---

### Step 3: Run the Environment Installer
Verify that all system requirements (Python, Git, Docker, Node, npm, SQLite, database, and folders permissions) are present:
```bash
python codeorbit.py install
```
*If everything is correctly configured, you will receive a success status:*
```text
Ready to build with CodeOrbit AI
```

---

### Step 4: Configure the Environment Variables
Create a local `.env` configuration file:
```bash
# On Windows PowerShell:
Copy-Item .env.example .env
# On macOS/Linux:
cp .env.example .env
```
Open `.env` and paste your Google Gemini API credential token:
```ini
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere
```

---

### Step 5: Run Platform Diagnostics
Verify configuration files and SQLite connection health:
```bash
python codeorbit.py doctor
```
Ensure that the final line prints: `Overall Diagnostic Status: HEALTHY`.

---

### Step 6: Test Drive with the E2E Demo Simulation
To see CodeOrbit AI's multi-agent swarm pipeline (Scan → Plan → Consensus → Execute → Self-Heal → Review → Merge → Complete) in action, run the simulated workflow command:
```bash
python codeorbit.py demo
```
This simulated run illustrates how the planning DAG, AST check parser, developer/reviewer/architect consensus voting, and self-healing repair loops interact.

---

### Step 7: Launch the API Server & Next.js Dashboard
1. **Start the FastAPI Backend**:
   ```bash
   python main.py
   ```
   *The REST API serves interactive OpenAPI documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).*

2. **Start the Next.js Dashboard**:
   In a separate terminal shell:
   ```bash
   cd dashboard
   npm install
   npm run dev
   ```
   *Access the web management panel at [http://localhost:3000](http://localhost:3000) to view real-time task queues and sandbox resource profilers.*

---

### Step 8: Trigger Your First Agent Workspace Task
With the server running and API key active, trigger a showcase task using the CLI:
```bash
python codeorbit.py run examples/python-cli
```
This runs the pre-configured end-to-end showcase run, registering execution logs in the SQLite database and transmitting telemetries to the live dashboard dashboard.
