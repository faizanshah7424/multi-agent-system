'use client';

import React from 'react';
import { Rocket, Zap, Brain } from 'lucide-react';

export const VisionSection: React.FC = () => {
  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <h3 className="text-xs font-extrabold uppercase tracking-widest text-indigo-400">
          Core Principles
        </h3>
        <h4 className="text-xl font-extrabold text-white">
          Vision, Mission & AI Philosophy
        </h4>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
        <div className="p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800/80 backdrop-blur-xl space-y-2 hover:border-indigo-500/40 transition">
          <div className="flex items-center space-x-2 text-indigo-400">
            <Rocket className="h-4 w-4" />
            <h5 className="font-extrabold text-xs uppercase tracking-wider">🚀 Vision</h5>
          </div>
          <p className="text-xs text-zinc-300 leading-relaxed font-semibold">
            Build the world&apos;s first Autonomous Software Company in the browser.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800/80 backdrop-blur-xl space-y-2 hover:border-indigo-500/40 transition">
          <div className="flex items-center space-x-2 text-emerald-400">
            <Zap className="h-4 w-4" />
            <h5 className="font-extrabold text-xs uppercase tracking-wider">⚡ Mission</h5>
          </div>
          <p className="text-xs text-zinc-300 leading-relaxed font-semibold">
            Empower entrepreneurs to launch enterprise products without multi-million dollar engineering budgets.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800/80 backdrop-blur-xl space-y-2 hover:border-indigo-500/40 transition">
          <div className="flex items-center space-x-2 text-purple-400">
            <Brain className="h-4 w-4" />
            <h5 className="font-extrabold text-xs uppercase tracking-wider">🧠 AI Philosophy</h5>
          </div>
          <p className="text-xs text-zinc-300 leading-relaxed font-semibold">
            Humans make high-level product decisions. AI handles complete technical execution.
          </p>
        </div>
      </div>
    </div>
  );
};
