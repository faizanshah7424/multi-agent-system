'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';

interface UserPayload {
  id: string;
  email: string;
  role: string;
  is_verified?: boolean;
  is_active?: boolean;
}

interface AuthContextType {
  user: UserPayload | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  setError: (err: string | null) => void;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, role?: string) => Promise<{ message: string; verification_token?: string }>;
  logout: () => Promise<void>;
  forgotPassword: (email: string) => Promise<{ message: string; reset_token?: string }>;
  resetPassword: (token: string, newPassword: string) => Promise<void>;
  verifyEmail: (token: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface JwtClaims {
  uid?: string;
  sub?: string;
  role?: string;
  exp?: number;
}

function parseJwt(token: string): JwtClaims | null {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      window.atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload) as JwtClaims;
  } catch {
    return null;
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserPayload | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Sync user state from localStorage access token
  const syncAuthState = useCallback(() => {
    if (typeof window === 'undefined') return;
    const token = localStorage.getItem('auth_access_token');
    if (token) {
      const claims = parseJwt(token);
      if (claims && claims.exp && claims.exp * 1000 > Date.now()) {
        setUser({
          id: claims.uid || '',
          email: claims.sub || '',
          role: claims.role || 'member'
        });
        setIsAuthenticated(true);
      } else {
        // Expired or invalid
        localStorage.removeItem('auth_access_token');
        localStorage.removeItem('auth_refresh_token');
        setUser(null);
        setIsAuthenticated(false);
      }
    } else {
      setUser(null);
      setIsAuthenticated(false);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    syncAuthState();

    // Listen for custom logout event dispatched by the fetchJson interceptor
    const handleLogoutEvent = () => {
      setUser(null);
      setIsAuthenticated(false);
    };

    window.addEventListener('auth_logout', handleLogoutEvent);
    return () => {
      window.removeEventListener('auth_logout', handleLogoutEvent);
    };
  }, [syncAuthState]);

  const login = async (email: string, password: string) => {
    setError(null);
    setLoading(true);
    try {
      const res = await api.login({ email, password });
      localStorage.setItem('auth_access_token', res.access_token);
      localStorage.setItem('auth_refresh_token', res.refresh_token);
      syncAuthState();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed. Please verify credentials.';
      setError(message);
      setLoading(false);
      throw err;
    }
  };

  const signup = async (email: string, password: string, role = 'member') => {
    setError(null);
    try {
      return await api.signup({ email, password, role });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Signup failed.';
      setError(message);
      throw err;
    }
  };

  const logout = async () => {
    setLoading(true);
    const refreshToken = localStorage.getItem('auth_refresh_token');
    if (refreshToken) {
      try {
        await api.logout({ refresh_token: refreshToken });
      } catch (err) {
        console.error('Logout error on server: ', err);
      }
    }
    localStorage.removeItem('auth_access_token');
    localStorage.removeItem('auth_refresh_token');
    setUser(null);
    setIsAuthenticated(false);
    setLoading(false);
  };

  const forgotPassword = async (email: string) => {
    setError(null);
    try {
      return await api.forgotPassword({ email });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error executing forgot password request.';
      setError(message);
      throw err;
    }
  };

  const resetPassword = async (token: string, newPassword: string) => {
    setError(null);
    try {
      await api.resetPassword({ token, new_password: newPassword });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error executing reset password request.';
      setError(message);
      throw err;
    }
  };

  const verifyEmail = async (token: string) => {
    setError(null);
    try {
      await api.verifyEmail(token);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error executing email verification.';
      setError(message);
      throw err;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        loading,
        error,
        setError,
        login,
        signup,
        logout,
        forgotPassword,
        resetPassword,
        verifyEmail
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
