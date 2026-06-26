'use client';

import React from 'react';
import { useDashboard } from '../context/DashboardContext';
import { Shield, Hammer, AlertCircle, Info, CheckCircle } from 'lucide-react';

export const AgentsView: React.FC = () => {
  const { agents, tasks } = useDashboard();

  // Compute workload for each agent (count steps currently 'running' or 'queued' assigned to agent)
  const getAgentWorkload = (agentName: string): number => {
    // If we have tasks with active running steps, we can parse them, otherwise fallback to 0
    return tasks.filter(t => t.status === 'RUNNING' && t.payload.task.toLowerCase().includes(agentName)).length;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Agent Registry Viewer</h1>
        <p className="text-muted-foreground">Registered autonomous agents, metadata profiles, and current processing queues.</p>
      </div>

      {agents.length === 0 ? (
        <div className="bg-yellow-500/10 border border-yellow-500/20 text-yellow-600 rounded-xl p-4 flex items-center space-x-3">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>No agents found in the system registry. Verify your registry decorator setups.</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {agents.map((agent) => {
            const workload = getAgentWorkload(agent.name);
            return (
              <div key={agent.name} className="bg-card text-card-foreground rounded-xl border p-6 shadow-sm flex flex-col justify-between hover:shadow-md transition">
                <div>
                  {/* Name and active badge */}
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-xl font-bold flex items-center space-x-2">
                        <span className="capitalize">{agent.name}</span>
                        <span className="text-xs font-normal text-muted-foreground font-mono">({agent.role})</span>
                      </h3>
                      <p className="text-sm text-muted-foreground mt-2">{agent.description}</p>
                    </div>
                    <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                      workload > 0 
                        ? 'bg-blue-500/10 text-blue-500 border border-blue-500/20 animate-pulse'
                        : 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
                    }`}>
                      {workload > 0 ? `Active: ${workload} tasks` : 'Idle / Available'}
                    </span>
                  </div>

                  {/* Capabilities */}
                  <div className="mt-6">
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center space-x-1.5">
                      <Shield className="h-3.5 w-3.5" />
                      <span>Specialized Capabilities</span>
                    </h4>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {agent.capabilities.map((cap) => (
                        <span key={cap} className="text-xs bg-muted px-2 py-0.5 rounded border">
                          {cap.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Exposed Tools */}
                  <div className="mt-4">
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center space-x-1.5">
                      <Hammer className="h-3.5 w-3.5" />
                      <span>Exposed System Tools</span>
                    </h4>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {agent.tools.map((tool) => (
                        <span key={tool} className="text-xs bg-primary/5 text-primary border border-primary/10 px-2.5 py-0.5 rounded-full font-mono">
                          {tool}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Audit details */}
                <div className="mt-6 pt-4 border-t border-border flex justify-between items-center text-xs text-muted-foreground bg-muted/20 -mx-6 -mb-6 p-4 rounded-b-xl">
                  <span className="flex items-center space-x-1">
                    <Info className="h-3.5 w-3.5 text-primary" />
                    <span>Registry Discovery: Dynamic</span>
                  </span>
                  <span className="flex items-center space-x-1 text-emerald-500 font-medium">
                    <CheckCircle className="h-3.5 w-3.5" />
                    <span>Liveness: Online</span>
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
