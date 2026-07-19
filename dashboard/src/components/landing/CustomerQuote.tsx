'use client';

import React from 'react';
import { Quote } from 'lucide-react';

export const CustomerQuote: React.FC = () => {
  return (
    <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-900/20 via-purple-900/20 to-zinc-900/60 border border-indigo-500/30 backdrop-blur-xl space-y-3 shadow-xl relative overflow-hidden">
      <div className="absolute top-0 right-0 p-4 opacity-10 text-indigo-400">
        <Quote className="h-24 w-24" />
      </div>

      <div className="flex items-center space-x-2 text-indigo-400 text-xs font-bold uppercase tracking-wider">
        <Quote className="h-4 w-4" />
        <span>Enterprise Customer Testimonial</span>
      </div>

      <p className="text-base sm:text-lg font-medium text-zinc-100 italic leading-relaxed relative z-10">
        &ldquo;CodeOrbit AI reduced our software delivery time from six months to five days. It plans, codes, tests, and deploys autonomously without requiring full engineering teams.&rdquo;
      </p>

      <div className="flex items-center space-x-3 pt-2 relative z-10">
        <div className="h-10 w-10 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-white text-sm">
          TS
        </div>
        <div>
          <h5 className="font-bold text-sm text-white">Chief Executive Officer</h5>
          <p className="text-xs text-indigo-300">TechScale Systems Inc.</p>
        </div>
      </div>
    </div>
  );
};
