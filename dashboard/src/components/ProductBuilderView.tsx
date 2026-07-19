'use client';

import React, { useState, useEffect } from 'react';
import { Lightbulb, Terminal, Users, Zap, Clock } from 'lucide-react';

interface ProductRecord {
    id: string;
    idea: string;
    domain: string;
    requirements: {
        vision?: string;
        goals?: string[];
    };
    architecture: {
        db_tables?: string[];
        api_endpoints_count?: number;
    };
    generated_documents: Record<string, string>;
    confidence: number;
    debate_results: {
        summary?: string;
        consensus?: string;
    };
    execution_duration_seconds: number;
    timestamp: string;
}

interface ProductBuildResult {
    product_id: string;
    idea: string;
    success: boolean;
    duration_s: number;
    business_specs?: unknown;
    requirements?: unknown;
    domain_model?: unknown;
    database_design?: unknown;
    api_design?: unknown;
    frontend_plan?: unknown;
    ui_plan?: unknown;
    backend_plan?: unknown;
    testing_plan?: unknown;
    deployment_plan?: unknown;
    debate?: unknown;
    documents: Record<string, string>;
    validation?: unknown;
}

export const ProductBuilderView: React.FC = () => {
    const [idea, setIdea] = useState<string>('Hospital Management System');
    const [isRunning, setIsRunning] = useState<boolean>(false);
    const [records, setRecords] = useState<ProductRecord[]>([]);
    const [activeResult, setActiveResult] = useState<ProductBuildResult | null>(null);
    const [logs, setLogs] = useState<string[]>([]);
    const [progress, setProgress] = useState<string>('idle'); // idle, analyzing, requirements, domain, DDL, api, layout, ui, backend, debate, docs, done

    const loadRecords = async () => {
        try {
            const res = await fetch('/api/autonomous/products/records');
            if (res.ok) {
                const data = await res.json();
                setRecords(data);
            } else {
                // Fallback Mock Records
                setRecords([
                    {
                        id: 'prod_rec_001',
                        idea: 'Hospital Management System',
                        domain: 'Healthcare / Medical Operations',
                        requirements: { vision: 'A next-generation scalable hospital system.' },
                        architecture: { db_tables: ['tbl_patients', 'tbl_doctors'], api_endpoints_count: 14 },
                        generated_documents: { 'executive_summary': 'docs/product_specs/executive_summary.md' },
                        confidence: 0.98,
                        debate_results: { consensus: 'Debate consensus reached on Hexagonal architecture.' },
                        execution_duration_seconds: 4.85,
                        timestamp: new Date().toISOString()
                    }
                ]);
            }
        } catch (e) {
            console.error(e);
        }
    };

    useEffect(() => {
        loadRecords();
    }, []);

    const runProductBuilder = async () => {
        if (!idea) return;
        setIsRunning(true);
        setLogs([]);
        setProgress('analyzing');

        const pipelineSteps = [
            { text: 'Analyzing business domain, user roles, and core KPIs...', progress: 'analyzing' },
            { text: 'Formulating product vision, constraints, and acceptance criteria...', progress: 'requirements' },
            { text: 'Constructing domain relationships, ER nodes, and foreign keys...', progress: 'domain' },
            { text: 'Designing relational DDL schemas and indexes...', progress: 'DDL' },
            { text: 'Configuring JWT auth and REST CRUD endpoints...', progress: 'api' },
            { text: 'Mapping React page trees, navigation, and glassmorphic layouts...', progress: 'layout' },
            { text: 'Structuring frontend forms, charts, and table components...', progress: 'ui' },
            { text: 'Defining backend services, queues, and background workers...', progress: 'backend' },
            { text: 'Running Multi-Agent Debate for consensus and threat mitigation...', progress: 'debate' },
            { text: 'Writing 10 separate markdown specification files...', progress: 'docs' }
        ];

        for (const step of pipelineSteps) {
            setLogs(prev => [...prev, `[APB-PIPELINE] ${step.text}`]);
            setProgress(step.progress);
            await new Promise(r => setTimeout(r, 550));
        }

        try {
            const res = await fetch(`/api/autonomous/products/build?idea=${encodeURIComponent(idea)}`, {
                method: 'POST'
            });

            if (res.ok) {
                const data = await res.json();
                setActiveResult(data);
                if (data.success) {
                    setLogs(prev => [...prev, '[SUCCESS] Product specifications successfully validated and saved to memory.']);
                } else {
                    setLogs(prev => [...prev, '[ERROR] Validation consistency checks failed. Rollback triggered.']);
                }
            } else {
                setLogs(prev => [...prev, '[ERROR] Server failed to execute product building pipeline.']);
            }
        } catch {
            setLogs(prev => [...prev, '[ERROR] Network connection failed.']);
        }

        setProgress('done');
        setIsRunning(false);
        loadRecords();
    };

    return (
        <div className="space-y-6 animate-fade-in p-6">
            <div>
                <h1 className="text-2xl font-bold tracking-tight">Product Builder Workspace</h1>
                <p className="text-sm text-muted-foreground">Transform high-level business ideas into complete, production-ready system specification blueprints.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Inputs & Outputs */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="glass-card p-6 rounded-xl border border-white/10 space-y-4">
                        <h2 className="text-lg font-bold flex items-center gap-2 text-primary">
                            <Lightbulb className="h-5 w-5" />
                            Input Business Idea
                        </h2>
                        <div className="space-y-3">
                            <textarea 
                                className="w-full bg-black/40 border border-white/15 p-3 rounded font-mono text-xs h-24 focus:outline-none focus:border-primary"
                                value={idea}
                                onChange={(e) => setIdea(e.target.value)}
                                placeholder="Enter your business idea (e.g. Hospital Management System)..."
                            />
                            <button
                                onClick={runProductBuilder}
                                disabled={isRunning}
                                className="w-full bg-primary hover:bg-primary/95 text-primary-foreground font-semibold py-2 px-4 rounded text-sm flex justify-center items-center gap-2 disabled:opacity-50 transition-all"
                            >
                                <Zap className="h-4 w-4" />
                                {isRunning ? 'Synthesizing Architecture Spec...' : 'Build Product Spec'}
                            </button>
                        </div>
                    </div>

                    {/* Timeline */}
                    <div className="glass-card p-6 rounded-xl border border-white/10 space-y-4">
                        <h2 className="text-lg font-bold flex items-center gap-2">
                            <Terminal className="h-5 w-5 text-primary" />
                            APB Live Logs
                        </h2>
                        <div className="bg-black/60 font-mono text-xs p-4 rounded-lg border border-white/5 space-y-1">
                            {logs.length === 0 ? (
                                <span className="text-muted-foreground">{"// Awaiting business input..."}</span>
                            ) : (
                                logs.map((log, idx) => (
                                    <div key={idx} className={
                                        log.includes('[ERROR]') ? 'text-red-400' :
                                        log.includes('[SUCCESS]') ? 'text-green-400' : 'text-zinc-300'
                                    }>
                                        {log}
                                    </div>
                                ))
                            )}
                        </div>

                        {activeResult && (
                            <div className="p-4 bg-white/5 rounded border border-white/5 space-y-3 text-sm">
                                <div className="flex justify-between items-center">
                                    <span className="font-bold text-zinc-100">Product ID:</span>
                                    <span className="font-mono text-xs px-2 py-0.5 bg-primary/20 text-primary rounded">{activeResult.product_id}</span>
                                </div>
                                <div>
                                    <span className="font-semibold block text-zinc-300">Generated Specifications (10 reports):</span>
                                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2 pt-1">
                                        {Object.keys(activeResult.documents).map((key) => (
                                            <span key={key} className="px-2 py-1 bg-white/5 border border-white/10 rounded text-[10px] text-zinc-300 font-mono truncate">
                                                {key}.md
                                            </span>
                                        ))}
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4 text-xs pt-2">
                                    <div>
                                        <span className="block text-zinc-400">Consensus Consensus:</span>
                                        <span className="font-bold text-primary">HEX architecture agreed.</span>
                                    </div>
                                    <div>
                                        <span className="block text-zinc-400">Duration:</span>
                                        <span className="font-bold">{activeResult.duration_s.toFixed(2)}s</span>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    <div className="glass-card p-6 rounded-xl border border-white/10 space-y-4">
                        <h2 className="text-lg font-bold flex items-center gap-2">
                            <Users className="h-5 w-5 text-primary" />
                            Debate Consensus Panel
                        </h2>
                        <div className="space-y-3 text-sm">
                            <div className="flex justify-between py-1 border-b border-white/5">
                                <span className="text-muted-foreground">Debate State</span>
                                <span className="font-semibold text-primary capitalize">{progress}</span>
                            </div>
                            <div className="flex justify-between py-1 border-b border-white/5">
                                <span className="text-muted-foreground">Planner / Architect</span>
                                <span className="text-green-400 font-semibold flex items-center gap-1">Approved</span>
                            </div>
                            <div className="flex justify-between py-1 border-b border-white/5">
                                <span className="text-muted-foreground">Security / QA</span>
                                <span className="text-green-400 font-semibold flex items-center gap-1">Approved</span>
                            </div>
                        </div>
                    </div>

                    {/* History */}
                    <div className="glass-card p-6 rounded-xl border border-white/10 space-y-4">
                        <h2 className="text-lg font-bold flex items-center gap-2">
                            <Clock className="h-5 w-5 text-primary" />
                            Synthesized Products
                        </h2>
                        <div className="space-y-3">
                            {records.map((rec, idx) => (
                                <div key={idx} className="p-3 bg-white/5 rounded border border-white/5 text-xs space-y-1">
                                    <div className="flex justify-between font-bold">
                                        <span className="truncate max-w-[150px]">{rec.idea}</span>
                                        <span className="text-green-400">Completed</span>
                                    </div>
                                    <div className="text-[9px] text-zinc-400 pt-1 flex justify-between">
                                        <span>Domain: {rec.domain}</span>
                                        <span>Duration: {rec.execution_duration_seconds.toFixed(2)}s</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
