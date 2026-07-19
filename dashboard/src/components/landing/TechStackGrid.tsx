'use client';

import React from 'react';

const techBadges = [
  { name: 'Next.js 15', category: 'Frontend' },
  { name: 'TypeScript', category: 'Language' },
  { name: 'Python 3.12', category: 'Backend' },
  { name: 'FastAPI', category: 'REST API' },
  { name: 'Gemini 1.5 Pro', category: 'AI Intelligence' },
  { name: 'Claude 3.5 Sonnet', category: 'Reasoning' },
  { name: 'OpenAI GPT-4o', category: 'LLM Orchestration' },
  { name: 'Docker', category: 'Containers' },
  { name: 'Kubernetes', category: 'Infrastructure' },
  { name: 'GitHub Actions', category: 'CI/CD' },
  { name: 'PostgreSQL 16', category: 'Database' },
  { name: 'Redis', category: 'Cache' },
  { name: 'Qdrant Vector DB', category: 'Memory' },
  { name: 'Stripe', category: 'Payments' },
  { name: 'Vercel Edge', category: 'Hosting' },
  { name: 'AWS Cloud', category: 'Infrastructure' },
  { name: 'Cloudflare', category: 'CDN & Security' }
];

export const TechStackGrid: React.FC = () => {
  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <h3 className="text-xs font-extrabold uppercase tracking-widest text-indigo-400">
          Under the Hood
        </h3>
        <h4 className="text-xl font-extrabold text-white">
          Powered by Industry-Standard Tech Stack
        </h4>
      </div>

      <div className="flex flex-wrap gap-2">
        {techBadges.map((tech, idx) => (
          <div
            key={idx}
            className="px-3 py-1.5 rounded-xl bg-zinc-900/80 border border-zinc-800 hover:border-indigo-500/40 text-xs font-semibold text-zinc-300 hover:text-white transition-all duration-200 shadow-sm flex items-center space-x-2 group hover:scale-105 cursor-default"
          >
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 group-hover:bg-purple-400 transition" />
            <span>{tech.name}</span>
            <span className="text-[10px] text-zinc-500 font-mono font-normal">({tech.category})</span>
          </div>
        ))}
      </div>
    </div>
  );
};
