'use client';

import React from 'react';
import { useDashboard } from '../context/DashboardContext';
import { Layers, Zap, Trash2, Info } from 'lucide-react';

export const CacheView: React.FC = () => {
  const { cacheMetrics, refreshData, useMockData } = useDashboard();

  if (!cacheMetrics) {
    return <div className="p-8 text-center text-muted-foreground">Loading caching metrics...</div>;
  }

  // Handle invalidate cache
  const handleInvalidateLLMCache = async () => {
    try {
      if (useMockData) {
        alert("LLM Cache invalidated (Mock Mode).");
        refreshData();
        return;
      }
      // Simple POST request to invalidation URL
      await fetch(`http://127.0.0.1:8000/metrics/cache/invalidate`, { method: 'POST' }).catch(() => {});
      alert("LLM prompt hash cache invalidated.");
      refreshData();
    } catch (err) {
      const error = err as Error;
      alert("Failed to invalidate cache: " + error.message);
    }
  };

  const handleInvalidateToolCache = async () => {
    try {
      if (useMockData) {
        alert("Tool Cache invalidated (Mock Mode).");
        refreshData();
        return;
      }
      await fetch(`http://127.0.0.1:8000/metrics/cache/invalidate`, { method: 'POST' }).catch(() => {});
      alert("Tool execution cache invalidated.");
      refreshData();
    } catch (err) {
      const error = err as Error;
      alert("Failed to invalidate cache: " + error.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Caching Optimization Layer</h1>
        <p className="text-muted-foreground">Monitor cache rates and latency savings for LLM calls and tool executions.</p>
      </div>

      {/* Caching Panel split */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* LLM Prompt Hash Cache Panel */}
        <div className="bg-card text-card-foreground border rounded-xl p-6 shadow-sm flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <div className="flex items-center space-x-2">
                <Zap className="h-5 w-5 text-yellow-500" />
                <h2 className="font-bold text-base">LLM Prompt Cache</h2>
              </div>
              <span className="text-[10px] uppercase font-bold text-muted-foreground px-2 py-0.5 border rounded bg-muted">
                Prompt SHA256 Key
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-muted/30 border rounded-lg p-3 text-center">
                <span className="text-[10px] text-muted-foreground uppercase font-bold">Cache Hit Rate</span>
                <span className="text-2xl font-black text-yellow-500 block mt-1">
                  {(cacheMetrics.llm_cache.hit_rate * 100).toFixed(1)}%
                </span>
              </div>
              <div className="bg-muted/30 border rounded-lg p-3 text-center">
                <span className="text-[10px] text-muted-foreground uppercase font-bold">Cached Prompts</span>
                <span className="text-2xl font-black text-foreground block mt-1">
                  {cacheMetrics.llm_cache.size}
                </span>
              </div>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Cache Hits count:</span>
                <span className="font-semibold text-emerald-500">{cacheMetrics.llm_cache.hits}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Cache Misses count:</span>
                <span className="font-semibold text-rose-500">{cacheMetrics.llm_cache.misses}</span>
              </div>
            </div>
          </div>

          <button
            onClick={handleInvalidateLLMCache}
            className="flex items-center justify-center space-x-2 border border-rose-500/30 text-rose-500 hover:bg-rose-500/10 py-2.5 rounded-lg text-sm font-semibold transition"
          >
            <Trash2 className="h-4 w-4" />
            <span>Invalidate LLM Cache</span>
          </button>
        </div>

        {/* Tool Execution Cache Panel */}
        <div className="bg-card text-card-foreground border rounded-xl p-6 shadow-sm flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <div className="flex items-center space-x-2">
                <Layers className="h-5 w-5 text-indigo-500" />
                <h2 className="font-bold text-base">Tool Execution Cache</h2>
              </div>
              <span className="text-[10px] uppercase font-bold text-muted-foreground px-2 py-0.5 border rounded bg-muted">
                Read-Only Tools
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-muted/30 border rounded-lg p-3 text-center">
                <span className="text-[10px] text-muted-foreground uppercase font-bold">Cache Hit Rate</span>
                <span className="text-2xl font-black text-indigo-500 block mt-1">
                  {(cacheMetrics.tool_cache.hit_rate * 100).toFixed(1)}%
                </span>
              </div>
              <div className="bg-muted/30 border rounded-lg p-3 text-center">
                <span className="text-[10px] text-muted-foreground uppercase font-bold">Latency Saved</span>
                <span className="text-2xl font-black text-emerald-500 block mt-1">
                  {(cacheMetrics.tool_cache.latency_saved_ms / 1000).toFixed(1)}s
                </span>
              </div>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Cache Hits count:</span>
                <span className="font-semibold text-emerald-500">{cacheMetrics.tool_cache.hits}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Cache Misses count:</span>
                <span className="font-semibold text-rose-500">{cacheMetrics.tool_cache.misses}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Cached Tool Signatures:</span>
                <span className="font-semibold">{cacheMetrics.tool_cache.size}</span>
              </div>
            </div>
          </div>

          <button
            onClick={handleInvalidateToolCache}
            className="flex items-center justify-center space-x-2 border border-rose-500/30 text-rose-500 hover:bg-rose-500/10 py-2.5 rounded-lg text-sm font-semibold transition"
          >
            <Trash2 className="h-4 w-4" />
            <span>Invalidate Tool Cache</span>
          </button>
        </div>

      </div>

      {/* Info Warning */}
      <div className="bg-muted/40 border rounded-xl p-4 flex items-start space-x-2 text-xs text-muted-foreground">
        <Info className="h-4 w-4 text-primary shrink-0 mt-0.5" />
        <p>
          Prompt caches hash input tokens to avoid redundant generation costs on duplicate prompts. Tool cache operates strictly on idempotent operations: web searches, file reads, and vector memory queries.
        </p>
      </div>

    </div>
  );
};
