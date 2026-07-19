'use client';

import React from 'react';
import { 
  Lightbulb, Wand2, Layers, Users, Code2, 
  TestTube2, GitCommit, Rocket, CheckCircle2 
} from 'lucide-react';

const steps = [
  { step: '01', name: 'Idea', icon: Lightbulb, color: 'text-amber-400 border-amber-500/30 bg-amber-500/10' },
  { step: '02', name: 'AI Planning', icon: Wand2, color: 'text-indigo-400 border-indigo-500/30 bg-indigo-500/10' },
  { step: '03', name: 'Architecture', icon: Layers, color: 'text-blue-400 border-blue-500/30 bg-blue-500/10' },
  { step: '04', name: 'Discussion', icon: Users, color: 'text-purple-400 border-purple-500/30 bg-purple-500/10' },
  { step: '05', name: 'Coding', icon: Code2, color: 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' },
  { step: '06', name: 'Testing', icon: TestTube2, color: 'text-teal-400 border-teal-500/30 bg-teal-500/10' },
  { step: '07', name: 'GitHub Commit', icon: GitCommit, color: 'text-pink-400 border-pink-500/30 bg-pink-500/10' },
  { step: '08', name: 'Deployment', icon: Rocket, color: 'text-violet-400 border-violet-500/30 bg-violet-500/10' },
  { step: '09', name: 'Production', icon: CheckCircle2, color: 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10' }
];

export const WorkflowTimeline: React.FC = () => {
  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <h3 className="text-xs font-extrabold uppercase tracking-widest text-indigo-400">
          Autonomous Pipeline
        </h3>
        <h4 className="text-xl font-extrabold text-white">
          Idea-to-Production Workflow
        </h4>
      </div>

      <div className="p-5 rounded-2xl bg-zinc-900/60 border border-zinc-800/80 backdrop-blur-xl space-y-4 shadow-xl">
        <div className="grid grid-cols-3 sm:grid-cols-9 gap-2">
          {steps.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div key={idx} className="flex flex-col items-center text-center space-y-2 group">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center border ${item.color} shadow-sm group-hover:scale-110 transition duration-300`}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="space-y-0.5">
                  <span className="text-[10px] font-mono font-bold text-zinc-500 block">{item.step}</span>
                  <span className="text-[11px] font-bold text-zinc-200 block truncate max-w-[80px]">{item.name}</span>
                </div>
              </div>
            );
          })}
        </div>

        <div className="pt-3 border-t border-zinc-800/80 flex items-center justify-between text-xs text-zinc-400">
          <span className="flex items-center space-x-1.5 font-mono">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Zero manual setup required</span>
          </span>
          <span className="font-semibold text-indigo-400">Fully Automated Swarm Execution</span>
        </div>
      </div>
    </div>
  );
};
