'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useDashboard } from '../context/DashboardContext';
import { api, NotificationItem, NotificationPreferences, NotificationQueueItem, NotificationStats } from '../lib/api';
import { 
  Bell, Mail, Settings, ShieldAlert, CheckCircle2, 
  AlertTriangle, Info, Play, RefreshCw, Send, Loader2,
  ToggleLeft, ToggleRight, Radio
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

// MOCK DATA for local offline testing
const mockPrefs: NotificationPreferences = {
  email_enabled: true,
  sms_enabled: false,
  in_app_enabled: true,
  marketing_emails: false,
  security_alerts: true,
  task_updates: true
};

const mockNotifications: NotificationItem[] = [
  { id: 'n1', title: 'Security Hardening Alert', message: 'New developer login detected from IP 192.168.1.150.', type: 'warning', category: 'security', is_read: false, created_at: '2026-07-10T18:00:00Z', read_at: null },
  { id: 'n2', title: 'Task Executed Successfully', message: 'Workflow task "deploy_agent_registry" completed in 1.45s.', type: 'success', category: 'task', is_read: true, created_at: '2026-07-10T17:45:00Z', read_at: '2026-07-10T17:46:00Z' },
  { id: 'n3', title: 'Welcome to Orbit', message: 'Start building your multi-agent workspaces today.', type: 'info', category: 'general', is_read: false, created_at: '2026-07-10T12:00:00Z', read_at: null }
];

const mockStats: NotificationStats = {
  in_app: { total: 3, unread: 2 },
  queue: { total: 24, pending: 0, sent: 21, failed: 2, retrying: 1 },
  channels: { email: 16, sms: 8 },
  recent_queue: [
    { id: 'q1', channel: 'email', recipient: 'dev@orbit.ai', title: 'Task Failure Report', content: 'Task "database_sync" failed FAIL_TEST', status: 'retrying', attempts: 2, error_message: 'Simulated SMTP Connection Error', created_at: '2026-07-10T18:20:00Z' },
    { id: 'q2', channel: 'sms', recipient: '+15550199222', title: null, content: 'Urgent security alert: MFA enabled for user admin@orbit.ai.', status: 'sent', attempts: 1, error_message: null, created_at: '2026-07-10T18:15:00Z' },
    { id: 'q3', channel: 'email', recipient: 'user@orbit.ai', title: 'Marketing Newsletter', content: 'Checkout the new features in Orbit 2.0!', status: 'failed', attempts: 3, error_message: 'Simulated SMTP Connection Error', created_at: '2026-07-10T17:00:00Z' }
  ]
};

export const NotificationsView: React.FC = () => {
  const { useMockData } = useDashboard();
  const { user } = useAuth();
  
  const [activeTab, setActiveTab] = useState<'center' | 'preferences' | 'dashboard'>('center');
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  const [stats, setStats] = useState<NotificationStats | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [savingPrefs, setSavingPrefs] = useState(false);
  const [processingQueue, setProcessingQueue] = useState(false);
  const [sendingTest, setSendingTest] = useState(false);
  
  // Test Form States
  const [testTitle, setTestTitle] = useState('Workspace Update Alert');
  const [testMessage, setTestMessage] = useState('A new agent task has completed successfully.');
  const [testCategory, setTestCategory] = useState('task');
  const [testChannel, setTestChannel] = useState('all');
  const [testForceFailure, setTestForceFailure] = useState(false);
  
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchNotificationData = useCallback(async () => {
    setLoading(true);
    setMessage(null);
    try {
      if (useMockData) {
        setNotifications(mockNotifications);
        setPreferences(mockPrefs);
        setStats(mockStats);
      } else {
        const [notifList, prefData, statsData] = await Promise.all([
          api.getNotifications(false),
          api.getNotificationPreferences(),
          (user?.role === 'admin' || user?.role === 'developer') ? api.getNotificationStats() : Promise.resolve(null)
        ]);
        setNotifications(notifList);
        setPreferences(prefData);
        setStats(statsData);
      }
    } catch (err) {
      console.error(err);
      const msg = err instanceof Error ? err.message : 'Failed to sync notifications.';
      setMessage({ type: 'error', text: msg });
    } finally {
      setLoading(false);
    }
  }, [useMockData, user]);

  useEffect(() => {
    fetchNotificationData();
  }, [fetchNotificationData]);

  const handleRead = async (notifId: string) => {
    try {
      if (useMockData) {
        setNotifications(prev => prev.map(n => n.id === notifId ? { ...n, is_read: true, read_at: new Date().toISOString() } : n));
        setMessage({ type: 'success', text: 'Marked notification as read.' });
      } else {
        await api.readNotification(notifId);
        const list = await api.getNotifications(false);
        setNotifications(list);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to update status.';
      setMessage({ type: 'error', text: msg });
    }
  };

  const handleReadAll = async () => {
    try {
      if (useMockData) {
        setNotifications(prev => prev.map(n => ({ ...n, is_read: true, read_at: new Date().toISOString() })));
        setMessage({ type: 'success', text: 'All notifications marked as read.' });
      } else {
        await api.readAllNotifications();
        const list = await api.getNotifications(false);
        setNotifications(list);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to update status.';
      setMessage({ type: 'error', text: msg });
    }
  };

  const handleSavePreferences = async (updatedPrefs: Partial<NotificationPreferences>) => {
    if (!preferences) return;
    setSavingPrefs(true);
    setMessage(null);
    const newPrefs = { ...preferences, ...updatedPrefs };
    try {
      if (useMockData) {
        setPreferences(newPrefs);
        setMessage({ type: 'success', text: 'Preferences updated locally.' });
      } else {
        const response = await api.updateNotificationPreferences(newPrefs);
        setPreferences(response.preferences);
        setMessage({ type: 'success', text: 'Preferences saved on backend.' });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to save preferences.';
      setMessage({ type: 'error', text: msg });
    } finally {
      setSavingPrefs(false);
    }
  };

  const handleTriggerQueue = async () => {
    setProcessingQueue(true);
    setMessage(null);
    try {
      if (useMockData) {
        // Simulate queue worker processing
        setTimeout(() => {
          if (stats) {
            const updatedRecent = stats.recent_queue.map(item => {
              if (item.status === 'retrying') {
                return { ...item, status: 'sent', attempts: item.attempts + 1, error_message: null };
              }
              return item;
            });
            setStats({
              ...stats,
              queue: { ...stats.queue, pending: 0, retrying: 0, sent: stats.queue.sent + 1 },
              recent_queue: updatedRecent
            });
          }
          setMessage({ type: 'success', text: 'Queue worker executed. Failed notification retried successfully.' });
          setProcessingQueue(false);
        }, 1000);
      } else {
        const response = await api.triggerProcessQueue();
        const statsData = await api.getNotificationStats();
        setStats(statsData);
        setMessage({ type: 'success', text: response.message });
        setProcessingQueue(false);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to process queue.';
      setMessage({ type: 'error', text: msg });
      setProcessingQueue(false);
    }
  };

  const handleSendTest = async (e: React.FormEvent) => {
    e.preventDefault();
    setSendingTest(true);
    setMessage(null);
    try {
      if (useMockData) {
        // Mock add notification
        const newNotif: NotificationItem = {
          id: 'test_' + Math.random().toString(36).substr(2, 4),
          title: testTitle,
          message: testMessage + (testForceFailure ? ' FAIL_TEST' : ''),
          type: 'info',
          category: testCategory,
          is_read: false,
          created_at: new Date().toISOString(),
          read_at: null
        };
        setNotifications([newNotif, ...notifications]);
        
        // Mock update stats if admin
        if (stats) {
          const newQueueItem: NotificationQueueItem = {
            id: 'q_' + Math.random().toString(36).substr(2, 4),
            channel: testChannel === 'all' ? 'email' : testChannel,
            recipient: testChannel === 'sms' ? '+15550199123' : 'user@orbit.ai',
            title: testTitle,
            content: testMessage + (testForceFailure ? ' FAIL_TEST' : ''),
            status: testForceFailure ? 'retrying' : 'sent',
            attempts: 1,
            error_message: testForceFailure ? 'Simulated Connection Error' : null,
            created_at: new Date().toISOString()
          };
          setStats({
            ...stats,
            queue: {
              ...stats.queue,
              total: stats.queue.total + 1,
              sent: stats.queue.sent + (testForceFailure ? 0 : 1),
              retrying: stats.queue.retrying + (testForceFailure ? 1 : 0)
            },
            recent_queue: [newQueueItem, ...stats.recent_queue]
          });
        }
        
        setMessage({ type: 'success', text: 'Test notification dispatched.' });
      } else {
        const payload = {
          title: testTitle,
          message: testMessage,
          category: testCategory,
          channel: testChannel === 'all' ? undefined : testChannel,
          force_failure: testForceFailure
        };
        await api.triggerTestNotification(payload);
        
        // Refresh Lists
        const [notifList, statsData] = await Promise.all([
          api.getNotifications(false),
          (user?.role === 'admin' || user?.role === 'developer') ? api.getNotificationStats() : Promise.resolve(null)
        ]);
        setNotifications(notifList);
        if (statsData) setStats(statsData);
        setMessage({ type: 'success', text: 'Test notification dispatched successfully.' });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to send test notification.';
      setMessage({ type: 'error', text: msg });
    } finally {
      setSendingTest(false);
    }
  };

  const getNotifIcon = (type: string) => {
    switch (type) {
      case 'success': return <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />;
      case 'warning': return <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0" />;
      case 'error': return <ShieldAlert className="h-5 w-5 text-rose-500 shrink-0" />;
      default: return <Info className="h-5 w-5 text-indigo-400 shrink-0" />;
    }
  };

  const isManagementPrivileged = user?.role === 'admin' || user?.role === 'developer';

  return (
    <div className="space-y-6">
      
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center">
            <Bell className="h-6 w-6 text-indigo-400 mr-2.5 animate-bounce" />
            Communication & Notifications Hub
          </h2>
          <p className="text-sm text-zinc-400 mt-1">
            Read in-app alerts, adjust delivery channels, and manage SMTP/SMS queue workers.
          </p>
        </div>
      </div>

      {/* Message Notifications */}
      {message && (
        <div className={`p-4 rounded-xl border flex items-start space-x-3 text-sm animate-in fade-in duration-200 ${
          message.type === 'success' 
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
            : 'bg-red-500/10 border-red-500/20 text-red-400'
        }`}>
          {message.type === 'success' ? <CheckCircle2 className="h-5 w-5 shrink-0" /> : <ShieldAlert className="h-5 w-5 shrink-0" />}
          <span>{message.text}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-zinc-800 space-x-2">
        <button
          onClick={() => setActiveTab('center')}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
            activeTab === 'center' ? 'border-indigo-500 text-indigo-400 font-bold' : 'border-transparent text-zinc-400 hover:text-zinc-200'
          } flex items-center space-x-2`}
        >
          <Bell className="h-4 w-4" />
          <span>Notification Center</span>
          {notifications.filter(n => !n.is_read).length > 0 && (
            <span className="bg-indigo-600 text-white text-[10px] px-1.5 py-0.5 rounded-full font-bold ml-1">
              {notifications.filter(n => !n.is_read).length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('preferences')}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
            activeTab === 'preferences' ? 'border-indigo-500 text-indigo-400 font-bold' : 'border-transparent text-zinc-400 hover:text-zinc-200'
          } flex items-center space-x-2`}
        >
          <Settings className="h-4 w-4" />
          <span>Preferences & Channels</span>
        </button>
        {isManagementPrivileged && (
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
              activeTab === 'dashboard' ? 'border-indigo-500 text-indigo-400 font-bold' : 'border-transparent text-zinc-400 hover:text-zinc-200'
            } flex items-center space-x-2`}
          >
            <Radio className="h-4 w-4 animate-pulse" />
            <span>Worker Queue Dashboard</span>
          </button>
        )}
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="flex flex-col items-center space-y-3">
            <Loader2 className="h-10 w-10 text-indigo-500 animate-spin" />
            <span className="text-sm text-zinc-400">Loading communication registers...</span>
          </div>
        </div>
      ) : (
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl p-6 shadow-xl backdrop-blur-md animate-in fade-in duration-300">
          
          {/* TAB 1: NOTIFICATION CENTER (IN-APP INBOX) */}
          {activeTab === 'center' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-bold text-white flex items-center">
                  <Bell className="h-5 w-5 text-indigo-400 mr-2" />
                  Your Notifications Inbox
                </h3>
                {notifications.filter(n => !n.is_read).length > 0 && (
                  <button
                    onClick={handleReadAll}
                    className="text-xs text-indigo-400 hover:text-indigo-300 font-medium transition hover:underline"
                  >
                    Mark all as read
                  </button>
                )}
              </div>

              {notifications.length === 0 ? (
                <div className="text-center py-12 text-zinc-500 space-y-2">
                  <Bell className="h-12 w-12 text-zinc-700 mx-auto" />
                  <p className="text-sm font-semibold">Your inbox is completely clear.</p>
                  <p className="text-xs text-zinc-600">We&apos;ll alert you here when tasks execute or logins occur.</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
                  {notifications.map(notif => (
                    <div
                      key={notif.id}
                      className={`p-4 rounded-xl border transition flex items-start justify-between space-x-4 ${
                        notif.is_read 
                          ? 'bg-zinc-950/20 border-zinc-800/60 opacity-75' 
                          : 'bg-zinc-900/80 border-indigo-500/20 hover:border-indigo-500/35'
                      }`}
                    >
                      <div className="flex items-start space-x-3.5">
                        {getNotifIcon(notif.type)}
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-sm text-zinc-100">{notif.title}</span>
                            <span className="text-[9px] uppercase font-bold tracking-widest px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">
                              {notif.category}
                            </span>
                            {!notif.is_read && (
                              <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-ping shrink-0" />
                            )}
                          </div>
                          <p className="text-xs text-zinc-400 leading-relaxed">{notif.message}</p>
                          <span className="text-[10px] text-zinc-500 block">
                            {new Date(notif.created_at).toLocaleString()}
                          </span>
                        </div>
                      </div>
                      
                      {!notif.is_read && (
                        <button
                          onClick={() => handleRead(notif.id)}
                          className="text-xs font-semibold text-zinc-400 hover:text-white transition px-2.5 py-1 bg-zinc-800/80 hover:bg-zinc-800 rounded-lg"
                        >
                          Mark Read
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: PREFERENCES & CHANNELS */}
          {activeTab === 'preferences' && preferences && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center">
                  <Settings className="h-5 w-5 text-indigo-400 mr-2" />
                  Preferences & Gateway Configurations
                </h3>
                <p className="text-xs text-zinc-400 mt-1">Opt in or out of notification types and direct contact channels.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                
                {/* Left Side: Contact Channels Toggles */}
                <div className="space-y-4">
                  <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest border-b border-zinc-800 pb-2">Active Channels</h4>
                  
                  <div className="space-y-4 bg-zinc-950/40 border border-zinc-800/80 rounded-xl p-4">
                    {/* In-app Toggle */}
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="block text-sm font-bold text-zinc-200">In-App Alerts</span>
                        <span className="block text-[11px] text-zinc-400">Receive inbox alerts directly on this dashboard.</span>
                      </div>
                      <button
                        onClick={() => handleSavePreferences({ in_app_enabled: !preferences.in_app_enabled })}
                        disabled={savingPrefs}
                        className="transition text-zinc-300 hover:text-white"
                      >
                        {preferences.in_app_enabled ? <ToggleRight className="h-6 w-6 text-indigo-500" /> : <ToggleLeft className="h-6 w-6 text-zinc-600" />}
                      </button>
                    </div>

                    {/* Email Toggle */}
                    <div className="flex items-center justify-between border-t border-zinc-800/60 pt-4">
                      <div>
                        <span className="block text-sm font-bold text-zinc-200">Email Gateway</span>
                        <span className="block text-[11px] text-zinc-400">Dispatches details via SMTP notifications.</span>
                      </div>
                      <button
                        onClick={() => handleSavePreferences({ email_enabled: !preferences.email_enabled })}
                        disabled={savingPrefs}
                        className="transition text-zinc-300 hover:text-white"
                      >
                        {preferences.email_enabled ? <ToggleRight className="h-6 w-6 text-indigo-500" /> : <ToggleLeft className="h-6 w-6 text-zinc-600" />}
                      </button>
                    </div>

                    {/* SMS Toggle */}
                    <div className="flex items-center justify-between border-t border-zinc-800/60 pt-4">
                      <div>
                        <span className="block text-sm font-bold text-zinc-200">SMS Gateway alerts</span>
                        <span className="block text-[11px] text-zinc-400">Receive instant telemetry updates on your phone.</span>
                      </div>
                      <button
                        onClick={() => handleSavePreferences({ sms_enabled: !preferences.sms_enabled })}
                        disabled={savingPrefs}
                        className="transition text-zinc-300 hover:text-white"
                      >
                        {preferences.sms_enabled ? <ToggleRight className="h-6 w-6 text-indigo-500" /> : <ToggleLeft className="h-6 w-6 text-zinc-600" />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Right Side: Message Categories Toggles */}
                <div className="space-y-4">
                  <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest border-b border-zinc-800 pb-2">Topic Categories</h4>
                  
                  <div className="space-y-4 bg-zinc-950/40 border border-zinc-800/80 rounded-xl p-4">
                    {/* Security Alerts */}
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="block text-sm font-bold text-zinc-200 flex items-center">
                          <ShieldAlert className="h-4 w-4 text-rose-500 mr-1.5" />
                          Security Alerts
                        </span>
                        <span className="block text-[11px] text-zinc-400">Login warnings, MFA updates, and key changes.</span>
                      </div>
                      <button
                        onClick={() => handleSavePreferences({ security_alerts: !preferences.security_alerts })}
                        disabled={savingPrefs}
                        className="transition text-zinc-300 hover:text-white"
                      >
                        {preferences.security_alerts ? <ToggleRight className="h-6 w-6 text-indigo-500" /> : <ToggleLeft className="h-6 w-6 text-zinc-600" />}
                      </button>
                    </div>

                    {/* Task Updates */}
                    <div className="flex items-center justify-between border-t border-zinc-800/60 pt-4">
                      <div>
                        <span className="block text-sm font-bold text-zinc-200 flex items-center">
                          <Play className="h-4 w-4 text-emerald-400 mr-1.5" />
                          Workflow Task execution reports
                        </span>
                        <span className="block text-[11px] text-zinc-400">Notifications when agent workflows finish.</span>
                      </div>
                      <button
                        onClick={() => handleSavePreferences({ task_updates: !preferences.task_updates })}
                        disabled={savingPrefs}
                        className="transition text-zinc-300 hover:text-white"
                      >
                        {preferences.task_updates ? <ToggleRight className="h-6 w-6 text-indigo-500" /> : <ToggleLeft className="h-6 w-6 text-zinc-600" />}
                      </button>
                    </div>

                    {/* Marketing Emails */}
                    <div className="flex items-center justify-between border-t border-zinc-800/60 pt-4">
                      <div>
                        <span className="block text-sm font-bold text-zinc-200 flex items-center">
                          <Mail className="h-4 w-4 text-indigo-400 mr-1.5" />
                          Marketing Announcements
                        </span>
                        <span className="block text-[11px] text-zinc-400">Newsletters, tips, and feature additions.</span>
                      </div>
                      <button
                        onClick={() => handleSavePreferences({ marketing_emails: !preferences.marketing_emails })}
                        disabled={savingPrefs}
                        className="transition text-zinc-300 hover:text-white"
                      >
                        {preferences.marketing_emails ? <ToggleRight className="h-6 w-6 text-indigo-500" /> : <ToggleLeft className="h-6 w-6 text-zinc-600" />}
                      </button>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          )}

          {/* TAB 3: WORKER QUEUE MONITOR & METRICS */}
          {activeTab === 'dashboard' && isManagementPrivileged && stats && (
            <div className="space-y-8 animate-in fade-in duration-300">
              
              {/* Metrics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                
                {/* Pending */}
                <div className="bg-zinc-950/40 border border-zinc-800 p-4 rounded-xl flex flex-col justify-between">
                  <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-widest">Pending</span>
                  <div className="flex items-baseline space-x-2 mt-2">
                    <span className="text-2xl font-bold text-amber-400">{stats.queue.pending}</span>
                    <span className="text-xs text-zinc-400">items</span>
                  </div>
                </div>

                {/* Retrying */}
                <div className="bg-zinc-950/40 border border-zinc-800 p-4 rounded-xl flex flex-col justify-between">
                  <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-widest">Retrying</span>
                  <div className="flex items-baseline space-x-2 mt-2">
                    <span className="text-2xl font-bold text-indigo-400">{stats.queue.retrying}</span>
                    <span className="text-xs text-zinc-400">items</span>
                  </div>
                </div>

                {/* Sent (Success) */}
                <div className="bg-zinc-950/40 border border-zinc-800 p-4 rounded-xl flex flex-col justify-between">
                  <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-widest">Sent (Success)</span>
                  <div className="flex items-baseline space-x-2 mt-2">
                    <span className="text-2xl font-bold text-emerald-400">{stats.queue.sent}</span>
                    <span className="text-xs text-zinc-400">items</span>
                  </div>
                </div>

                {/* Perm Failed */}
                <div className="bg-zinc-950/40 border border-zinc-800 p-4 rounded-xl flex flex-col justify-between">
                  <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-widest">Perm Failed</span>
                  <div className="flex items-baseline space-x-2 mt-2">
                    <span className="text-2xl font-bold text-rose-500">{stats.queue.failed}</span>
                    <span className="text-xs text-zinc-400">items</span>
                  </div>
                </div>

                {/* Total Queued */}
                <div className="bg-zinc-950/40 border border-zinc-800 p-4 rounded-xl flex flex-col justify-between col-span-2 md:col-span-1">
                  <span className="text-zinc-500 text-[10px] uppercase font-bold tracking-widest">Total Queue</span>
                  <div className="flex items-baseline space-x-2 mt-2">
                    <span className="text-2xl font-bold text-zinc-200">{stats.queue.total}</span>
                    <span className="text-xs text-zinc-400">dispatches</span>
                  </div>
                </div>
              </div>

              {/* Action Trigger Block & Test Form */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                {/* Left: Queue Worker Exec controls */}
                <div className="bg-zinc-950/20 border border-zinc-800/80 p-5 rounded-xl space-y-4">
                  <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest border-b border-zinc-800 pb-2 flex items-center">
                    <Radio className="h-3.5 w-3.5 text-indigo-400 mr-1.5" />
                    Queue Worker Actions
                  </h4>
                  
                  <p className="text-xs text-zinc-400 leading-relaxed">
                    Normally, the worker processes SMTP/SMS retries automatically every 5 seconds. You can trigger a manual run below.
                  </p>

                  <button
                    onClick={handleTriggerQueue}
                    disabled={processingQueue}
                    className="w-full px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-50 text-white font-semibold text-xs rounded-lg flex items-center justify-center space-x-2 transition"
                  >
                    {processingQueue ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                    <span>Run Queue Processor Worker</span>
                  </button>
                </div>

                {/* Right/Middle: Send test form */}
                <form onSubmit={handleSendTest} className="lg:col-span-2 bg-zinc-950/20 border border-zinc-800/80 p-5 rounded-xl space-y-4">
                  <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest border-b border-zinc-800 pb-2 flex items-center">
                    <Send className="h-3.5 w-3.5 text-indigo-400 mr-1.5" />
                    Trigger System Test Notification
                  </h4>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase">Alert Subject</label>
                      <input
                        type="text"
                        value={testTitle}
                        onChange={(e) => setTestTitle(e.target.value)}
                        required
                        className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      />
                    </div>

                    <div className="space-y-1.5">
                      <label className="text-[10px] font-bold text-zinc-400 uppercase">Topic Category</label>
                      <select
                        value={testCategory}
                        onChange={(e) => setTestCategory(e.target.value)}
                        className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition"
                      >
                        <option value="general">general</option>
                        <option value="task">task</option>
                        <option value="security">security</option>
                        <option value="marketing">marketing</option>
                      </select>
                    </div>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-zinc-400 uppercase">Alert Message Body</label>
                    <textarea
                      value={testMessage}
                      onChange={(e) => setTestMessage(e.target.value)}
                      required
                      rows={2}
                      className="w-full bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg p-2 outline-none focus:border-indigo-500 transition resize-none"
                    />
                  </div>

                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
                    <div className="flex items-center space-x-6">
                      <div className="space-y-1.5">
                        <label className="text-[9px] font-bold text-zinc-500 uppercase block">Delivery Channel</label>
                        <div className="flex space-x-3 text-xs text-zinc-300">
                          {['all', 'in_app', 'email', 'sms'].map(chan => (
                            <label key={chan} className="flex items-center space-x-1.5 cursor-pointer">
                              <input
                                type="radio"
                                name="testChannel"
                                checked={testChannel === chan}
                                onChange={() => setTestChannel(chan)}
                                className="border-zinc-800 bg-zinc-950 text-indigo-600 focus:ring-0 focus:ring-offset-0"
                              />
                              <span className="capitalize">{chan.replace('_', ' ')}</span>
                            </label>
                          ))}
                        </div>
                      </div>
                      
                      <label className="flex items-center space-x-2 cursor-pointer mt-4 sm:mt-0">
                        <input
                          type="checkbox"
                          checked={testForceFailure}
                          onChange={(e) => setTestForceFailure(e.target.checked)}
                          className="rounded border-zinc-800 bg-zinc-950 text-indigo-600 focus:ring-0 focus:ring-offset-0"
                        />
                        <span className="text-xs font-bold text-rose-400">Force API Failure (Test Retries)</span>
                      </label>
                    </div>

                    <button
                      type="submit"
                      disabled={sendingTest}
                      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs rounded-lg flex items-center space-x-1.5 transition disabled:opacity-50"
                    >
                      {sendingTest ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                      <span>Dispatch Alert</span>
                    </button>
                  </div>
                </form>
              </div>

              {/* Retry Queue Monitor Table */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest border-b border-zinc-800 pb-2">
                  Retry Queue Monitor (Recent Outputs)
                </h4>
                
                {stats.recent_queue.length === 0 ? (
                  <div className="text-center py-6 text-zinc-500 text-xs">
                    No queued SMTP/SMS dispatches have been registered yet.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-zinc-800 text-zinc-500 font-bold uppercase tracking-wider text-[10px]">
                          <th className="py-2.5 px-3">Gateway</th>
                          <th className="py-2.5 px-3">Recipient info</th>
                          <th className="py-2.5 px-3">Status</th>
                          <th className="py-2.5 px-3 text-center">Attempts</th>
                          <th className="py-2.5 px-3">Last Error info</th>
                          <th className="py-2.5 px-3 text-right">Queued At</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-800/50 font-mono text-[11px]">
                        {stats.recent_queue.map(item => (
                          <tr key={item.id} className="hover:bg-zinc-800/10 transition">
                            <td className="py-2.5 px-3">
                              <span className="px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-300 font-bold uppercase text-[9px]">
                                {item.channel}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 text-zinc-300">{item.recipient}</td>
                            <td className="py-2.5 px-3">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                item.status === 'sent' ? 'bg-emerald-500/10 text-emerald-500' :
                                item.status === 'failed' ? 'bg-rose-500/10 text-rose-500' :
                                'bg-amber-500/10 text-amber-500 animate-pulse'
                              }`}>
                                {item.status}
                              </span>
                            </td>
                            <td className="py-2.5 px-3 text-center text-zinc-400">{item.attempts} / 3</td>
                            <td className="py-2.5 px-3 text-rose-400 max-w-[200px] truncate" title={item.error_message || ''}>
                              {item.error_message || <span className="text-zinc-600">-</span>}
                            </td>
                            <td className="py-2.5 px-3 text-right text-zinc-500">
                              {new Date(item.created_at).toLocaleTimeString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

            </div>
          )}

        </div>
      )}

    </div>
  );
};
