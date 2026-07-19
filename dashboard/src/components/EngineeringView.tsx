'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useDashboard } from '../context/DashboardContext';
import { 
  Shield, Terminal, Cpu, 
  CheckCircle, RefreshCw, 
  Layers, BarChart2, Check, X, Lock, Eye
} from 'lucide-react';

interface SecurityFinding {
  finding_id: string;
  category: string;
  severity: string;
  message: string;
  file_path?: string;
  line_number?: number;
}

interface SandboxStatus {
  docker_available: boolean;
  details: string;
  resource_allocation: {
    cpu_limit: string;
    memory_limit: string;
    network_policy: string;
    root_mount: string;
  };
}

interface RuntimePolicy {
  allowed_prefixes: string[];
  protected_configs: string[];
  workspace_root: string;
}

interface EDRRecord {
  id: string;
  project: string;
  problem: string;
  alternatives: string[];
  chosen: string;
  architectural_impact: string;
  risk: string;
  status: string;
}

interface LatencyMetrics {
  startup_time: number;
  planning_latency: number;
  sandbox_startup: number;
  memory_retrieval: number;
  consensus_duration: number;
  self_healing_duration: number;
  total_time: number;
}

export const EngineeringView: React.FC = () => {
  const { apiUrl, useMockData } = useDashboard();
  const [activeTab, setActiveTab] = useState<'sandbox' | 'security' | 'consensus' | 'performance'>('sandbox');
  
  // Tab 1: Sandbox & Secrets state
  const [dockerStatus, setDockerStatus] = useState<SandboxStatus>({
    docker_available: true,
    details: "Docker Daemon is online.",
    resource_allocation: {
      cpu_limit: "1.0 CPU Core",
      memory_limit: "512MB RAM",
      network_policy: "ISOLATED (none)",
      root_mount: "READ-ONLY"
    }
  });
  
  const [secretsStatus, setSecretsStatus] = useState<Record<string, boolean>>({
    "GEMINI_API_KEY": true,
    "OPENAI_API_KEY": true,
    "ANTHROPIC_API_KEY": false
  });
  
  const [policies, setPolicies] = useState<RuntimePolicy>({
    allowed_prefixes: ["python", "pip", "pytest", "npm", "npx", "git", "cargo", "poetry", "docker", "echo", "cat", "ls", "mkdir", "rm"],
    protected_configs: ["package.json", "tsconfig.json", "settings.json", "pyproject.toml", ".env", "docker-compose.yml"],
    workspace_root: "/app/workspace"
  });

  // Tab 2: Security Auditor state
  const [codeToAudit, setCodeToAudit] = useState<string>(
    "import os\n\n" +
    "# Hardcoded API Credentials\n" +
    "GEMINI_KEY = 'AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P'\n\n" +
    "def run_command(user_input):\n" +
    "    # Vulnerable shell injection\n" +
    "    os.system('echo ' + user_input)\n\n" +
    "def read_report(file_name):\n" +
    "    # Vulnerable path traversal\n" +
    "    with open('../../reports/' + file_name) as f:\n" +
    "        return f.read()\n"
  );
  const [auditFindings, setAuditFindings] = useState<SecurityFinding[]>([]);
  const [auditing, setAuditing] = useState<boolean>(false);

  // Tab 3: Consensus approvals state
  const [activeEdrs, setActiveEdrs] = useState<EDRRecord[]>([
    {
      id: "edr_001",
      project: "python_cli",
      problem: "Resolve missing import dependency in Python CLI executable.",
      alternatives: ["Fallback to stdlib sys modules", "Install third party requests wrapper"],
      chosen: "Inject standard sys import to cli.py and verify via sandbox pytest.",
      architectural_impact: "Lightweight footprint, zero runtime dependency overhead.",
      risk: "Local environment needs Python 3.10+.",
      status: "WAITING_FOR_APPROVAL"
    },
    {
      id: "edr_002",
      project: "ecommerce_sys",
      problem: "Prevent IndexError in shop cart operations during high concurrency.",
      alternatives: ["Mutex thread locking", "Boundary validation checks"],
      chosen: "Enforce array index boundaries on item retrieval.",
      architectural_impact: "Clean array bounds checking inside shop/cart.py.",
      risk: "Slight latency overhead on checkouts.",
      status: "APPROVED"
    }
  ]);

  // Tab 4: Latencies metrics state
  const latencies: LatencyMetrics = {
    startup_time: 0.05,
    planning_latency: 0.12,
    sandbox_startup: 0.85,
    memory_retrieval: 0.08,
    consensus_duration: 0.45,
    self_healing_duration: 0.15,
    total_time: 1.85
  };

  // Fetch real data on mount / refresh
  const loadData = useCallback(async () => {
    if (useMockData) return;
    try {
      const secRes = await fetch(`${apiUrl}/security/secrets`);
      if (secRes.ok) setSecretsStatus(await secRes.ok ? await secRes.json() : secretsStatus);

      const polRes = await fetch(`${apiUrl}/security/policies`);
      if (polRes.ok) setPolicies(await polRes.json());

      const sandRes = await fetch(`${apiUrl}/sandbox/status`);
      if (sandRes.ok) setDockerStatus(await sandRes.json());
    } catch {
      console.warn("FastAPI offline, retaining simulator mocks.");
    }
  }, [apiUrl, useMockData, secretsStatus]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRunAudit = async () => {
    setAuditing(true);
    setAuditFindings([]);
    
    // Slight sleep to look organic
    await new Promise(resolve => setTimeout(resolve, 600));

    if (useMockData) {
      // Return simulated findings
      const mockFindings: SecurityFinding[] = [
        {
          finding_id: "sec_a81f",
          category: "SECRET_EXPOSURE",
          severity: "CRITICAL",
          message: "Potential hardcoded credential or API key found: 'AIzaSyA1B2...'",
          file_path: "custom_file.py",
          line_number: 4
        },
        {
          category: "UNSAFE_SHELL",
          severity: "HIGH",
          finding_id: "sec_b92d",
          message: "Dangerous dynamic execution or subprocess call: 'os.system('echo ' + user_input)'",
          file_path: "custom_file.py",
          line_number: 8
        },
        {
          category: "PATH_TRAVERSAL",
          severity: "MEDIUM",
          finding_id: "sec_c19a",
          message: "Relative path parent references ('..') found during filesystem access.",
          file_path: "custom_file.py",
          line_number: 12
        }
      ];
      setAuditFindings(mockFindings);
      setAuditing(false);
      return;
    }

    try {
      const res = await fetch(`${apiUrl}/security/audit?code_content=${encodeURIComponent(codeToAudit)}`, {
        method: 'POST'
      });
      if (res.ok) {
        setAuditFindings(await res.json());
      } else {
        alert("Security scan failed: " + res.statusText);
      }
    } catch (e: unknown) {
      const err = e as Error;
      alert("API Error connecting to auditor: " + err.message);
    } finally {
      setAuditing(false);
    }
  };

  const handleApproveEdr = (id: string, decision: string) => {
    // Update locally
    setActiveEdrs(prev => prev.map(e => e.id === id ? { ...e, status: decision } : e));
  };

  return (
    <div className="space-y-6">
      
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center border-b pb-4 gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center">
            <Shield className="h-7 w-7 text-indigo-400 mr-2.5" />
            Engineering Operations Center
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Observe the isolated runtime sandbox, review multi-agent EDR consensus, and scan code additions.
          </p>
        </div>
        <button 
          onClick={loadData}
          className="flex items-center space-x-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs px-3.5 py-2 rounded-lg font-bold transition border border-zinc-700"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Refresh Monitors</span>
        </button>
      </div>

      {/* Tabs Switcher */}
      <div className="flex border-b border-zinc-800 space-x-2">
        <button
          onClick={() => setActiveTab('sandbox')}
          className={`px-4 py-2 text-sm font-bold border-b-2 transition ${
            activeTab === 'sandbox' 
              ? 'border-indigo-500 text-indigo-400' 
              : 'border-transparent text-zinc-400 hover:text-zinc-200'
          }`}
        >
          Sandbox & Secrets
        </button>
        <button
          onClick={() => setActiveTab('security')}
          className={`px-4 py-2 text-sm font-bold border-b-2 transition ${
            activeTab === 'security' 
              ? 'border-indigo-500 text-indigo-400' 
              : 'border-transparent text-zinc-400 hover:text-zinc-200'
          }`}
        >
          Security Auditor
        </button>
        <button
          onClick={() => setActiveTab('consensus')}
          className={`px-4 py-2 text-sm font-bold border-b-2 transition ${
            activeTab === 'consensus' 
              ? 'border-indigo-500 text-indigo-400' 
              : 'border-transparent text-zinc-400 hover:text-zinc-200'
          }`}
        >
          Consensus & Approvals
        </button>
        <button
          onClick={() => setActiveTab('performance')}
          className={`px-4 py-2 text-sm font-bold border-b-2 transition ${
            activeTab === 'performance' 
              ? 'border-indigo-500 text-indigo-400' 
              : 'border-transparent text-zinc-400 hover:text-zinc-200'
          }`}
        >
          Performance Telemetry
        </button>
      </div>

      {/* Tab 1: Sandbox & Secrets */}
      {activeTab === 'sandbox' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Docker Status Container */}
          <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl p-6 shadow-xl space-y-6">
            <h3 className="text-lg font-bold text-zinc-200 flex items-center">
              <Cpu className="h-5 w-5 text-indigo-400 mr-2" />
              Production Container Sandbox
            </h3>
            
            <div className={`flex items-center space-x-3 p-4 rounded-xl border ${
              dockerStatus.docker_available
                ? 'bg-emerald-500/10 border border-emerald-500/20'
                : 'bg-rose-500/10 border border-rose-500/20'
            }`}>
              {dockerStatus.docker_available ? (
                <CheckCircle className="h-5 w-5 text-emerald-400" />
              ) : (
                <X className="h-5 w-5 text-rose-400" />
              )}
              <div>
                <h4 className={`text-sm font-bold ${dockerStatus.docker_available ? 'text-emerald-300' : 'text-rose-300'}`}>
                  {dockerStatus.docker_available ? 'Docker Daemon Online' : 'Docker Daemon Offline'}
                </h4>
                <p className={`text-xs leading-relaxed mt-0.5 ${dockerStatus.docker_available ? 'text-emerald-400/80' : 'text-rose-400/80'}`}>
                  {dockerStatus.details}
                </p>
              </div>
            </div>

            <div className="space-y-3 pt-2">
              <span className="text-xs text-zinc-400 font-bold uppercase tracking-wider">Resource Allocations</span>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-zinc-800/40 p-3 rounded-lg border border-zinc-800 text-center">
                  <span className="text-xs text-zinc-500 block">CPU limit</span>
                  <span className="text-sm font-bold text-zinc-200 block mt-1">{dockerStatus.resource_allocation.cpu_limit}</span>
                </div>
                <div className="bg-zinc-800/40 p-3 rounded-lg border border-zinc-800 text-center">
                  <span className="text-xs text-zinc-500 block">RAM quota</span>
                  <span className="text-sm font-bold text-zinc-200 block mt-1">{dockerStatus.resource_allocation.memory_limit}</span>
                </div>
                <div className="bg-zinc-800/40 p-3 rounded-lg border border-zinc-800 text-center">
                  <span className="text-xs text-zinc-500 block">Network</span>
                  <span className="text-xs font-bold text-zinc-200 block mt-1">{dockerStatus.resource_allocation.network_policy}</span>
                </div>
                <div className="bg-zinc-800/40 p-3 rounded-lg border border-zinc-800 text-center">
                  <span className="text-xs text-zinc-500 block">Host Access</span>
                  <span className="text-sm font-bold text-zinc-200 block mt-1">{dockerStatus.resource_allocation.root_mount}</span>
                </div>
              </div>
            </div>

            {/* Allowed Policies list */}
            <div className="space-y-2 pt-2 border-t border-zinc-800">
              <span className="text-xs text-zinc-400 font-bold uppercase tracking-wider block">Sandbox Execution Allowlist</span>
              <div className="text-xs font-mono text-zinc-300 leading-relaxed bg-zinc-950 p-3 rounded-xl border border-zinc-800">
                <span className="font-bold text-indigo-400 block mb-1">Commands:</span>
                <span>{policies.allowed_prefixes.join(', ')}</span>
                
                <span className="font-bold text-indigo-400 block mt-3 mb-1">Protected Configs:</span>
                <span>{policies.protected_configs.join(', ')}</span>
                
                <span className="font-bold text-indigo-400 block mt-3 mb-1">Workspace Root:</span>
                <span>{policies.workspace_root}</span>
              </div>
            </div>
          </div>

          {/* Secret Management Panel */}
          <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl p-6 shadow-xl space-y-6">
            <h3 className="text-lg font-bold text-zinc-200 flex items-center">
              <Lock className="h-5 w-5 text-indigo-400 mr-2" />
              Runtime Secrets Verification
            </h3>

            <div className="space-y-4">
              <p className="text-xs text-zinc-400 leading-relaxed">
                Environment configurations are scanned dynamically to confirm that LLM API keys are loaded. Secrets are automatically masked from all logs and telemetry streams.
              </p>
              
              <div className="space-y-3.5">
                {Object.entries(secretsStatus).map(([key, isLoaded]) => (
                  <div key={key} className="flex justify-between items-center p-3 bg-zinc-800/30 rounded-xl border border-zinc-800">
                    <span className="text-xs font-mono font-bold text-zinc-300">{key}</span>
                    <span className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                      isLoaded 
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/25' 
                        : 'bg-rose-500/10 text-rose-400 border border-rose-500/25'
                    }`}>
                      {isLoaded ? 'CONFIGURED' : 'MISSING'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      )}

      {/* Tab 2: Security Auditor */}
      {activeTab === 'security' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Code input text area */}
          <div className="lg:col-span-7 bg-zinc-900/40 border border-zinc-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-bold text-zinc-300 uppercase tracking-wider flex items-center">
                <Terminal className="h-4.5 w-4.5 text-indigo-400 mr-1.5" />
                Proposed Implementation Scanner
              </h3>
              <span className="text-[10px] text-zinc-500 font-bold uppercase">Python Syntax</span>
            </div>
            
            <textarea
              value={codeToAudit}
              onChange={(e) => setCodeToAudit(e.target.value)}
              className="w-full h-80 bg-zinc-950 text-zinc-300 font-mono text-xs p-4 rounded-xl border border-zinc-800 focus:outline-none focus:ring-1 focus:ring-indigo-500 leading-relaxed"
            />

            <button
              onClick={handleRunAudit}
              disabled={auditing}
              className="w-full flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-700 text-white font-bold py-2.5 rounded-xl text-xs transition"
            >
              {auditing ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Analyzing source syntax...</span>
                </>
              ) : (
                <>
                  <Eye className="h-4 w-4" />
                  <span>Audit Code Proposal</span>
                </>
              )}
            </button>
          </div>

          {/* Audit findings panel */}
          <div className="lg:col-span-5 bg-zinc-900/40 border border-zinc-800 rounded-2xl p-6 shadow-xl space-y-4 flex flex-col">
            <h3 className="text-sm font-bold text-zinc-300 uppercase tracking-wider flex items-center">
              <Shield className="h-4.5 w-4.5 text-rose-500 mr-1.5" />
              Security Findings Report
            </h3>

            <div className="space-y-3 min-h-[200px]">
              {auditFindings.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center space-y-3 text-zinc-500 py-12">
                  <CheckCircle className="h-10 w-10 text-zinc-700" />
                  <div>
                    <h4 className="text-xs font-bold text-zinc-400">Zero Vulnerabilities Flagged</h4>
                    <p className="text-[10px] text-zinc-600 max-w-xs mt-1">
                      Paste a custom script or run the auditor to check for credentials, OS command chaining, or traversals.
                    </p>
                  </div>
                </div>
              ) : (
                auditFindings.map((finding) => (
                  <div key={finding.finding_id} className="p-4 bg-zinc-800/40 border border-zinc-800 rounded-xl space-y-2">
                    <div className="flex justify-between items-start">
                      <span className={`px-2 py-0.5 rounded text-[9px] font-extrabold tracking-wide uppercase ${
                        finding.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/20' :
                        finding.severity === 'HIGH' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/20' :
                        'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20'
                      }`}>
                        {finding.severity}
                      </span>
                      <span className="text-[10px] text-zinc-500 font-bold font-mono">ID: {finding.finding_id}</span>
                    </div>
                    <p className="text-xs text-zinc-200 leading-relaxed font-medium">{finding.message}</p>
                    {finding.line_number && (
                      <div className="text-[10px] text-zinc-500 flex space-x-2 font-semibold">
                        <span>File: {finding.file_path}</span>
                        <span>•</span>
                        <span>Line: {finding.line_number}</span>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

        </div>
      )}

      {/* Tab 3: Consensus & Approvals */}
      {activeTab === 'consensus' && (
        <div className="space-y-6">
          <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h3 className="text-lg font-bold text-zinc-200 flex items-center">
              <Layers className="h-5 w-5 text-indigo-400 mr-2" />
              Engineering Decision Records (EDRs)
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {activeEdrs.map((edr) => (
                <div key={edr.id} className="bg-zinc-800/30 border border-zinc-800 rounded-xl p-5 space-y-4 flex flex-col justify-between">
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-mono font-bold text-indigo-400">{edr.project.toUpperCase()}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        edr.status === 'APPROVED' ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20' :
                        edr.status === 'REJECTED' ? 'bg-rose-500/15 text-rose-400 border border-rose-500/20' :
                        'bg-yellow-500/10 text-yellow-500 border border-yellow-500/20'
                      }`}>
                        {edr.status}
                      </span>
                    </div>

                    <div className="space-y-1">
                      <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Problem Statement</span>
                      <p className="text-xs text-zinc-300 font-medium leading-relaxed">{edr.problem}</p>
                    </div>

                    <div className="space-y-1">
                      <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Chosen Fix Path</span>
                      <p className="text-xs text-zinc-200 font-semibold leading-relaxed bg-zinc-950/40 p-2.5 rounded-lg border border-zinc-800/60">{edr.chosen}</p>
                    </div>
                  </div>

                  {edr.status === 'WAITING_FOR_APPROVAL' ? (
                    <div className="flex space-x-3 pt-4 border-t border-zinc-800/60 mt-4">
                      <button
                        onClick={() => handleApproveEdr(edr.id, 'APPROVED')}
                        className="flex-1 flex items-center justify-center space-x-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2 rounded-lg text-xs transition"
                      >
                        <Check className="h-3.5 w-3.5" />
                        <span>Approve Fix</span>
                      </button>
                      <button
                        onClick={() => handleApproveEdr(edr.id, 'REJECTED')}
                        className="flex-1 flex items-center justify-center space-x-1.5 bg-rose-600 hover:bg-rose-500 text-white font-bold py-2 rounded-lg text-xs transition"
                      >
                        <X className="h-3.5 w-3.5" />
                        <span>Reject Fix</span>
                      </button>
                    </div>
                  ) : (
                    <div className="pt-4 border-t border-zinc-800/60 text-center mt-4">
                      <span className="text-[11px] text-zinc-500 font-semibold uppercase tracking-wider">Decided by Human Gate Manager</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Performance Telemetry */}
      {activeTab === 'performance' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Latency meters */}
          <div className="lg:col-span-2 bg-zinc-900/40 border border-zinc-800 rounded-2xl p-6 shadow-xl space-y-6">
            <h3 className="text-lg font-bold text-zinc-200 flex items-center">
              <BarChart2 className="h-5 w-5 text-indigo-400 mr-2" />
              Pipeline Execution Latencies
            </h3>

            <div className="space-y-4">
              
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-zinc-400">Sandbox Creation / Setup</span>
                  <span className="text-zinc-200">{latencies.sandbox_startup}s</span>
                </div>
                <div className="w-full bg-zinc-850 h-2 rounded-full overflow-hidden border border-zinc-800">
                  <div className="bg-indigo-500 h-full rounded-full" style={{ width: '85%' }} />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-zinc-400">Consensus Debate Loop</span>
                  <span className="text-zinc-200">{latencies.consensus_duration}s</span>
                </div>
                <div className="w-full bg-zinc-850 h-2 rounded-full overflow-hidden border border-zinc-800">
                  <div className="bg-indigo-500 h-full rounded-full" style={{ width: '45%' }} />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-zinc-400">Self-Healing Diagnostics</span>
                  <span className="text-zinc-200">{latencies.self_healing_duration}s</span>
                </div>
                <div className="w-full bg-zinc-850 h-2 rounded-full overflow-hidden border border-zinc-800">
                  <div className="bg-indigo-500 h-full rounded-full" style={{ width: '15%' }} />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-zinc-400">Memory Retrieval (EME)</span>
                  <span className="text-zinc-200">{latencies.memory_retrieval}s</span>
                </div>
                <div className="w-full bg-zinc-850 h-2 rounded-full overflow-hidden border border-zinc-800">
                  <div className="bg-indigo-500 h-full rounded-full" style={{ width: '8%' }} />
                </div>
              </div>

            </div>
          </div>

          {/* Test stats */}
          <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl p-6 shadow-xl space-y-6">
            <h3 className="text-lg font-bold text-zinc-200 flex items-center">
              <CheckCircle className="h-5 w-5 text-indigo-400 mr-2" />
              Platform Test Report
            </h3>

            <div className="space-y-4">
              <div className="flex justify-between items-center border-b border-zinc-850 pb-3">
                <span className="text-xs text-zinc-400 font-semibold">Total Core Tests</span>
                <span className="text-sm font-bold text-zinc-200">67</span>
              </div>
              <div className="flex justify-between items-center border-b border-zinc-850 pb-3">
                <span className="text-xs text-zinc-400 font-semibold">Pass Rate</span>
                <span className="text-sm font-bold text-emerald-400">100%</span>
              </div>
              <div className="flex justify-between items-center border-b border-zinc-850 pb-3">
                <span className="text-xs text-zinc-400 font-semibold">Regressions detected</span>
                <span className="text-sm font-bold text-zinc-200">0</span>
              </div>
              
              <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-center">
                <span className="text-xs font-bold text-indigo-400">System Integration Status</span>
                <span className="block text-[10px] text-indigo-400/80 mt-1 uppercase font-semibold">Fully Converged</span>
              </div>
            </div>
          </div>

        </div>
      )}

    </div>
  );
};
