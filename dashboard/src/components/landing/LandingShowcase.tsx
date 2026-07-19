'use client';

import React from 'react';
import { Sparkles, Layers, ArrowUpRight } from 'lucide-react';
import { FeatureCards } from './FeatureCards';
import { WorkflowTimeline } from './WorkflowTimeline';
import { VisionSection } from './VisionSection';
import { TechStackGrid } from './TechStackGrid';
import { PlatformMetrics } from './PlatformMetrics';
import { CustomerQuote } from './CustomerQuote';
import { ResourceLinks } from './ResourceLinks';

export const LandingShowcase: React.FC = () => {
  return (
    <div className="space-y-12 pr-0 lg:pr-8 py-6">
      
      {/* Keynote Header & Hero Headline */}
      <div className="space-y-4">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold animate-pulse">
          <Sparkles className="h-4 w-4" />
          <span>CodeOrbit AI — Autonomous AI Software Engineering Platform</span>
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-white leading-[1.1]">
          Build production software with <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">autonomous AI engineers.</span>
        </h1>

        <p className="text-base sm:text-lg text-zinc-300 leading-relaxed max-w-3xl font-normal">
          CodeOrbit AI is not another chat copilot. It is an autonomous software company inside your browser that plans business requirements, conducts multi-agent architectural debates, writes production source code, executes test matrixes, commits to GitHub, and deploys to cloud infrastructure automatically.
        </p>

        <div className="flex flex-wrap gap-3 pt-2">
          <a
            href="#features"
            className="px-4 py-2 rounded-xl bg-zinc-900 border border-zinc-800 hover:border-indigo-500/40 text-xs font-bold text-zinc-200 transition flex items-center space-x-1.5"
          >
            <Layers className="h-4 w-4 text-indigo-400" />
            <span>Explore Engineering Engine</span>
          </a>
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="px-4 py-2 rounded-xl bg-indigo-600/10 border border-indigo-500/30 text-indigo-300 text-xs font-bold transition flex items-center space-x-1 hover:bg-indigo-600/20"
          >
            <span>GitHub Repository</span>
            <ArrowUpRight className="h-3.5 w-3.5" />
          </a>
        </div>
      </div>

      {/* Feature Cards Grid */}
      <div id="features">
        <FeatureCards />
      </div>

      {/* 9-Stage Workflow Timeline */}
      <WorkflowTimeline />

      {/* Vision, Mission & Philosophy */}
      <VisionSection />

      {/* Platform Scale Metrics */}
      <PlatformMetrics />

      {/* Tech Stack Grid */}
      <TechStackGrid />

      {/* Customer Quote */}
      <CustomerQuote />

      {/* Resource & Documentation Links */}
      <ResourceLinks />

    </div>
  );
};
