'use client';

import React from 'react';
import { 
  BookOpen, Terminal, Layers, ExternalLink, 
  CreditCard, Compass, MessageSquare, ShieldCheck 
} from 'lucide-react';

const resources = [
  { title: 'Getting Started Guide', desc: '5-minute onboarding & CLI setup.', icon: BookOpen, href: '#' },
  { title: 'Documentation & API Spec', desc: 'OpenAPI 3.0 REST endpoint reference.', icon: Terminal, href: '#' },
  { title: 'Architecture Topology', desc: 'Hexagonal multi-agent design specs.', icon: Layers, href: '#' },
  { title: 'Pricing & Enterprise Plans', desc: 'Transparent usage quota tiers.', icon: CreditCard, href: '#' },
  { title: 'Product Roadmap 2026', desc: 'Upcoming features & autonomous capabilities.', icon: Compass, href: '#' },
  { title: 'Developer Community', desc: 'Join our Discord server & GitHub Discussions.', icon: MessageSquare, href: '#' },
  { title: 'Privacy & Security Audit', desc: 'SOC2 & AST sandboxing policies.', icon: ShieldCheck, href: '#' },
];

export const ResourceLinks: React.FC = () => {
  return (
    <div className="space-y-4">
      <div className="space-y-1">
        <h3 className="text-xs font-extrabold uppercase tracking-widest text-indigo-400">
          Resources & Links
        </h3>
        <h4 className="text-xl font-extrabold text-white">
          Explore Platform Documentation & Community
        </h4>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
        {resources.map((res, idx) => {
          const Icon = res.icon;
          return (
            <a
              key={idx}
              href={res.href}
              className="group p-4 rounded-2xl bg-zinc-900/60 border border-zinc-800/80 hover:border-indigo-500/40 backdrop-blur-xl transition-all duration-300 hover:-translate-y-0.5 space-y-2 flex flex-col justify-between"
            >
              <div className="flex justify-between items-start">
                <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 group-hover:scale-110 transition">
                  <Icon className="h-4 w-4" />
                </div>
                <ExternalLink className="h-3.5 w-3.5 text-zinc-500 group-hover:text-indigo-400 transition" />
              </div>
              <div>
                <h5 className="font-bold text-xs text-zinc-100 group-hover:text-indigo-300 transition">
                  {res.title}
                </h5>
                <p className="text-[11px] text-zinc-400 mt-1 leading-snug">
                  {res.desc}
                </p>
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
};
