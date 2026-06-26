'use client';

import React, { useState } from 'react';
import { useDashboard } from '../context/DashboardContext';
import { Save, AlertTriangle, HelpCircle, Wifi, RefreshCw } from 'lucide-react';

export const SettingsView: React.FC = () => {
  const { 
    darkMode, setDarkMode, 
    useMockData, setUseMockData, 
    apiUrl, setApiUrl,
    refreshData 
  } = useDashboard();

  const [inputUrl, setInputUrl] = useState<string>(apiUrl);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  const handleSaveSettings = (e: React.FormEvent) => {
    e.preventDefault();
    setApiUrl(inputUrl);
    setSaveSuccess(true);
    setTimeout(() => {
      setSaveSuccess(false);
      refreshData();
    }, 1500);
  };

  const handleResetMetrics = async () => {
    try {
      if (useMockData) {
        alert("Metrics reset simulation triggered.");
        return;
      }
      await fetch(`${apiUrl}/metrics/reset`, { method: 'POST' }).catch(() => {});
      alert("Metrics registries cleared.");
      refreshData();
    } catch (err) {
      const error = err as Error;
      alert("Failed to reset metrics: " + error.message);
    }
  };

  return (
    <div className="max-w-3xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">System Settings</h1>
        <p className="text-muted-foreground">Adjust telemetry variables, toggle endpoints, and manage local storage configurations.</p>
      </div>

      <div className="bg-card text-card-foreground border rounded-xl p-6 shadow-sm space-y-6">
        
        {/* Toggle Mode */}
        <div className="flex items-center justify-between border-b pb-4">
          <div className="space-y-1">
            <span className="font-bold text-sm">Offline Mock Data Mode</span>
            <p className="text-xs text-muted-foreground">
              Fallback mode toggling between simulated datasets and live backend connections.
            </p>
          </div>
          <button
            onClick={() => setUseMockData(!useMockData)}
            className={`w-14 h-7 rounded-full p-1 transition-colors duration-200 focus:outline-none ${useMockData ? 'bg-primary' : 'bg-muted'}`}
          >
            <div className={`w-5 h-5 rounded-full bg-white transition-transform duration-200 ${useMockData ? 'translate-x-7' : 'translate-x-0'}`} />
          </button>
        </div>

        {/* Dark Mode */}
        <div className="flex items-center justify-between border-b pb-4">
          <div className="space-y-1">
            <span className="font-bold text-sm">Visual Dark Theme</span>
            <p className="text-xs text-muted-foreground">
              Toggles between light slate layouts and premium carbon dark interfaces.
            </p>
          </div>
          <button
            onClick={() => setDarkMode(!darkMode)}
            className={`w-14 h-7 rounded-full p-1 transition-colors duration-200 focus:outline-none ${darkMode ? 'bg-primary' : 'bg-muted'}`}
          >
            <div className={`w-5 h-5 rounded-full bg-white transition-transform duration-200 ${darkMode ? 'translate-x-7' : 'translate-x-0'}`} />
          </button>
        </div>

        {/* API Config Form */}
        <form onSubmit={handleSaveSettings} className="space-y-4">
          <div className="flex items-center space-x-2">
            <Wifi className="h-5 w-5 text-primary" />
            <span className="font-bold text-sm">FastAPI Connection Configuration</span>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              placeholder="http://127.0.0.1:8000"
              className="flex-1 bg-background border rounded-lg px-3.5 py-2 text-sm focus:ring-1 focus:ring-primary outline-none"
            />
            <button
              type="submit"
              className="flex items-center justify-center space-x-2 bg-primary text-primary-foreground text-sm font-semibold px-6 py-2 rounded-lg hover:bg-primary/95 transition"
            >
              <Save className="h-4 w-4" />
              <span>Save Configuration</span>
            </button>
          </div>
          {saveSuccess && (
            <p className="text-xs text-emerald-500 font-semibold animate-pulse">API base URL updated successfully!</p>
          )}
        </form>

        {/* Dangerous Reset Commands */}
        <div className="pt-4 border-t space-y-4">
          <div className="flex items-center space-x-2 text-rose-500">
            <AlertTriangle className="h-5 w-5" />
            <span className="font-bold text-sm">Danger Actions Zone</span>
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <button
              onClick={handleResetMetrics}
              className="flex items-center justify-center space-x-2 border border-rose-500 text-rose-500 hover:bg-rose-500/10 px-4 py-2.5 rounded-lg text-xs font-semibold transition"
            >
              <RefreshCw className="h-4 w-4" />
              <span>Reset Accumulators</span>
            </button>
          </div>
        </div>

      </div>

      {/* Info card */}
      <div className="bg-card border rounded-xl p-6 shadow-sm space-y-3">
        <h3 className="font-bold text-sm flex items-center space-x-1.5">
          <HelpCircle className="h-4 w-4 text-primary" />
          <span>Dashboard Information</span>
        </h3>
        <p className="text-xs text-muted-foreground leading-relaxed">
          This dashboard integrates with the Python FastAPI Multi-Agent system. It maps thread execution lists, long-term memory registries, and prompt-saving caches.
        </p>
      </div>

    </div>
  );
};
