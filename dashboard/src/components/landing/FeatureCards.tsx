'use client';

import React from 'react';
import { 
  Wand2, Bot, Code2, ShieldCheck, 
  TestTube2, FileText, GitBranch, Cloud 
} from 'lucide-react';

interface FeatureItem {
  icon: React.ElementType;
  title: string;
  description: string;
  accent: string;
}

const features: FeatureItem[] = [
  {
    icon: Wand2,
    title: 'AI Product Planning',
    description: 'Deconstructs natural language ideas into PRD specifications, user stories, and acceptance criteria.',
    accent: 'from-indigo-500/20 to-purple-500/20 text-indigo-400 border-indigo-500/30'
  },
  {
    icon: Bot,
    title: 'Multi-Agent Discussion',
    description: 'Planner, Architect, Developer, Security, and QA agents collaborate until 100% consensus is achieved.',
    accent: 'from-blue-500/20 to-indigo-500/20 text-blue-400 border-blue-500/30'
  },
  {
    icon: Code2,
    title: 'Automatic Source Coding',
    description: 'Scaffolds Next.js 15, FastAPI controllers, PostgreSQL ORM schemas, and Docker configs on disk.',
    accent: 'from-emerald-500/20 to-teal-500/20 text-emerald-400 border-emerald-500/30'
  },
  {
    icon: ShieldCheck,
    title: 'AI Security & Code Review',
    description: 'Enforces AST vulnerability boundary policies, Bandit scans, and strict type safety.',
    accent: 'from-purple-500/20 to-pink-500/20 text-purple-400 border-purple-500/30'
  },
  {
    icon: TestTube2,
    title: 'Automated QA & Self-Healing',
    description: 'Runs backend Pytest & frontend build matrixes, automatically patching stack traces upon failure.',
    accent: 'from-amber-500/20 to-orange-500/20 text-amber-400 border-amber-500/30'
  },
  {
    icon: FileText,
    title: 'Documentation Synthesis',
    description: 'Generates 10 structured Markdown specs including ER diagrams, OpenAPI contracts, and PRDs.',
    accent: 'from-cyan-500/20 to-blue-500/20 text-cyan-400 border-cyan-500/30'
  },
  {
    icon: GitBranch,
    title: 'GitHub Repository Creation',
    description: 'Initializes Git tracking, creates remote repositories, pushes releases, and builds CHANGELOGs.',
    accent: 'from-pink-500/20 to-rose-500/20 text-pink-400 border-pink-500/30'
  },
  {
    icon: Cloud,
    title: 'CI/CD & Cloud Provisioning',
    description: 'Deploys containerized services to Vercel, Railway, Cloud Run, and AWS with active telemetry.',
    accent: 'from-violet-500/20 to-indigo-500/20 text-violet-400 border-violet-500/30'
  }
];

export const FeatureCards: React.FC = () => {
  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <h3 className="text-xs font-extrabold uppercase tracking-widest text-indigo-400">
          Autonomous Engineering Core
        </h3>
        <h4 className="text-xl font-extrabold text-white">
          Full Lifecycle Software Automation
        </h4>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
        {features.map((item, idx) => {
          const Icon = item.icon;
          return (
            <div
              key={idx}
              className="group relative p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800/80 hover:border-indigo-500/40 backdrop-blur-xl transition-all duration-300 hover:shadow-xl hover:shadow-indigo-500/5 hover:-translate-y-0.5 space-y-2.5"
            >
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-xl bg-gradient-to-br ${item.accent} border shadow-inner transition group-hover:scale-110 duration-300`}>
                  <Icon className="h-4 w-4" />
                </div>
                <h5 className="font-bold text-sm text-zinc-100 group-hover:text-indigo-300 transition">
                  {item.title}
                </h5>
              </div>
              <p className="text-xs text-zinc-400 leading-relaxed font-normal">
                {item.description}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
