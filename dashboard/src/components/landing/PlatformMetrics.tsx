'use client';

import React from 'react';
import { Bot, Layers, CheckCircle2, Cloud, ShieldCheck } from 'lucide-react';

const metrics = [
  { label: 'AI Agents', value: '120+', icon: Bot, color: 'text-indigo-400' },
  { label: 'Repositories Generated', value: '1,500+', icon: Layers, color: 'text-purple-400' },
  { label: 'Test Success Rate', value: '98%', icon: CheckCircle2, color: 'text-emerald-400' },
  { label: 'Deployments Today', value: '35+', icon: Cloud, color: 'text-blue-400' },
  { label: 'Platform Uptime', value: '99.9%', icon: ShieldCheck, color: 'text-teal-400' }
];

export const PlatformMetrics: React.FC = () => {
  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <h3 className="text-xs font-extrabold uppercase tracking-widest text-indigo-400">
          Scale & Proven Performance
        </h3>
        <h4 className="text-xl font-extrabold text-white">
          Platform Metrics & Impact
        </h4>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {metrics.map((item, idx) => {
          const Icon = item.icon;
          return (
            <div
              key={idx}
              className="p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800/80 backdrop-blur-xl space-y-1 text-center hover:border-indigo-500/30 transition group shadow-sm"
            >
              <div className="flex justify-center mb-1">
                <Icon className={`h-4 w-4 ${item.color} group-hover:scale-110 transition`} />
              </div>
              <div className="text-2xl font-extrabold text-white tracking-tight font-mono">{item.value}</div>
              <div className="text-[11px] text-zinc-400 font-semibold">{item.label}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
