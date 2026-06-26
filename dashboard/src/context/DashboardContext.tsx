'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api, TaskModel, AgentMetadata, WorkerInfo, QueueStatus, SystemMetrics, CacheMetrics } from '../lib/api';
import * as mock from '../lib/mockData';

interface DashboardContextType {
  darkMode: boolean;
  setDarkMode: (dark: boolean) => void;
  useMockData: boolean;
  setUseMockData: (mock: boolean) => void;
  apiUrl: string;
  setApiUrl: (url: string) => void;
  
  // Dynamic Global State fetched from API (or Mock)
  agents: AgentMetadata[];
  tasks: TaskModel[];
  workers: WorkerInfo[];
  queueStatus: QueueStatus | null;
  metrics: SystemMetrics | null;
  cacheMetrics: CacheMetrics | null;
  
  loading: boolean;
  error: string | null;
  refreshData: () => Promise<void>;
  
  // Active selected elements
  selectedTaskId: string | null;
  setSelectedTaskId: (id: string | null) => void;
}

const DashboardContext = createContext<DashboardContextType | undefined>(undefined);

export const DashboardProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [darkMode, setDarkMode] = useState<boolean>(true);
  const [useMockData, setUseMockData] = useState<boolean>(true); // Default to mock data first for safety
  const [apiUrl, setApiUrl] = useState<string>('http://127.0.0.1:8000');
  
  const [agents, setAgents] = useState<AgentMetadata[]>(mock.mockAgents);
  const [tasks, setTasks] = useState<TaskModel[]>(mock.mockTasks);
  const [workers, setWorkers] = useState<WorkerInfo[]>(mock.mockWorkers);
  const [queueStatus, setQueueStatus] = useState<QueueStatus | null>(mock.mockQueueStatus);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(mock.mockMetrics);
  const [cacheMetrics, setCacheMetrics] = useState<CacheMetrics | null>(mock.mockCacheMetrics);
  
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>("task_fa2b98e1");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Sync settings with local storage on startup
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedDark = localStorage.getItem('dashboard_dark');
      const savedMock = localStorage.getItem('dashboard_mock');
      const savedApi = localStorage.getItem('dashboard_api_url');
      
      if (savedDark !== null) {
        setDarkMode(savedDark === 'true');
      } else {
        // Default to dark mode for rich premium aesthetics!
        setDarkMode(true);
      }
      
      if (savedMock !== null) {
        setUseMockData(savedMock === 'true');
      }
      
      if (savedApi !== null) {
        setApiUrl(savedApi);
      }
    }
  }, []);

  // Update theme class on HTML element
  useEffect(() => {
    const root = window.document.documentElement;
    if (darkMode) {
      root.classList.add('dark');
      localStorage.setItem('dashboard_dark', 'true');
    } else {
      root.classList.remove('dark');
      localStorage.setItem('dashboard_dark', 'false');
    }
  }, [darkMode]);

  // Update localStorage when settings change
  useEffect(() => {
    localStorage.setItem('dashboard_mock', String(useMockData));
  }, [useMockData]);

  useEffect(() => {
    localStorage.setItem('dashboard_api_url', apiUrl);
    if (typeof window !== 'undefined') {
      (window as unknown as Record<string, string>).NEXT_PUBLIC_API_URL = apiUrl;
    }
  }, [apiUrl]);

  const refreshData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    if (useMockData) {
      // Simulate slight network latency
      await new Promise(resolve => setTimeout(resolve, 300));
      setAgents(mock.mockAgents);
      setTasks(mock.mockTasks);
      setWorkers(mock.mockWorkers);
      setQueueStatus(mock.mockQueueStatus);
      setMetrics(mock.mockMetrics);
      setCacheMetrics(mock.mockCacheMetrics);
      setLoading(false);
      return;
    }

    try {
      const [agentsData, tasksData, workersData, queueData, metricsData, cacheData] = await Promise.all([
        api.getAgents().catch(() => mock.mockAgents),
        api.getTasks().catch(() => mock.mockTasks),
        api.getWorkers().catch(() => mock.mockWorkers),
        api.getQueueStatus().catch(() => mock.mockQueueStatus),
        api.getMetrics().catch(() => mock.mockMetrics),
        api.getCache().catch(() => mock.mockCacheMetrics)
      ]);

      setAgents(agentsData);
      setTasks(tasksData);
      setWorkers(workersData);
      setQueueStatus(queueData);
      setMetrics(metricsData);
      setCacheMetrics(cacheData);
    } catch (err) {
      const error = err as Error;
      console.error("Dashboard refresh error: ", error);
      setError(error.message || "Failed to load live data from backend api.");
      // Fallback automatically to mock data if connection fails
      setUseMockData(true);
    } finally {
      setLoading(false);
    }
  }, [useMockData, apiUrl]);

  // Run periodic auto-refresh of states
  useEffect(() => {
    refreshData();
    const interval = setInterval(() => {
      refreshData();
    }, 5000); // refresh every 5 seconds
    
    return () => clearInterval(interval);
  }, [refreshData]);

  return (
    <DashboardContext.Provider value={{
      darkMode, setDarkMode,
      useMockData, setUseMockData,
      apiUrl, setApiUrl,
      agents, tasks, workers, queueStatus, metrics, cacheMetrics,
      loading, error, refreshData,
      selectedTaskId, setSelectedTaskId
    }}>
      {children}
    </DashboardContext.Provider>
  );
};

export const useDashboard = () => {
  const context = useContext(DashboardContext);
  if (context === undefined) {
    throw new Error('useDashboard must be used within a DashboardProvider');
  }
  return context;
};
