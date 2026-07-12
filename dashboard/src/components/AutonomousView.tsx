'use client';

import React from 'react';
import { Cpu, Play, Terminal } from 'lucide-react';

export const AutonomousView: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white flex items-center">
          <Cpu className="h-6 w-6 text-indigo-400 mr-2" />
          Autonomous Execution Center
        </h2>
        <p className="text-sm text-zinc-400 mt-1">
          Monitor and trigger autonomous agent loops for complex software engineering tasks.
        </p>
      </div>

      <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl p-6 shadow-xl backdrop-blur-md">
        <div className="flex flex-col items-center justify-center h-64 text-center space-y-4">
          <div className="p-4 bg-indigo-500/10 rounded-full text-indigo-400">
            <Terminal className="h-10 w-10 animate-pulse" />
          </div>
          <h3 className="text-lg font-semibold text-zinc-200">No active autonomous sessions</h3>
          <p className="text-sm text-zinc-500 max-w-sm">
            Launch a task from the planner or type a prompt to initiate an autonomous pair-programming loop.
          </p>
          <button className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-lg flex items-center space-x-1.5 transition">
            <Play className="h-3.5 w-3.5" />
            <span>Start Autonomous Agent</span>
          </button>
        </div>
      </div>
    </div>
  );
};
