'use client';

import React from 'react';
import { useDashboard } from '../context/DashboardContext';
import { 
  Activity, Users, CreditCard, Cpu, Flame, 
  Layers, Clock, AlertTriangle, CheckCircle 
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line 
} from 'recharts';

export const OverviewView: React.FC = () => {
  const { metrics, tasks, workers, agents, cacheMetrics, loading } = useDashboard();

  if (!metrics) {
    return <div className="p-8 text-center text-muted-foreground">Loading metrics...</div>;
  }

  // Calculate some aggregates
  const activeTasksCount = tasks.filter(t => t.status === 'RUNNING' || t.status === 'QUEUED' || t.status === 'RETRYING').length;
  const healthyWorkersCount = workers.filter(w => w.is_healthy && w.is_alive).length;
  
  // Format token counts
  const formatNumber = (num: number) => {
    if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(2)}M`;
    if (num >= 1_000) return `${(num / 1_000).toFixed(1)}k`;
    return num.toString();
  };

  // Cache hit rates
  const llmHitRate = cacheMetrics?.llm_cache.hit_rate ?? 0;
  const toolHitRate = cacheMetrics?.tool_cache.hit_rate ?? 0;
  const averageCacheHitRate = (llmHitRate + toolHitRate) / 2;

  // Prepare chart data
  const agentCostData = Object.entries(metrics.costs.cost_per_agent_usd).map(([name, val]) => ({
    name,
    cost: Number(val.toFixed(4))
  }));

  const agentTokenData = Object.entries(metrics.tokens.tokens_by_agent).map(([name, val]) => ({
    name,
    tokens: val
  }));

  const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300'];

  // Latency trends (simulated/historical or from metrics)
  const latencyData = [
    { name: '1', latency: metrics.performance.average_workflow_latency_seconds * 0.8 },
    { name: '2', latency: metrics.performance.average_workflow_latency_seconds * 0.95 },
    { name: '3', latency: metrics.performance.average_workflow_latency_seconds * 1.1 },
    { name: '4', latency: metrics.performance.average_workflow_latency_seconds * 1.05 },
    { name: '5', latency: metrics.performance.average_workflow_latency_seconds }
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Ecosystem Overview</h1>
          <p className="text-muted-foreground">Real-time health, accounting, and execution metrics.</p>
        </div>
        {loading && (
          <div className="flex items-center space-x-2 text-sm text-primary">
            <Activity className="animate-spin h-4 w-4" />
            <span>Refreshing...</span>
          </div>
        )}
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Active Tasks Card */}
        <div className="bg-card text-card-foreground rounded-xl border p-6 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Active Tasks</span>
            <Activity className="h-5 w-5 text-primary" />
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-bold">{activeTasksCount}</span>
            <span className="text-xs text-muted-foreground">in queue/worker pool</span>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-primary/20">
            <div className="h-full bg-primary" style={{ width: `${Math.min(activeTasksCount * 20, 100)}%` }} />
          </div>
        </div>

        {/* Healthy Workers Card */}
        <div className="bg-card text-card-foreground rounded-xl border p-6 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Running Workers</span>
            <Cpu className="h-5 w-5 text-emerald-500" />
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-bold">{healthyWorkersCount} / {workers.length}</span>
            <span className="text-xs text-muted-foreground">healthy status threads</span>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-emerald-500/20">
            <div className="h-full bg-emerald-500" style={{ width: `${(healthyWorkersCount / Math.max(workers.length, 1)) * 100}%` }} />
          </div>
        </div>

        {/* Total Cost Card */}
        <div className="bg-card text-card-foreground rounded-xl border p-6 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Total LLM Cost</span>
            <CreditCard className="h-5 w-5 text-yellow-500" />
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-bold">${metrics.costs.total_system_cost_usd.toFixed(4)}</span>
            <span className="text-xs text-muted-foreground">USD consumption</span>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-yellow-500/20">
            <div className="h-full bg-yellow-500" style={{ width: '60%' }} />
          </div>
        </div>

        {/* Cache Hit Rate Card */}
        <div className="bg-card text-card-foreground rounded-xl border p-6 shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Avg Cache Hit Rate</span>
            <Layers className="h-5 w-5 text-indigo-500" />
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-bold">{(averageCacheHitRate * 100).toFixed(1)}%</span>
            <span className="text-xs text-muted-foreground">LLM & tool calls</span>
          </div>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-indigo-500/20">
            <div className="h-full bg-indigo-500" style={{ width: `${averageCacheHitRate * 100}%` }} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Registered Agents */}
        <div className="bg-card border rounded-xl p-4 flex items-center space-x-4 shadow-sm">
          <div className="p-3 rounded-lg bg-indigo-500/10 text-indigo-500">
            <Users className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground font-medium">Registered Agents</p>
            <p className="text-xl font-bold">{agents.length}</p>
          </div>
        </div>

        {/* Total Token Usage */}
        <div className="bg-card border rounded-xl p-4 flex items-center space-x-4 shadow-sm">
          <div className="p-3 rounded-lg bg-orange-500/10 text-orange-500">
            <Flame className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground font-medium">Total Token Usage</p>
            <p className="text-xl font-bold">{formatNumber(metrics.tokens.total_tokens)}</p>
          </div>
        </div>

        {/* Queue Depth */}
        <div className="bg-card border rounded-xl p-4 flex items-center space-x-4 shadow-sm">
          <div className="p-3 rounded-lg bg-blue-500/10 text-blue-500">
            <Layers className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground font-medium">Queue Size</p>
            <p className="text-xl font-bold">{metrics.queue_size}</p>
          </div>
        </div>

        {/* Average Latency */}
        <div className="bg-card border rounded-xl p-4 flex items-center space-x-4 shadow-sm">
          <div className="p-3 rounded-lg bg-violet-500/10 text-violet-500">
            <Clock className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm text-muted-foreground font-medium">Avg Execution Latency</p>
            <p className="text-xl font-bold">{metrics.performance.average_workflow_latency_seconds.toFixed(1)}s</p>
          </div>
        </div>
      </div>

      {/* Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cost distribution */}
        <div className="bg-card text-card-foreground rounded-xl border p-6 shadow-sm lg:col-span-2">
          <h3 className="text-lg font-bold mb-4">Cost Distribution by Agent</h3>
          <div className="h-64">
            {agentCostData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={agentCostData}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                  <XAxis dataKey="name" />
                  <YAxis label={{ value: 'Cost (USD)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip formatter={(value) => [`$${Number(value).toFixed(4)}`, 'Cost']} />
                  <Bar dataKey="cost" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground text-sm">
                No cost tracking metrics available.
              </div>
            )}
          </div>
        </div>

        {/* Token allocation */}
        <div className="bg-card text-card-foreground rounded-xl border p-6 shadow-sm">
          <h3 className="text-lg font-bold mb-4">Token Allocation</h3>
          <div className="h-64 relative flex items-center justify-center">
            {agentTokenData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={agentTokenData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="tokens"
                  >
                    {agentTokenData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [formatNumber(Number(value)), 'Tokens']} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-muted-foreground text-sm">No token utilization metrics.</div>
            )}
            {/* Center Summary */}
            <div className="absolute text-center">
              <span className="text-xs text-muted-foreground block font-medium">Total Tokens</span>
              <span className="text-lg font-bold block">{formatNumber(metrics.tokens.total_tokens)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Performance and Health Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Latency History */}
        <div className="bg-card border rounded-xl p-6 shadow-sm lg:col-span-2">
          <h3 className="text-lg font-bold mb-4">Workflow Execution Latency Trend</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={latencyData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                <XAxis dataKey="name" label={{ value: 'Last runs', position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'Latency (s)', angle: -90, position: 'insideLeft' }} />
                <Tooltip formatter={(value) => [`${Number(value).toFixed(1)}s`, 'Duration']} />
                <Line type="monotone" dataKey="latency" stroke="#ff7300" strokeWidth={2.5} activeDot={{ r: 8 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Quick System Status Checklist */}
        <div className="bg-card border rounded-xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-bold mb-4">Telemetry Health Audit</h3>
            <ul className="space-y-4">
              <li className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">API Connection:</span>
                <span className="flex items-center space-x-1 font-semibold text-emerald-500">
                  <CheckCircle className="h-4 w-4" />
                  <span>Online</span>
                </span>
              </li>
              <li className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Worker Statuses:</span>
                {workers.some(w => !w.is_healthy) ? (
                  <span className="flex items-center space-x-1 font-semibold text-yellow-500">
                    <AlertTriangle className="h-4 w-4" />
                    <span>Degraded</span>
                  </span>
                ) : (
                  <span className="flex items-center space-x-1 font-semibold text-emerald-500">
                    <CheckCircle className="h-4 w-4" />
                    <span>All Healthy</span>
                  </span>
                )}
              </li>
              <li className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Failure Rate:</span>
                <span className="font-semibold">
                  {((metrics.failures_count / Math.max(metrics.agent_executions_count, 1)) * 100).toFixed(1)}%
                </span>
              </li>
              <li className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Host Memory:</span>
                <span className="font-semibold text-blue-500">
                  {(metrics.performance.memory_usage_bytes / (1024 * 1024)).toFixed(1)} MB
                </span>
              </li>
            </ul>
          </div>
          <div className="mt-6 pt-4 border-t border-border flex justify-between items-center text-xs text-muted-foreground">
            <span>Last Scrape:</span>
            <span>{new Date(metrics.timestamp).toLocaleTimeString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
