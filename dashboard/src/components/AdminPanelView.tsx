'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useDashboard } from '../context/DashboardContext';
import { api, AdminUser, AdminRole, AdminPermission, AuditLog } from '../lib/api';
import { Users, Shield, BookOpen, UserCheck, ShieldAlert, CheckCircle, Save, ToggleLeft, ToggleRight, Loader } from 'lucide-react';

const mockUsers: AdminUser[] = [
  { id: 'usr_1', email: 'admin@orbit.ai', role: 'admin', is_active: true, is_verified: true, created_at: '2026-07-01T12:00:00Z' },
  { id: 'usr_2', email: 'dev@orbit.ai', role: 'developer', is_active: true, is_verified: true, created_at: '2026-07-02T14:30:00Z' },
  { id: 'usr_3', email: 'member@orbit.ai', role: 'member', is_active: true, is_verified: false, created_at: '2026-07-03T09:15:00Z' },
  { id: 'usr_4', email: 'deactivated@orbit.ai', role: 'member', is_active: false, is_verified: true, created_at: '2026-07-04T16:45:00Z' }
];

const mockRoles: AdminRole[] = [
  { id: 'r_1', name: 'admin', description: 'Full administrator access', created_at: '2026-07-01T12:00:00Z', permissions: ['users:read', 'users:write', 'roles:read', 'roles:write', 'audit:read', 'tasks:create', 'tasks:delete'] },
  { id: 'r_2', name: 'developer', description: 'Developer trigger rights', created_at: '2026-07-01T12:00:00Z', permissions: ['users:read', 'audit:read', 'tasks:create'] },
  { id: 'r_3', name: 'member', description: 'Standard read-only member', created_at: '2026-07-01T12:00:00Z', permissions: ['users:read'] }
];

const mockPermissions: AdminPermission[] = [
  { id: 'p_1', name: 'users:read', description: 'Read users list and profiles' },
  { id: 'p_2', name: 'users:write', description: 'Create, edit, deactivate users' },
  { id: 'p_3', name: 'roles:read', description: 'Read roles and permissions assignment' },
  { id: 'p_4', name: 'roles:write', description: 'Manage role permissions' },
  { id: 'p_5', name: 'audit:read', description: 'View authentication and system audit logs' },
  { id: 'p_6', name: 'tasks:create', description: 'Trigger background executions' },
  { id: 'p_7', name: 'tasks:delete', description: 'Cancel running agent tasks' }
];

const mockLogs: AuditLog[] = [
  { id: 1, event_type: 'ROLE_PERMISSIONS_UPDATED', user_id: 'usr_1', details: "Admin admin@orbit.ai updated permissions for role 'developer' to: ['users:read', 'audit:read', 'tasks:create']", timestamp: '2026-07-10T15:20:00Z' },
  { id: 2, event_type: 'USER_UPDATED', user_id: 'usr_1', details: "Admin admin@orbit.ai updated user dev@orbit.ai: role from 'member' to 'developer'", timestamp: '2026-07-10T14:15:00Z' },
  { id: 3, event_type: 'LOGIN_SUCCESS', user_id: 'usr_1', details: "User admin@orbit.ai logged in successfully from 127.0.0.1", timestamp: '2026-07-10T12:00:00Z' }
];

export const AdminPanelView: React.FC = () => {
  const { useMockData } = useDashboard();
  const [activeTab, setActiveTab] = useState<'users' | 'roles' | 'audit'>('users');
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [roles, setRoles] = useState<AdminRole[]>([]);
  const [permissions, setPermissions] = useState<AdminPermission[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedRole, setSelectedRole] = useState<AdminRole | null>(null);
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [saving, setSaving] = useState(false);

  const fetchAdminData = useCallback(async () => {
    setLoading(true);
    setMessage(null);
    try {
      if (useMockData) {
        setUsers(mockUsers);
        setRoles(mockRoles);
        setPermissions(mockPermissions);
        setAuditLogs(mockLogs);
        if (mockRoles.length > 0 && !selectedRole) {
          setSelectedRole(mockRoles[0]);
          setSelectedPermissions(mockRoles[0].permissions);
        }
      } else {
        const [usersData, rolesData, permissionsData, logsData] = await Promise.all([
          api.getAdminUsers(),
          api.getAdminRoles(),
          api.getAdminPermissions(),
          api.getAdminAuditLogs()
        ]);
        setUsers(usersData);
        setRoles(rolesData);
        setPermissions(permissionsData);
        setAuditLogs(logsData);
        if (rolesData.length > 0 && !selectedRole) {
          setSelectedRole(rolesData[0]);
          setSelectedPermissions(rolesData[0].permissions);
        }
      }
    } catch (err) {
      console.error(err);
      const msg = err instanceof Error ? err.message : 'Failed to fetch admin data from backend.';
      setMessage({ type: 'error', text: msg });
    }
    finally {
      setLoading(false);
    }
  }, [useMockData, selectedRole]);

  useEffect(() => {
    fetchAdminData();
  }, [fetchAdminData]);

  const handleRoleChange = (role: AdminRole) => {
    setSelectedRole(role);
    setSelectedPermissions(role.permissions);
  };

  const handleTogglePermission = (permName: string) => {
    if (selectedPermissions.includes(permName)) {
      setSelectedPermissions(selectedPermissions.filter(p => p !== permName));
    } else {
      setSelectedPermissions([...selectedPermissions, permName]);
    }
  };

  const handleSaveRolePermissions = async () => {
    if (!selectedRole) return;
    setSaving(true);
    setMessage(null);
    try {
      if (useMockData) {
        const updatedRoles = roles.map(r => 
          r.id === selectedRole.id ? { ...r, permissions: selectedPermissions } : r
        );
        setRoles(updatedRoles);
        const newLog: AuditLog = {
          id: auditLogs.length + 1,
          event_type: 'ROLE_PERMISSIONS_UPDATED',
          user_id: 'usr_1',
          details: `Admin admin@orbit.ai updated permissions for role '${selectedRole.name}' to: ${JSON.stringify(selectedPermissions)}`,
          timestamp: new Date().toISOString()
        };
        setAuditLogs([newLog, ...auditLogs]);
        setMessage({ type: 'success', text: `Permissions saved for role '${selectedRole.name}'` });
      } else {
        await api.updateRolePermissions(selectedRole.id, selectedPermissions);
        // Refresh
        const rolesData = await api.getAdminRoles();
        setRoles(rolesData);
        const logsData = await api.getAdminAuditLogs();
        setAuditLogs(logsData);
        setMessage({ type: 'success', text: `Permissions updated successfully on backend for role '${selectedRole.name}'` });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to save role permissions.';
      setMessage({ type: 'error', text: msg });
    } finally {
      setSaving(false);
    }
  };

  const handleUserRoleUpdate = async (userId: string, newRole: string) => {
    setMessage(null);
    try {
      if (useMockData) {
        const updatedUsers = users.map(u => 
          u.id === userId ? { ...u, role: newRole } : u
        );
        setUsers(updatedUsers);
        const targetEmail = users.find(u => u.id === userId)?.email || 'unknown';
        const newLog: AuditLog = {
          id: auditLogs.length + 1,
          event_type: 'USER_UPDATED',
          user_id: 'usr_1',
          details: `Admin admin@orbit.ai updated user ${targetEmail}: role to '${newRole}'`,
          timestamp: new Date().toISOString()
        };
        setAuditLogs([newLog, ...auditLogs]);
        setMessage({ type: 'success', text: `User role updated to '${newRole}'` });
      } else {
        await api.updateAdminUser(userId, { role: newRole });
        const usersData = await api.getAdminUsers();
        setUsers(usersData);
        const logsData = await api.getAdminAuditLogs();
        setAuditLogs(logsData);
        setMessage({ type: 'success', text: 'User role updated successfully on backend.' });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to update user role.';
      setMessage({ type: 'error', text: msg });
    }
  };

  const handleToggleUserStatus = async (userId: string, currentStatus: boolean) => {
    setMessage(null);
    const newStatus = !currentStatus;
    try {
      if (useMockData) {
        const updatedUsers = users.map(u => 
          u.id === userId ? { ...u, is_active: newStatus } : u
        );
        setUsers(updatedUsers);
        const targetEmail = users.find(u => u.id === userId)?.email || 'unknown';
        const newLog: AuditLog = {
          id: auditLogs.length + 1,
          event_type: 'USER_UPDATED',
          user_id: 'usr_1',
          details: `Admin admin@orbit.ai updated user ${targetEmail}: active status to '${newStatus}'`,
          timestamp: new Date().toISOString()
        };
        setAuditLogs([newLog, ...auditLogs]);
        setMessage({ type: 'success', text: `User active status toggled to '${newStatus}'` });
      } else {
        await api.updateAdminUser(userId, { is_active: newStatus });
        const usersData = await api.getAdminUsers();
        setUsers(usersData);
        const logsData = await api.getAdminAuditLogs();
        setAuditLogs(logsData);
        setMessage({ type: 'success', text: 'User status updated successfully on backend.' });
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to toggle user status.';
      setMessage({ type: 'error', text: msg });
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center">
            <Shield className="h-6 w-6 text-indigo-400 mr-2.5 animate-pulse" />
            Security & Administration Panel
          </h2>
          <p className="text-sm text-zinc-400 mt-1">
            Manage system roles, permissions, audit logs, and developer accounts.
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
          {message.type === 'success' ? <CheckCircle className="h-5 w-5 shrink-0" /> : <ShieldAlert className="h-5 w-5 shrink-0" />}
          <span>{message.text}</span>
        </div>
      )}

      {/* Tab Selectors */}
      <div className="flex border-b border-zinc-800 space-x-2">
        <button
          onClick={() => setActiveTab('users')}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
            activeTab === 'users' ? 'border-indigo-500 text-indigo-400 font-bold' : 'border-transparent text-zinc-400 hover:text-zinc-200'
          } flex items-center space-x-2`}
        >
          <Users className="h-4 w-4" />
          <span>User Management</span>
        </button>
        <button
          onClick={() => setActiveTab('roles')}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
            activeTab === 'roles' ? 'border-indigo-500 text-indigo-400 font-bold' : 'border-transparent text-zinc-400 hover:text-zinc-200'
          } flex items-center space-x-2`}
        >
          <Shield className="h-4 w-4" />
          <span>Roles & Permissions</span>
        </button>
        <button
          onClick={() => setActiveTab('audit')}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
            activeTab === 'audit' ? 'border-indigo-500 text-indigo-400 font-bold' : 'border-transparent text-zinc-400 hover:text-zinc-200'
          } flex items-center space-x-2`}
        >
          <BookOpen className="h-4 w-4" />
          <span>System Audit Logs</span>
        </button>
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="flex flex-col items-center space-y-3">
            <Loader className="h-10 w-10 text-indigo-500 animate-spin" />
            <span className="text-sm text-zinc-400">Fetching schema information...</span>
          </div>
        </div>
      ) : (
        <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl p-6 shadow-xl backdrop-blur-md animate-in fade-in duration-300">
          
          {/* USER MANAGEMENT TAB */}
          {activeTab === 'users' && (
            <div className="space-y-4">
              <h3 className="text-lg font-bold text-white flex items-center">
                <UserCheck className="h-5 w-5 text-indigo-400 mr-2" />
                Active Profiles Registry
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-zinc-800 text-zinc-400 font-semibold uppercase tracking-wider text-xs">
                      <th className="py-3 px-4">User Email</th>
                      <th className="py-3 px-4">System Role</th>
                      <th className="py-3 px-4">Verification</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/60">
                    {users.map(u => (
                      <tr key={u.id} className="hover:bg-zinc-800/10 transition">
                        <td className="py-3.5 px-4 font-medium text-white">{u.email}</td>
                        <td className="py-3.5 px-4">
                          <select
                            value={u.role}
                            onChange={(e) => handleUserRoleUpdate(u.id, e.target.value)}
                            className="bg-zinc-950 border border-zinc-800 text-zinc-300 rounded-lg px-2 py-1 text-xs outline-none transition focus:border-indigo-500"
                          >
                            <option value="member">member</option>
                            <option value="developer">developer</option>
                            <option value="admin">admin</option>
                          </select>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            u.is_verified ? 'bg-emerald-500/10 text-emerald-500' : 'bg-yellow-500/10 text-yellow-500'
                          }`}>
                            {u.is_verified ? 'Verified' : 'Pending'}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            u.is_active ? 'bg-indigo-500/10 text-indigo-400' : 'bg-red-500/10 text-red-500'
                          }`}>
                            {u.is_active ? 'Active' : 'Suspended'}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            onClick={() => handleToggleUserStatus(u.id, u.is_active)}
                            className="text-xs transition p-1 hover:bg-zinc-800 rounded flex items-center space-x-1 ml-auto text-zinc-300"
                          >
                            {u.is_active ? (
                              <>
                                <ToggleRight className="h-5 w-5 text-indigo-400" />
                                <span>Suspend</span>
                              </>
                            ) : (
                              <>
                                <ToggleLeft className="h-5 w-5 text-zinc-600" />
                                <span>Activate</span>
                              </>
                            )}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ROLES & PERMISSIONS TAB */}
          {activeTab === 'roles' && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              
              {/* Left Column: Roles list */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-widest">Select System Role</h4>
                <div className="flex flex-col space-y-2">
                  {roles.map(r => (
                    <button
                      key={r.id}
                      onClick={() => handleRoleChange(r)}
                      className={`p-4 rounded-xl text-left border transition text-sm flex flex-col space-y-1.5 ${
                        selectedRole?.id === r.id 
                          ? 'bg-indigo-600/10 border-indigo-500 text-indigo-300' 
                          : 'bg-zinc-950/40 border-zinc-800/80 text-zinc-400 hover:bg-zinc-800/20'
                      }`}
                    >
                      <span className="font-bold capitalize text-white">{r.name}</span>
                      <span className="text-xs leading-relaxed">{r.description}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Right Columns: Permissions assignment */}
              <div className="md:col-span-2 space-y-4 border-t md:border-t-0 md:border-l border-zinc-800/60 pt-6 md:pt-0 md:pl-8">
                {selectedRole ? (
                  <div className="space-y-6">
                    <div className="flex justify-between items-center">
                      <div>
                        <h4 className="text-sm font-bold text-white capitalize">Permissions for role: {selectedRole.name}</h4>
                        <p className="text-xs text-zinc-400 mt-0.5">Toggle active authorization rights for this security profile.</p>
                      </div>
                      <button
                        onClick={handleSaveRolePermissions}
                        disabled={saving}
                        className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white text-xs font-medium rounded-lg flex items-center space-x-1.5 transition disabled:opacity-50"
                      >
                        {saving ? <Loader className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                        <span>Save Permissions</span>
                      </button>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {permissions.map(p => {
                        const checked = selectedPermissions.includes(p.name);
                        return (
                          <div
                            key={p.id}
                            onClick={() => handleTogglePermission(p.name)}
                            className={`p-3.5 rounded-xl border cursor-pointer transition flex items-start space-x-3 ${
                              checked 
                                ? 'bg-indigo-500/5 border-indigo-500/30 text-zinc-200' 
                                : 'bg-zinc-950/20 border-zinc-800/80 text-zinc-500 hover:border-zinc-800'
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={checked}
                              readOnly
                              className="mt-0.5 rounded border-zinc-800 bg-zinc-950 text-indigo-600 focus:ring-indigo-600/30"
                            />
                            <div>
                              <span className="block text-xs font-bold font-mono">{p.name}</span>
                              <span className="block text-[11px] text-zinc-400 mt-1 leading-snug">{p.description}</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div className="h-48 flex items-center justify-center text-zinc-500 text-sm">
                    Please select a role to configure permissions.
                  </div>
                )}
              </div>

            </div>
          )}

          {/* AUDIT LOGS TAB */}
          {activeTab === 'audit' && (
            <div className="space-y-4">
              <h3 className="text-lg font-bold text-white flex items-center">
                <BookOpen className="h-5 w-5 text-indigo-400 mr-2" />
                Security Access Audit Logs
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="border-b border-zinc-800 text-zinc-400 font-semibold uppercase tracking-wider text-xs">
                      <th className="py-3 px-4">Event Type</th>
                      <th className="py-3 px-4">Operator ID</th>
                      <th className="py-3 px-4">Details</th>
                      <th className="py-3 px-4 text-right">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-800/60 font-mono text-xs">
                    {auditLogs.map(l => (
                      <tr key={l.id} className="hover:bg-zinc-800/10 transition">
                        <td className="py-3 px-4">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            l.event_type.includes('DENIED') || l.event_type.includes('FAIL')
                              ? 'bg-red-500/10 text-red-500' 
                              : 'bg-indigo-500/10 text-indigo-400'
                          }`}>
                            {l.event_type}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-zinc-300">{l.user_id || 'SYSTEM'}</td>
                        <td className="py-3 px-4 text-zinc-400">{l.details}</td>
                        <td className="py-3 px-4 text-zinc-500 text-right">
                          {new Date(l.timestamp).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

        </div>
      )}

    </div>
  );
};
