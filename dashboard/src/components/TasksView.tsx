'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useDashboard } from '../context/DashboardContext';
import { api, TaskModel, MemoryLog, MemoryMessage } from '../lib/api';
import * as mock from '../lib/mockData';
import { 
  Play, Search, AlertCircle, RefreshCw, XCircle, 
  CheckCircle, Clock, MessageSquare, Terminal, Eye, FileText 
} from 'lucide-react';

interface WorkflowStep {
  step_id: number;
  name: string;
  status: string;
  assigned_agent: string;
}

export const TasksView: React.FC = () => {
  const { tasks, refreshData, useMockData } = useDashboard();
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  
  // Selected Task State
  const [selectedTask, setSelectedTask] = useState<TaskModel | null>(null);
  const [logs, setLogs] = useState<MemoryLog[]>([]);
  const [messages, setMessages] = useState<MemoryMessage[]>([]);
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [loadingDetails, setLoadingDetails] = useState<boolean>(false);

  // New Task Form State
  const [newPrompt, setNewPrompt] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);

  const logsEndRef = useRef<HTMLDivElement>(null);

  // Auto scroll logs to bottom on update
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Set first task as selected by default on load
  useEffect(() => {
    if (tasks.length > 0 && !selectedTask) {
      setSelectedTask(tasks[0]);
    }
  }, [tasks, selectedTask]);

  // Fetch task execution details (logs, messages, steps)
  const fetchTaskDetails = useCallback(async (taskId: string) => {
    setLoadingDetails(true);
    try {
      if (useMockData) {
        const mockHist = mock.mockHistory[taskId] || { logs: [], messages: [] };
        setLogs(mockHist.logs);
        setMessages(mockHist.messages);
        
        // Mock some workflow steps
        setSteps([
          { step_id: 1, name: "Plan deconstruction", status: "completed", assigned_agent: "planner" },
          { step_id: 2, name: "Web scraping research", status: taskId === 'task_fa2b98e1' ? "running" : "completed", assigned_agent: "researcher" },
          { step_id: 3, name: "Source implementation", status: taskId === 'task_fa2b98e1' ? "pending" : "completed", assigned_agent: "developer" }
        ]);
        return;
      }

      const [history, statusRes] = await Promise.all([
        api.getMemoryHistory(taskId).catch(() => ({ logs: [], messages: [] })),
        api.getMemoryStatus(taskId).catch(() => ({ steps: [] }))
      ]);

      setLogs(history.logs || []);
      setMessages(history.messages || []);
      setSteps((statusRes.steps || []) as WorkflowStep[]);
    } catch (err) {
      console.error("Failed to load details for task: " + taskId, err);
    } finally {
      setLoadingDetails(false);
    }
  }, [useMockData]);

  useEffect(() => {
    if (selectedTask) {
      fetchTaskDetails(selectedTask.task_id);
      
      // Setup polling for logs/steps if task is running
      if (selectedTask.status === 'RUNNING' || selectedTask.status === 'RETRYING') {
        const interval = setInterval(() => {
          fetchTaskDetails(selectedTask.task_id);
        }, 3000);
        return () => clearInterval(interval);
      }
    }
  }, [selectedTask, fetchTaskDetails]);

  // Filter tasks
  const filteredTasks = tasks.filter(task => {
    const matchesStatus = filterStatus === 'ALL' || task.status === filterStatus;
    const matchesSearch = task.payload.task.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          task.task_id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  // Handle task submission
  const handleSubmitTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPrompt.trim()) return;

    setSubmitting(true);
    setFormError(null);
    setFormSuccess(null);

    try {
      if (useMockData) {
        // Mock addition
        const newTaskId = `task_${Math.random().toString(16).slice(2, 10)}`;
        const newTask: TaskModel = {
          task_id: newTaskId,
          user_id: "user_dashboard",
          task_type: "workflow",
          payload: { task: newPrompt },
          status: "QUEUED",
          created_at: new Date().toISOString(),
          started_at: null,
          completed_at: null,
          retry_count: 0,
          error: null
        };
        
        // Add to mock task history list
        mock.mockTasks.unshift(newTask);
        mock.mockHistory[newTaskId] = {
          logs: [{ timestamp: new Date().toISOString(), source: "system", message: `Queuing background task execution: '${newPrompt}'`, level: "INFO" }],
          messages: [{ role: "user", content: newPrompt, timestamp: new Date().toISOString(), agent_name: "user" }]
        };
        
        setSelectedTask(newTask);
        setFormSuccess(`Task created successfully in mock pool (ID: ${newTaskId})`);
        setNewPrompt('');
        refreshData();
        return;
      }

      const res = await api.createTask({ task: newPrompt });
      setSelectedTask(res);
      setFormSuccess(`Task submitted successfully! Thread ID: ${res.task_id}`);
      setNewPrompt('');
      refreshData();
    } catch (err) {
      const error = err as Error;
      setFormError(error.message || "Failed to trigger background task.");
    } finally {
      setSubmitting(false);
    }
  };

  // Cancel task
  const handleCancelTask = async (taskId: string) => {
    try {
      if (useMockData) {
        mock.mockTasks.forEach(t => {
          if (t.task_id === taskId) {
            t.status = 'CANCELLED';
            t.completed_at = new Date().toISOString();
            t.error = "Cancelled via Dashboard user command.";
          }
        });
        if (selectedTask?.task_id === taskId) {
          setSelectedTask({ ...selectedTask, status: 'CANCELLED' });
        }
        refreshData();
        return;
      }
      await api.cancelTask(taskId);
      refreshData();
      if (selectedTask?.task_id === taskId) {
        const updated = await api.getTask(taskId);
        setSelectedTask(updated);
      }
    } catch (err) {
      const error = err as Error;
      alert("Failed to cancel task: " + error.message);
    }
  };

  // Consolidated memory summary trigger
  const handleConsolidateMemory = async (sessionId: string) => {
    try {
      if (useMockData) {
        alert("Memory consolidation complete! Summary vector written to index.");
        return;
      }
      const res = await api.consolidateMemory(sessionId);
      alert(`Memory Consolidated Successfully!\nSummary: ${res.consolidated_summary}`);
    } catch (err) {
      const error = err as Error;
      alert(`Consolidation failed: ${error.message}`);
    }
  };

  // Render status badge helpers
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED': return <CheckCircle className="h-4 w-4 text-emerald-500" />;
      case 'FAILED': return <XCircle className="h-4 w-4 text-rose-500" />;
      case 'RUNNING': return <RefreshCw className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'RETRYING': return <RefreshCw className="h-4 w-4 text-yellow-500 animate-spin" />;
      case 'CANCELLED': return <XCircle className="h-4 w-4 text-gray-500" />;
      default: return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'COMPLETED': return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';
      case 'FAILED': return 'bg-rose-500/10 text-rose-500 border-rose-500/20';
      case 'RUNNING': return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      case 'RETRYING': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      default: return 'bg-muted text-muted-foreground border-border';
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-8rem)]">
      
      {/* Left Column: Tasks Queue Lists */}
      <div className="bg-card rounded-xl border flex flex-col h-full shadow-sm overflow-hidden">
        
        {/* New Task Creator Form */}
        <div className="p-4 border-b">
          <h2 className="font-bold text-sm text-muted-foreground uppercase tracking-wider mb-2">Trigger Work Routine</h2>
          <form onSubmit={handleSubmitTask} className="space-y-2">
            <textarea
              value={newPrompt}
              onChange={(e) => setNewPrompt(e.target.value)}
              placeholder="e.g. Write a Python script to scan the workspace directory and report file count..."
              className="w-full text-sm bg-background border rounded-lg p-2 h-20 focus:ring-1 focus:ring-primary outline-none resize-none"
            />
            {formError && <div className="text-xs text-rose-500 flex items-center space-x-1"><AlertCircle className="h-3 w-3" /><span>{formError}</span></div>}
            {formSuccess && <div className="text-xs text-emerald-500 font-semibold">{formSuccess}</div>}
            <button
              type="submit"
              disabled={submitting || !newPrompt.trim()}
              className="w-full flex items-center justify-center space-x-2 bg-primary text-primary-foreground py-2 rounded-lg text-sm font-semibold hover:bg-primary/95 transition disabled:opacity-50"
            >
              <Play className="h-4 w-4" />
              <span>{submitting ? 'Queuing Task...' : 'Trigger Workflow'}</span>
            </button>
          </form>
        </div>

        {/* Task List Search & Filter */}
        <div className="p-3 border-b bg-muted/30 flex items-center justify-between gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-2 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search Tasks ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-background pl-8 pr-3 py-1.5 border rounded-md text-xs focus:ring-1 focus:ring-primary outline-none"
            />
          </div>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="text-xs bg-background border rounded-md p-1.5 focus:ring-1 focus:ring-primary outline-none"
          >
            <option value="ALL">All Status</option>
            <option value="COMPLETED">Completed</option>
            <option value="RUNNING">Running</option>
            <option value="QUEUED">Queued</option>
            <option value="RETRYING">Retrying</option>
            <option value="FAILED">Failed</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>

        {/* Tasks List */}
        <div className="flex-1 overflow-y-auto divide-y">
          {filteredTasks.length === 0 ? (
            <div className="p-8 text-center text-xs text-muted-foreground">No tasks matching filters.</div>
          ) : (
            filteredTasks.map((task) => (
              <div
                key={task.task_id}
                onClick={() => setSelectedTask(task)}
                className={`p-3 cursor-pointer hover:bg-muted/40 transition text-left flex flex-col space-y-2 ${selectedTask?.task_id === task.task_id ? 'bg-primary/5 border-l-4 border-primary' : ''}`}
              >
                <div className="flex justify-between items-center">
                  <span className="font-mono text-xs font-semibold">{task.task_id}</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getStatusClass(task.status)}`}>
                    {task.status}
                  </span>
                </div>
                <p className="text-xs text-foreground font-medium line-clamp-2">{task.payload.task}</p>
                <div className="flex justify-between items-center text-[10px] text-muted-foreground">
                  <span>{new Date(task.created_at).toLocaleTimeString()}</span>
                  {task.retry_count > 0 && <span className="text-yellow-500 font-medium">Retries: {task.retry_count}</span>}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Right 2 Columns: Selected Task Real-Time Monitor */}
      <div className="lg:col-span-2 flex flex-col h-full bg-card rounded-xl border overflow-hidden shadow-sm">
        
        {selectedTask ? (
          <>
            {/* Header Details */}
            <div className="p-4 border-b bg-muted/20 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <div className="flex items-center space-x-2">
                  <h2 className="font-mono text-lg font-bold">{selectedTask.task_id}</h2>
                  <div className="flex items-center space-x-1 text-xs">
                    {getStatusIcon(selectedTask.status)}
                    <span className="font-medium text-muted-foreground capitalize">{selectedTask.status.toLowerCase()}</span>
                  </div>
                </div>
                <p className="text-sm mt-1 text-foreground font-semibold">{selectedTask.payload.task}</p>
              </div>
              <div className="flex items-center space-x-2 shrink-0">
                {(selectedTask.status === 'RUNNING' || selectedTask.status === 'QUEUED' || selectedTask.status === 'RETRYING') && (
                  <button
                    onClick={() => handleCancelTask(selectedTask.task_id)}
                    className="flex items-center space-x-1 border border-rose-500/30 text-rose-500 hover:bg-rose-500/10 px-3 py-1.5 rounded-lg text-xs font-semibold"
                  >
                    <span>Cancel Work</span>
                  </button>
                )}
                {selectedTask.status === 'COMPLETED' && (
                  <button
                    onClick={() => handleConsolidateMemory(selectedTask.task_id)}
                    className="flex items-center space-x-1 border border-primary/30 text-primary hover:bg-primary/10 px-3 py-1.5 rounded-lg text-xs font-semibold"
                  >
                    <FileText className="h-3.5 w-3.5" />
                    <span>Consolidate Memory</span>
                  </button>
                )}
              </div>
            </div>

            {/* Error banner if failed */}
            {selectedTask.error && (
              <div className="bg-rose-500/10 border-b border-rose-500/20 text-rose-500 p-3 text-xs flex items-start space-x-2">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold">Error Log Summary:</span>
                  <p className="font-mono mt-0.5">{selectedTask.error}</p>
                </div>
              </div>
            )}

            {/* Steps Progress */}
            {steps.length > 0 && (
              <div className="p-3 border-b bg-muted/10 flex flex-wrap gap-4 items-center">
                <span className="text-[10px] uppercase font-bold text-muted-foreground">Workflow Steps:</span>
                <div className="flex flex-wrap gap-2">
                  {steps.map(step => (
                    <div key={step.step_id} className="flex items-center space-x-1 bg-background border rounded px-2 py-0.5 text-xs">
                      {getStatusIcon(step.status.toUpperCase())}
                      <span className="font-medium text-foreground">Step {step.step_id}: {step.name}</span>
                      <span className="text-[10px] text-muted-foreground">({step.assigned_agent})</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Output Panels: Terminal Logs vs Chat transcripts */}
            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x overflow-hidden">
              
              {/* Terminal Execution Logs */}
              <div className="flex flex-col h-full overflow-hidden bg-zinc-950 text-zinc-100">
                <div className="px-3 py-2 bg-zinc-900 border-b border-zinc-800 flex items-center space-x-2 shrink-0">
                  <Terminal className="h-4 w-4 text-emerald-400" />
                  <span className="text-xs font-bold font-mono text-zinc-400 uppercase tracking-wider">System Terminal Trace</span>
                </div>
                
                <div className="flex-1 p-3 overflow-y-auto font-mono text-xs space-y-2 select-text">
                  {loadingDetails ? (
                    <div className="text-zinc-500">Retrieving system execution stack...</div>
                  ) : logs.length === 0 ? (
                    <div className="text-zinc-500">No terminal trace entries found for this execution.</div>
                  ) : (
                    logs.map((log, idx) => (
                      <div key={idx} className="leading-relaxed">
                        <span className="text-zinc-500">[{new Date(log.timestamp).toLocaleTimeString()}]</span>{' '}
                        <span className={`font-semibold ${
                          log.level === 'ERROR' ? 'text-red-400' :
                          log.level === 'WARN' ? 'text-yellow-400' : 'text-blue-400'
                        }`}>
                          [{log.source.toUpperCase()}]
                        </span>{' '}
                        <span className="text-zinc-300">{log.message}</span>
                      </div>
                    ))
                  )}
                  <div ref={logsEndRef} />
                </div>
              </div>

              {/* Chat Transcripts */}
              <div className="flex flex-col h-full overflow-hidden bg-background">
                <div className="px-3 py-2 bg-muted/40 border-b flex items-center space-x-2 shrink-0">
                  <MessageSquare className="h-4 w-4 text-primary" />
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Agent Workspace Chatter</span>
                </div>
                
                <div className="flex-1 p-4 overflow-y-auto space-y-4">
                  {loadingDetails ? (
                    <div className="text-muted-foreground text-sm">Loading agents dialogs...</div>
                  ) : messages.length === 0 ? (
                    <div className="text-muted-foreground text-sm text-center py-12">No agent-to-agent workspace chatter recorded yet.</div>
                  ) : (
                    messages.map((msg, idx) => (
                      <div
                        key={idx}
                        className={`flex flex-col space-y-1 ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                      >
                        <div className="flex items-baseline space-x-2 text-[10px] text-muted-foreground">
                          <span className="font-bold text-foreground capitalize">{msg.agent_name || msg.role}</span>
                          <span>{new Date(msg.timestamp).toLocaleTimeString()}</span>
                        </div>
                        <div className={`p-3 rounded-lg text-sm max-w-[85%] text-left border ${
                          msg.role === 'user'
                            ? 'bg-primary text-primary-foreground border-primary/20 rounded-tr-none'
                            : 'bg-card text-foreground border-border rounded-tl-none shadow-sm'
                        }`}>
                          <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground p-12 text-center">
            <Eye className="h-12 w-12 text-muted/60 mb-3" />
            <h3 className="font-bold text-base text-foreground">No Task Selected</h3>
            <p className="text-sm max-w-xs mt-1">Select a session from the queue left side pane to inspect terminal trace logs and agent chat transcripts.</p>
          </div>
        )}
      </div>

    </div>
  );
};
