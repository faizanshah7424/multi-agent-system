'use client';

import React, { useState } from 'react';
import { DashboardProvider, useDashboard } from '../context/DashboardContext';
import { OverviewView } from './OverviewView';
import { TasksView } from './TasksView';
import { AgentsView } from './AgentsView';
import { MemoryView } from './MemoryView';
import { QueueView } from './QueueView';
import { CostsView } from './CostsView';
import { CacheView } from './CacheView';
import { SettingsView } from './SettingsView';
import { AutonomousView } from './AutonomousView';
import { EngineeringView } from './EngineeringView';
import { FeatureView } from './FeatureView';
import { RepositoryView } from './RepositoryView';
import { ProductBuilderView } from './ProductBuilderView';
import { AdminPanelView } from './AdminPanelView';
import { NotificationsView } from './NotificationsView';
import { HospitalView } from './HospitalView';
import { NewProjectView } from './NewProjectView';
import { 
  Activity, Users, CreditCard, Cpu, Database, 
  Layers, Zap, Settings, Sun, Moon, 
  Menu, X, RefreshCw, Lightbulb, LogOut, Shield, Bell, Heart,
  Wand2, Cloud
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

type ViewType = 
  | 'new_project'
  | 'overview' 
  | 'tasks' 
  | 'agents' 
  | 'memory' 
  | 'autonomous' 
  | 'engineering' 
  | 'feature' 
  | 'repository_engineer' 
  | 'product_builder' 
  | 'queue' 
  | 'costs' 
  | 'cache' 
  | 'settings'
  | 'admin_panel'
  | 'notifications'
  | 'hospital';

const DashboardContent: React.FC = () => {
  const [activeView, setActiveView] = useState<ViewType>('new_project');
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);
  const [devMode, setDevMode] = useState<boolean>(false);
  const { darkMode, setDarkMode, useMockData, loading, refreshData } = useDashboard();
  const { user, logout } = useAuth();

  const userMenuItems = [
    { id: 'new_project', name: 'New Project', icon: Wand2 },
    { id: 'repository_engineer', name: 'Projects', icon: Layers },
    { id: 'overview', name: 'Dashboard', icon: Cpu },
    { id: 'autonomous', name: 'Deployments', icon: Cloud },
    { id: 'settings', name: 'Settings', icon: Settings },
  ];

  const devMenuItems = [
    { id: 'tasks', name: 'Task Queue', icon: Activity },
    { id: 'memory', name: 'Memory Explorer', icon: Database },
    { id: 'agents', name: 'Agent Registry', icon: Users },
    { id: 'engineering', name: 'Engineering Center', icon: Activity },
    { id: 'feature', name: 'Feature Center', icon: Cpu },
    { id: 'product_builder', name: 'Product Builder', icon: Lightbulb },
    { id: 'queue', name: 'Queue Monitor', icon: Layers },
    { id: 'costs', name: 'Analytics & Costs', icon: CreditCard },
    { id: 'cache', name: 'Cache Analytics', icon: Zap },
    { id: 'notifications', name: 'Notifications Center', icon: Bell },
    { id: 'hospital', name: 'Hospital Hub', icon: Heart },
  ];

  const menuItems = [...userMenuItems];
  if (devMode) {
    menuItems.push(...devMenuItems);
  }

  if (user && user.role === 'admin') {
    menuItems.push({ id: 'admin_panel', name: 'Admin', icon: Shield });
  }

  const renderView = () => {
    switch (activeView) {
      case 'new_project': return <NewProjectView />;
      case 'overview': return <OverviewView />;
      case 'tasks': return <TasksView />;
      case 'agents': return <AgentsView />;
      case 'memory': return <MemoryView />;
      case 'autonomous': return <AutonomousView />;
      case 'engineering': return <EngineeringView />;
      case 'feature': return <FeatureView />;
      case 'repository_engineer': return <RepositoryView />;
      case 'product_builder': return <ProductBuilderView />;
      case 'queue': return <QueueView />;
      case 'costs': return <CostsView />;
      case 'cache': return <CacheView />;
      case 'settings': return <SettingsView />;
      case 'admin_panel': return <AdminPanelView />;
      case 'notifications': return <NotificationsView />;
      case 'hospital': return <HospitalView />;
      default: return <NewProjectView />;
    }
  };

  const handleMenuClick = (id: ViewType) => {
    setActiveView(id);
    setMobileMenuOpen(false);
  };

  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col lg:flex-row">
      
      {/* Sidebar - Desktop Layout */}
      <aside className="hidden lg:flex lg:flex-col lg:w-64 bg-card border-r shrink-0 h-screen sticky top-0 z-20">
        
        {/* Sidebar Header Brand */}
        <div className="p-5 border-b flex items-center space-x-3 shrink-0">
          <div className="p-2 rounded-lg bg-primary text-primary-foreground shrink-0">
            <Activity className="h-5 w-5" />
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="font-extrabold text-sm uppercase tracking-wider block truncate">CodeOrbit AI</h1>
            <span className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest block truncate">Agent Telemetry</span>
          </div>
        </div>

        {/* Sidebar Navigation Links */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto" aria-label="Main Navigation">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const active = activeView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleMenuClick(item.id as ViewType)}
                aria-label={`Navigate to ${item.name}`}
                aria-current={active ? 'page' : undefined}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-semibold transition focus-visible:ring-2 focus-visible:ring-primary ${
                  active 
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                }`}
              >
                <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                <span className="truncate">{item.name}</span>
              </button>
            );
          })}
        </nav>

        {/* Sidebar Footer details */}
        <div className="p-4 border-t bg-muted/20 shrink-0 text-xs text-muted-foreground flex flex-col space-y-2.5">
          <div className="flex justify-between items-center">
            <span className="font-semibold">Developer Mode:</span>
            <button
              onClick={() => setDevMode(!devMode)}
              className={`px-2 py-0.5 rounded text-[10px] font-bold transition ${
                devMode
                  ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                  : 'bg-muted text-muted-foreground border border-border'
              }`}
            >
              {devMode ? 'ON' : 'OFF'}
            </button>
          </div>
          <div className="flex justify-between items-center text-[10px]">
            <span>Server Link:</span>
            <span className={`px-2 py-0.5 rounded font-bold ${
              useMockData 
                ? 'bg-yellow-500/10 text-yellow-600 border border-yellow-500/20' 
                : 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20'
            }`}>
              {useMockData ? 'Mock Mode' : 'Connected'}
            </span>
          </div>
          <p className="text-[10px] leading-tight">CodeOrbit AI v2.0 Platform.</p>
        </div>
      </aside>

      {/* Main viewport Container */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        
        {/* Global top navigation Header */}
        <header className="h-16 border-b bg-card flex items-center justify-between px-6 shrink-0 sticky top-0 z-10 shadow-sm">
          
          {/* Mobile menu trigger */}
          <div className="flex items-center space-x-4 lg:hidden">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="p-1.5 rounded-lg border text-muted-foreground hover:bg-muted"
            >
              <Menu className="h-5 w-5" />
            </button>
            <span className="font-extrabold text-sm uppercase tracking-wider block">CodeOrbit AI</span>
          </div>

          {/* Space fillers on Desktop */}
          <div className="hidden lg:flex items-center space-x-2 text-xs">
            <span className="text-muted-foreground">Mode:</span>
            <span className={`px-2 py-0.5 rounded font-mono font-bold uppercase ${
              useMockData 
                ? 'bg-yellow-500/10 text-yellow-500' 
                : 'bg-emerald-500/10 text-emerald-500'
            }`}>
              {useMockData ? 'SIMULATOR MODE (OFFLINE)' : 'LIVE CONNECTION'}
            </span>
          </div>

          {/* Action buttons (Refresh timer, Dark mode toggles) */}
          <div className="flex items-center space-x-4">
            {user && (
              <div className="flex items-center space-x-2 border-r pr-4 border-zinc-800">
                <div className="flex flex-col text-right hidden sm:flex">
                  <span className="text-xs font-semibold text-zinc-200">{user.email}</span>
                  <span className="text-[10px] text-zinc-400 capitalize">{user.role}</span>
                </div>
                <div className="h-8 w-8 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center font-bold text-xs text-indigo-400 uppercase">
                  {user.email ? user.email.substring(0, 2) : 'US'}
                </div>
              </div>
            )}
            
            <button
              onClick={() => refreshData()}
              disabled={loading}
              className={`p-2 rounded-lg border text-muted-foreground hover:bg-muted transition shrink-0 ${loading ? 'animate-spin' : ''}`}
              title="Refresh telemetry values"
            >
              <RefreshCw className="h-4 w-4" />
            </button>

            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-lg border text-muted-foreground hover:bg-muted transition shrink-0"
              title="Toggle design mode theme"
            >
              {darkMode ? <Sun className="h-4 w-4 text-yellow-500" /> : <Moon className="h-4 w-4" />}
            </button>

            {user && (
              <button
                onClick={() => logout()}
                className="p-2 rounded-lg border border-red-500/20 text-red-400 hover:bg-red-500/10 hover:text-red-300 transition shrink-0"
                title="Logout"
              >
                <LogOut className="h-4 w-4" />
              </button>
            )}
          </div>
        </header>

        {/* Dynamic sub-view viewport */}
        <main className="flex-1 p-6 bg-background/50 min-w-0">
          {renderView()}
        </main>
      </div>

      {/* Sidebar - Mobile Slide drawer */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          {/* Backdrop shadow overlay */}
          <div 
            className="fixed inset-0 bg-zinc-950/60 backdrop-blur-sm"
            onClick={() => setMobileMenuOpen(false)}
          />
          
          {/* Drawer container */}
          <div className="relative w-64 bg-card border-r h-full flex flex-col p-4 animate-in slide-in-from-left duration-200 z-10">
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center space-x-2">
                <div className="p-1.5 rounded-lg bg-primary text-primary-foreground">
                  <Activity className="h-4 w-4" />
                </div>
                <span className="font-extrabold text-sm uppercase tracking-wider">CodeOrbit AI</span>
              </div>
              <button
                onClick={() => setMobileMenuOpen(false)}
                className="p-1 rounded-lg border text-muted-foreground hover:bg-muted"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            
            <nav className="flex-grow space-y-1 overflow-y-auto">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const active = activeView === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => handleMenuClick(item.id as ViewType)}
                    className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-semibold transition ${
                      active 
                        ? 'bg-primary text-primary-foreground shadow-sm'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    }`}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span>{item.name}</span>
                  </button>
                );
              })}
            </nav>
          </div>
        </div>
      )}

    </div>
  );
};

export const DashboardLayout: React.FC = () => {
  return (
    <DashboardProvider>
      <DashboardContent />
    </DashboardProvider>
  );
};
