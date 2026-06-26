'use client';

import React from 'react';
import { useDashboard } from '../context/DashboardContext';
import { Layers, Cpu, CheckCircle, AlertTriangle, Clock } from 'lucide-react';

export const QueueView: React.FC = () => {
  const { workers, queueStatus, loading } = useDashboard();

  if (!queueStatus) {
    return <div className="p-8 text-center text-muted-foreground">Loading queue telemetry...</div>;
  }

  // Workload details
  const tasksByStatus = Object.entries(queueStatus.tasks_by_status);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Queue & Worker Monitor</h1>
          <p className="text-muted-foreground">Monitor the health of task queues and background execution worker pools.</p>
        </div>
        {loading && <span className="text-xs text-muted-foreground animate-pulse">Syncing states...</span>}
      </div>

      {/* Grid: Queue Status vs Worker Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Queue Depth stats */}
        <div className="bg-card text-card-foreground border rounded-xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 border-b pb-3 mb-4">
              <Layers className="h-5 w-5 text-primary" />
              <h2 className="font-bold text-base">Queue Depth Telemetry</h2>
            </div>
            
            <div className="space-y-6">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground font-medium">Pending/Queued items:</span>
                <span className="text-2xl font-bold text-primary">{queueStatus.queue_size}</span>
              </div>
              
              <div className="space-y-2">
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider block">Task Classifications</span>
                <div className="grid grid-cols-2 gap-2">
                  {tasksByStatus.map(([status, count]) => (
                    <div key={status} className="bg-muted/50 border rounded-lg p-2.5 flex flex-col items-center justify-center">
                      <span className="text-[10px] text-muted-foreground uppercase font-bold text-center">{status}</span>
                      <span className="text-lg font-bold mt-1">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
          <div className="mt-6 pt-4 border-t text-[10px] text-muted-foreground text-center">
            Active worker size configured to avoid API quota exhaustion.
          </div>
        </div>

        {/* Right Column: Worker Threads details */}
        <div className="bg-card text-card-foreground border rounded-xl p-6 shadow-sm lg:col-span-2 space-y-4">
          <div className="flex items-center space-x-2 border-b pb-3">
            <Cpu className="h-5 w-5 text-emerald-500" />
            <h2 className="font-bold text-base">Background Worker Pool</h2>
          </div>
          
          <div className="divide-y">
            {workers.map((worker) => (
              <div key={worker.worker_id} className="py-4 first:pt-0 last:pb-0 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="flex items-center space-x-3">
                  <div className={`p-2.5 rounded-lg border ${
                    worker.is_alive && worker.is_healthy 
                      ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'
                      : 'bg-rose-500/10 text-rose-500 border-rose-500/20'
                  }`}>
                    <Cpu className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-sm text-foreground">{worker.worker_name}</h3>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className="text-[10px] font-mono text-muted-foreground">ID: {worker.worker_id}</span>
                      <span className="text-[10px] font-mono text-muted-foreground flex items-center space-x-0.5">
                        <Clock className="h-3 w-3" />
                        <span>Last Active: {new Date(worker.last_active).toLocaleTimeString()}</span>
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  {/* Task details */}
                  <div className="text-right">
                    <span className="text-[10px] uppercase font-bold text-muted-foreground block">Active Task</span>
                    {worker.current_task ? (
                      <span className="text-xs font-mono font-bold text-primary">{worker.current_task}</span>
                    ) : (
                      <span className="text-xs text-muted-foreground">Idle</span>
                    )}
                  </div>
                  
                  {/* Status indicators */}
                  <div className="flex flex-col items-end">
                    <span className="text-[10px] uppercase font-bold text-muted-foreground block mb-0.5">Liveness</span>
                    {worker.is_alive && worker.is_healthy ? (
                      <span className="flex items-center space-x-0.5 text-xs text-emerald-500 font-semibold bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                        <CheckCircle className="h-3 w-3" />
                        <span>Healthy</span>
                      </span>
                    ) : (
                      <span className="flex items-center space-x-0.5 text-xs text-rose-500 font-semibold bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded-full">
                        <AlertTriangle className="h-3 w-3" />
                        <span>Offline</span>
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};
