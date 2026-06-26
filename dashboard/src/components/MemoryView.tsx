'use client';

import React, { useState } from 'react';
import { useDashboard } from '../context/DashboardContext';
import { api, MemorySearchItem } from '../lib/api';
import * as mock from '../lib/mockData';
import { Search, Database, Layers, Eye, BookOpen, AlertCircle } from 'lucide-react';

export const MemoryView: React.FC = () => {
  const { useMockData } = useDashboard();
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [limit, setLimit] = useState<number>(3);
  const [searchResults, setSearchResults] = useState<MemorySearchItem[]>(mock.mockMemorySearch);
  const [searching, setSearching] = useState<boolean>(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearching(true);
    setSearchError(null);

    try {
      if (useMockData) {
        await new Promise(resolve => setTimeout(resolve, 200));
        // Filter mock results on query matching
        const filtered = mock.mockMemorySearch.filter(item => 
          item.text.toLowerCase().includes(searchQuery.toLowerCase())
        );
        setSearchResults(filtered.length > 0 ? filtered : mock.mockMemorySearch);
        return;
      }
      const res = await api.searchMemory(searchQuery, limit);
      setSearchResults(res);
    } catch (err) {
      const error = err as Error;
      setSearchError(error.message || "Failed to search vector index.");
      setSearchResults(mock.mockMemorySearch); // Fallback to mock
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">Semantic Memory Explorer</h1>
        <p className="text-muted-foreground">Search and audit long-term vector embeddings and memory stores.</p>
      </div>

      {/* Grid: Search controls vs Vector Database Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Search Panel */}
        <div className="bg-card text-card-foreground border rounded-xl p-6 shadow-sm lg:col-span-2 space-y-4">
          <div className="flex items-center space-x-2 border-b pb-3">
            <Database className="h-5 w-5 text-primary" />
            <h2 className="font-bold text-base">Query Vector Store</h2>
          </div>
          
          <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="e.g. distributed workers locks safety..."
                className="w-full bg-background border rounded-lg pl-9 pr-4 py-2.5 text-sm focus:ring-1 focus:ring-primary outline-none"
              />
            </div>
            
            <div className="flex gap-2">
              <select
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="bg-background border rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-primary outline-none"
              >
                <option value={3}>Limit: 3</option>
                <option value={5}>Limit: 5</option>
                <option value={10}>Limit: 10</option>
              </select>
              
              <button
                type="submit"
                disabled={searching || !searchQuery.trim()}
                className="bg-primary text-primary-foreground font-semibold text-sm px-6 py-2.5 rounded-lg hover:bg-primary/95 disabled:opacity-50 transition shrink-0"
              >
                {searching ? 'Querying Index...' : 'Search Index'}
              </button>
            </div>
          </form>

          {searchError && (
            <div className="text-xs text-rose-500 flex items-center space-x-1"><AlertCircle className="h-3.5 w-3.5" /><span>{searchError}</span></div>
          )}

          {/* Search Result lists */}
          <div className="space-y-4 pt-2">
            <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Similarity Search Results</h3>
            {searchResults.length === 0 ? (
              <div className="p-8 text-center text-sm text-muted-foreground bg-muted/20 border border-dashed rounded-lg">No memory nodes match your query.</div>
            ) : (
              searchResults.map((item, index) => (
                <div key={index} className="bg-muted/30 border rounded-lg p-4 space-y-3 relative hover:bg-muted/40 transition">
                  <p className="text-sm font-medium leading-relaxed pr-24">{item.text}</p>
                  
                  {/* Metadata labels */}
                  <div className="flex flex-wrap gap-2 items-center text-xs">
                    <span className="bg-primary/10 text-primary px-2 py-0.5 rounded font-mono">
                      Source: {(item.metadata.source as string) || 'N/A'}
                    </span>
                    {typeof item.metadata.doc_type === 'string' && (
                      <span className="bg-emerald-500/10 text-emerald-500 px-2 py-0.5 rounded uppercase font-semibold text-[10px]">
                        Type: {item.metadata.doc_type}
                      </span>
                    )}
                    <span className="text-muted-foreground text-[10px]">
                      Indexed: {new Date(item.timestamp).toLocaleDateString()}
                    </span>
                  </div>

                  {/* Score badge */}
                  <div className="absolute right-4 top-4 flex flex-col items-center">
                    <span className="text-[10px] text-muted-foreground uppercase font-bold">Similarity</span>
                    <span className="text-sm font-extrabold text-primary">{(item.similarity * 100).toFixed(1)}%</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Info Panel */}
        <div className="bg-card text-card-foreground border rounded-xl p-6 shadow-sm space-y-6">
          <div>
            <div className="flex items-center space-x-2 border-b pb-3 mb-4">
              <Layers className="h-5 w-5 text-indigo-500" />
              <h2 className="font-bold text-base">Long-Term Storage</h2>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Consolidated execution summary logs are vector embedded using <strong>text-embedding-004</strong> and stored in a local persistent semantic store.
            </p>
          </div>

          <div className="space-y-4">
            <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center space-x-1">
              <BookOpen className="h-4 w-4 text-indigo-500" />
              <span>Consolidation Workflow</span>
            </h3>
            <ol className="text-xs text-muted-foreground space-y-3 list-decimal list-inside">
              <li>Logs and chat lines are captured during executions.</li>
              <li>Completed task memory is gathered.</li>
              <li>A summary vector model generates memory nodes.</li>
              <li>Embeddings are registered for similarity matching.</li>
            </ol>
          </div>

          <div className="bg-indigo-500/10 rounded-xl p-4 border border-indigo-500/20 text-xs flex items-start space-x-2">
            <Eye className="h-4 w-4 text-indigo-500 shrink-0 mt-0.5" />
            <p className="text-indigo-500">
              Embedding recall matches semantically rather than exact string queries. Queries match conceptual topics.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
};
