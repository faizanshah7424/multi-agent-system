'use client';

import React from 'react';
import { useDashboard } from '../context/DashboardContext';
import { CreditCard, Cpu, Activity, Info } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

export const CostsView: React.FC = () => {
  const { metrics } = useDashboard();

  if (!metrics) {
    return <div className="p-8 text-center text-muted-foreground">Loading cost analytics...</div>;
  }

  // Cost data formats
  const systemCost = metrics.costs.total_system_cost_usd;
  const agentCosts = Object.entries(metrics.costs.cost_per_agent_usd).map(([agent, val]) => ({
    name: agent,
    cost: val
  }));

  const taskCosts = Object.entries(metrics.costs.cost_per_task_usd).map(([task, val]) => ({
    name: task.slice(0, 10) + '...',
    cost: val,
    fullId: task
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Cost Analytics & Audits</h1>
        <p className="text-muted-foreground">Audit spending trends, token conversions, and pricing classifications.</p>
      </div>

      {/* Aggregate metrics rows */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        
        {/* Total Cost card */}
        <div className="bg-card text-card-foreground border rounded-xl p-6 shadow-sm flex items-center space-x-4">
          <div className="p-4 rounded-lg bg-yellow-500/10 text-yellow-500 shrink-0">
            <CreditCard className="h-6 w-6" />
          </div>
          <div>
            <span className="text-sm font-medium text-muted-foreground block">System Financial Spent</span>
            <span className="text-2xl font-bold block">${systemCost.toFixed(5)}</span>
            <span className="text-xs text-muted-foreground">accumulated USD consumption</span>
          </div>
        </div>

        {/* Pricing reference model */}
        <div className="bg-card border rounded-xl p-4 md:col-span-2 shadow-sm flex flex-col justify-center">
          <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider block mb-2">Model Pricing reference rules</span>
          <div className="grid grid-cols-3 gap-4 text-xs">
            <div className="bg-muted/40 border rounded p-2 text-center">
              <span className="font-bold text-foreground block">Gemini 2.5 Flash</span>
              <span className="text-muted-foreground block mt-0.5">$0.075 / $0.30 per 1M</span>
            </div>
            <div className="bg-muted/40 border rounded p-2 text-center">
              <span className="font-bold text-foreground block">Gemini 2.5 Pro</span>
              <span className="text-muted-foreground block mt-0.5">$1.25 / $5.00 per 1M</span>
            </div>
            <div className="bg-muted/40 border rounded p-2 text-center">
              <span className="font-bold text-foreground block">Embeddings 004</span>
              <span className="text-muted-foreground block mt-0.5">$0.025 / $0.00 per 1M</span>
            </div>
          </div>
        </div>

      </div>

      {/* Charts cost allocation */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Cost per Agent */}
        <div className="bg-card border rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider flex items-center space-x-1">
            <Cpu className="h-4 w-4 text-primary" />
            <span>Operational Spent per Agent Type</span>
          </h3>
          <div className="h-64">
            {agentCosts.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={agentCosts}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                  <XAxis dataKey="name" />
                  <YAxis label={{ value: 'Spent (USD)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip formatter={(value) => [`$${Number(value).toFixed(5)}`, 'Spent']} />
                  <Bar dataKey="cost" fill="#8884d8" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground text-xs">No agent cost metrics.</div>
            )}
          </div>
        </div>

        {/* Cost per task */}
        <div className="bg-card border rounded-xl p-6 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-wider flex items-center space-x-1">
            <Activity className="h-4 w-4 text-primary" />
            <span>Cost per Workflow Execution Session</span>
          </h3>
          <div className="h-64">
            {taskCosts.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={taskCosts}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                  <XAxis dataKey="name" />
                  <YAxis label={{ value: 'Spent (USD)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip formatter={(value, name, props) => [`$${Number(value).toFixed(5)}`, `Task ID: ${props.payload.fullId}`]} />
                  <Bar dataKey="cost" fill="#82ca9d" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-muted-foreground text-xs">No task cost metrics.</div>
            )}
          </div>
        </div>

      </div>

      {/* Pricing info alert */}
      <div className="bg-muted/40 border rounded-xl p-4 flex items-start space-x-2 text-xs text-muted-foreground">
        <Info className="h-4 w-4 text-primary shrink-0 mt-0.5" />
        <p>
          Operational spent calculations are accumulated dynamically as task workflow worker loops execute prompts. Costs depend on token volumes processed through the core Gemini APIs.
        </p>
      </div>

    </div>
  );
};
